import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import AskRequest, AskResponse
from app.agent import run_agent_loop

router = APIRouter(tags=["Chat & Agent"])

SUGGESTIONS = [
    "ما هي الحوادث المفتوحة حالياً وما درجة خطورتها؟",
    "اعرض تصاريح العمل النشطة والمنتهية في الموقع",
    "ما هي إجراءات CAPA المتأخرة عن موعدها؟",
    "كم عدد الفحوصات الطبية المكتملة ونتائجها؟",
    "ما هو وضع مخزون مهمات الوقاية الشخصية (PPE)؟",
    "اعرض أعلى المخاطر المسجلة في سجل المخاطر",
    "ما هي الشهادات التدريبية المنتهية أو القريبة من الانتهاء؟",
    "ما هي مؤشرات السلامة لشهر يوليو 2026 (TRIR و LTIFR)؟",
]


@router.post("/ask", response_model=AskResponse)
@router.post("/api/ask", response_model=AskResponse)
def ask_agent(req: AskRequest, db: Session = Depends(get_db)):
    """
    Main conversational agent endpoint. Receives user questions, executes tool calling against MySQL,
    and returns answer with full execution traces.
    """
    try:
        response = run_agent_loop(
            question=req.question,
            db=db,
            session_id=req.session_id,
            model_mode=req.model_mode or "auto",
            client_history=req.history,
        )
        return response
    except RuntimeError as exc:
        error_msg = (
            f"⚠️ All LLM providers are currently unavailable: {exc}. "
            "This is usually caused by a rate limit or token quota. Please try a shorter question or try again shortly."
        )
        return AskResponse(
            session_id=req.session_id or f"err-{uuid.uuid4().hex[:8]}",
            answer=error_msg,
            tool_calls=[],
            model_used=None,
        )
    except Exception as exc:
        return AskResponse(
            session_id=req.session_id or f"err-{uuid.uuid4().hex[:8]}",
            answer=f"⚠️ Unexpected server error: {exc}",
            tool_calls=[],
            model_used=None,
        )


@router.get("/suggestions")
@router.get("/api/suggestions")
def get_suggestions():
    """Returns sample prompt questions for the frontend assistant dock."""
    return SUGGESTIONS