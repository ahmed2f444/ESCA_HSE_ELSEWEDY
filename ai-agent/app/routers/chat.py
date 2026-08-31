import logging
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import AskRequest, AskResponse
from app.agent import run_agent_loop
from app.tools.rbac import normalize_role
from app.security import scrub_secrets_from_text, mask_safe_error

logger = logging.getLogger("esca_chat")
router = APIRouter(tags=["Chat & Agent"])

SUGGESTIONS = [
    "ما هي الحوادث المفتوحة حالياً وما درجة خطورتها؟",
    "اعرض تصاريح العمل النشطة والمنتهية في الموقع ePTW",
    "افحص تعارضات العمليات المتزامنة SIMOPS في منطقة الإنتاج",
    "ما هي إحصائيات ونسبة الامتثال لجولات التفتيش والسلامة؟",
    "جدول فحص سلامة روتيني لمنطقة خطوط العزل CCV الأسبوع القادم",
    "اقترح قائمة فحص مطابقة لمعيار ISO 45001 لمنطقة الإنتاج",
    "ما هي اشتراطات الدخول للأماكن المغلقة وفحص الغازات حسب OSHA؟",
    "انشئ بلاغ حادث جديد: انسكاب زيت هيدروليكي في منطقة الإنتاج",
    "سجل تقييم مخاطر HIRA جديد لنشاط تغيير بكرات الكابلات",
    "انشئ وثيقة تحليل سلامة المهام JSA لصيانة الرافعات العلوية",
    "ما هي مطافئ الحريق التي تحتاج فحص دوري أو إعادة تعبئة؟",
    "ارفع طلب توريد مهمات وقاية PPE للأصناف التي انخفض رصيدها",
    "صرف مهمة وقاية شخصية (PPE) للموظف وتحديث المخزون",
    "افحص التوافق الكيميائي لمادة الأسيتون والمواد المخزنة",
    "سجل نتيجة الفحص الطبي الدوري للموظف وتحديث الملف الصحي",
    "وثق اعتماد وتجديد شهادة تدريب السلامة الكيميائية",
    "اعرض أحدث تنبيهات حساسات الغازات والحرارة الذكية IoT",
    "احسب مؤشرات TRIR و LTIFR لشهر يوليو 2026",
    "اعرض سجل التدقيق غير القابل للتعديل لعمليات النظام",
    "ما هي القواعد الذهبية للسلامة (ESCA Golden Rules)؟",
    "ما هي إجراءات CAPA وملاحظات التفتيش المفتوحة؟",
]


@router.post("/ask", response_model=AskResponse)
@router.post("/api/ask", response_model=AskResponse)
def ask_agent(req: AskRequest, db: Session = Depends(get_db)):
    """
    Main conversational agent endpoint. Receives user questions, enforces RBAC on tools,
    executes live RAG & CRUD against Railway MySQL, and returns verified answer with traces.
    Protected by Prompt Guard, Rate Limiting, and Secret Credential Sanitization.
    """
    role = normalize_role(req.user_role)
    session_id = req.session_id or f"sess-{uuid.uuid4().hex[:8]}"
    try:
        response = run_agent_loop(
            question=req.question,
            db=db,
            session_id=session_id,
            model_mode=req.model_mode or "auto",
            client_history=req.history,
            user_role=role,
            user_id=req.admin_user_id or "AI_USER",
        )
        response.user_role = role
        return response
    except RuntimeError as exc:
        safe_msg = scrub_secrets_from_text(str(exc))
        logger.error("agent_runtime_error error=%s", safe_msg)
        error_msg = (
            f"⚠️ All LLM providers are currently unavailable: {safe_msg}. "
            "Please check network connection or switch model mode."
        )
        return AskResponse(
            session_id=session_id,
            answer=error_msg,
            tool_calls=[],
            model_used=None,
            user_role=role,
        )
    except Exception as exc:
        safe_msg = mask_safe_error(exc)
        logger.error("agent_unhandled_error error=%s", safe_msg)
        return AskResponse(
            session_id=session_id,
            answer=f"⚠️ {safe_msg}",
            tool_calls=[],
            model_used=None,
            user_role=role,
        )


@router.get("/suggestions")
@router.get("/api/suggestions")
def get_suggestions():
    """Returns sample prompt questions for the frontend assistant dock."""
    return SUGGESTIONS


@router.post("/transcribe")
@router.post("/api/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
):
    """
    Enterprise Multilingual Whisper Speech-to-Text endpoint.
    Handles Egyptian Arabic (ar-EG), Gulf/MSA (ar-SA), English (en-US),
    and mixed English + Arabic technical code-switching.
    """
    try:
        content = await file.read()
        if not content:
            return {"text": "", "success": False, "error": "Empty audio payload"}

        from openai import OpenAI
        from app.config import settings

        client = OpenAI(api_key=settings.groq_api_key, base_url=settings.groq_base_url)

        # Contextual prompt biasing to accurately capture HSE technical terms and Egyptian names
        hse_prompt = (
            "Elsewedy Cables ESCA HSE safety ePTW SIMOPS JSA HIRA OSHA ISO PPE CAPA "
            "مستودع كابلات تصريح عمل حادث وشيك فحص طبي هبة فؤاد محمود عبدالله أحمد سامي "
            "medical examination audiometry hearing test spirometry chemical hazard fire extinguisher"
        )

        filename = file.filename or "recording.webm"
        content_type = file.content_type or "audio/webm"

        kwargs = {
            "model": "whisper-large-v3-turbo",
            "file": (filename, content, content_type),
            "prompt": hse_prompt,
        }

        if language and language not in ("auto", "multilingual", "mixed", ""):
            lang_code = language.split("-")[0].lower()
            if lang_code in ("ar", "en", "fr"):
                kwargs["language"] = lang_code

        res = client.audio.transcriptions.create(**kwargs)
        transcribed_text = res.text.strip() if hasattr(res, "text") else str(res).strip()
        logger.info("whisper_transcription_success chars=%d", len(transcribed_text))
        return {
            "text": transcribed_text,
            "success": True,
            "model": "whisper-large-v3-turbo",
        }
    except Exception as exc:
        logger.error("whisper_transcription_failed error=%s", str(exc))
        return {
            "text": "",
            "success": False,
            "error": str(exc),
        }