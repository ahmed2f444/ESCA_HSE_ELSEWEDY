import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import AskRequest, AskResponse
from app.agent import run_agent_loop
from app.tools.rbac import normalize_role

router = APIRouter(tags=["Chat & Agent"])

SUGGESTIONS = [
    "ما هي الحوادث المفتوحة حالياً وما درجة خطورتها؟",
    "اعرض تصاريح العمل النشطة والمنتهية في الموقع",
    "ما هي إحصائيات ونسبة الامتثال لجولات التفتيش والسلامة؟",
    "جدول فحص سلامة روتيني لمنطقة خطوط العزل CCV الأسبوع القادم",
    "اقترح قائمة فحص مطابقة لمعيار ISO 45001 لمنطقة الإنتاج",
    "ما هي اشتراطات الدخول للأماكن المغلقة وفحص الغازات حسب OSHA؟",
    "انشئ بلاغ حادث جديد: انسكاب زيت هيدروليكي في منطقة الإنتاج",
    "اعتمد تصريح العمل ePTW رقم 1",
    "ما هي القواعد الذهبية للسلامة (ESCA Golden Rules)؟",
    "ما هي إجراءات CAPA وملاحظات التفتيش المفتوحة؟",
    "صرف مهمة وقاية شخصية (PPE) للموظف",
    "احسب مؤشرات TRIR و LTIFR لشهر يوليو 2026",
    "ما هي مطافئ الحريق التي تحتاج فحص دوري أو إعادة تعبئة؟",
]


@router.post("/ask", response_model=AskResponse)
@router.post("/api/ask", response_model=AskResponse)
def ask_agent(req: AskRequest, db: Session = Depends(get_db)):
    """
    Main conversational agent endpoint. Receives user questions, enforces RBAC on tools,
    executes live RAG & CRUD against Railway MySQL, and returns verified answer with traces.
    """
    role = normalize_role(req.user_role)
    try:
        response = run_agent_loop(
            question=req.question,
            db=db,
            session_id=req.session_id,
            model_mode=req.model_mode or "auto",
            client_history=req.history,
            user_role=role,
            user_id=req.admin_user_id or "AI_USER",
        )
        response.user_role = role
        return response
    except RuntimeError as exc:
        error_msg = (
            f"⚠️ All LLM providers are currently unavailable: {exc}. "
            "Please check network connection or switch model mode."
        )
        return AskResponse(
            session_id=req.session_id or f"err-{uuid.uuid4().hex[:8]}",
            answer=error_msg,
            tool_calls=[],
            model_used=None,
            user_role=role,
        )
    except Exception as exc:
        return AskResponse(
            session_id=req.session_id or f"err-{uuid.uuid4().hex[:8]}",
            answer=f"⚠️ Server error: {exc}",
            tool_calls=[],
            model_used=None,
            user_role=role,
        )


@router.get("/suggestions")
@router.get("/api/suggestions")
def get_suggestions():
    """Returns sample prompt questions for the frontend assistant dock."""
    return SUGGESTIONS