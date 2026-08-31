import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, get_db
from app.routers import chat, hazmat
from app.security import (
    SecurityHeadersMiddleware,
    RequestSizeLimitMiddleware,
    RateLimitMiddleware,
    mask_safe_error,
    scrub_secrets_from_text,
)

logger = logging.getLogger("esca_agent")
scheduler = None
scheduler_controller = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler, scheduler_controller
    if settings.enable_scheduler:
        background_scheduler = None
        controller = None
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from app.automation.runtime import create_scheduler_controller

            background_scheduler = BackgroundScheduler()
            controller = create_scheduler_controller(
                background_scheduler,
                settings,
            )
            scheduled_rules = controller.refresh_schedules(fail_fast=True)
            background_scheduler.start()
            scheduler = background_scheduler
            scheduler_controller = controller
            logger.info(
                "automation_scheduler_started mode=%s scheduled_rules=%d",
                controller.delivery_mode,
                scheduled_rules,
            )
        except Exception as exc:
            if background_scheduler and background_scheduler.running:
                background_scheduler.shutdown(wait=False)
            if controller:
                controller.close()
            logger.error(
                "automation_scheduler_start_failed error_type=%s",
                type(exc).__name__,
            )
            if settings.automation_live_enabled:
                raise RuntimeError(
                    "Live automation scheduler could not start safely"
                ) from None

    yield

    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
    if scheduler_controller:
        scheduler_controller.close()
    scheduler = None
    scheduler_controller = None
    logger.info("automation_scheduler_stopped")


app = FastAPI(
    title="ESCA HSE AI Agent & Automation Service",
    description="MySQL-backed LLM Agent with Groq integration, tool-calling, and automated scheduled checks.",
    version="1.0.0",
    lifespan=lifespan,
)

# 1. Rate Limiting Middleware (DDoS & Brute Force Protection)
app.add_middleware(
    RateLimitMiddleware,
    enabled=settings.security_rate_limit_enabled,
)

# 2. Request Body Size Limit Middleware (Memory Exhaustion Protection)
app.add_middleware(
    RequestSizeLimitMiddleware,
    max_body_bytes=settings.max_request_body_bytes,
)

# 3. Security Headers Middleware (CSP, HSTS, X-Frame-Options, X-Content-Type-Options)
app.add_middleware(SecurityHeadersMiddleware)

# 4. Strict CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins if settings.cors_allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include Chat & Agent Routes
app.include_router(chat.router)
app.include_router(hazmat.router)


@app.get("/health", tags=["Health"])
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection unavailable"
        ) from exc

    return {
        "status": "ok",
        "service": "ai-agent",
        "engine": "MySQL",
        "database": engine.url.database,
        "llm": f"Groq ({settings.groq_model}) + local Ollama fallback",
        "scheduler": "running" if scheduler and scheduler.running else "idle",
        "automation_delivery": settings.automation_delivery_mode,
        "automation_live": settings.automation_live_enabled,
    }


@app.get("/health/ready", tags=["Health"])
def readiness_check():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT DATABASE(), VERSION()")).fetchone()
            db_name = result[0] if result else "unknown"
            version = result[1] if result else "unknown"
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection unavailable"
        ) from exc

    return {
        "status": "ready",
        "service": "ai-agent",
        "database": "connected",
        "db_name": db_name,
        "db_version": version,
    }


@app.get("/api/v1/automation/detect", tags=["Automation"])
def detect_automation_candidates(
    db: Annotated[Session, Depends(get_db)],
    as_of: Annotated[
        datetime | None,
        Query(
            description=(
                "Optional timezone-aware evaluation time. "
                "Example: 2026-08-24T12:00:00+03:00"
            ),
        ),
    ] = None,
):
    """Safe read-only evaluation of automation rule candidates (AUT-001 to AUT-004)."""
    try:
        from app.automation.service import run_detection
        return run_detection(db, as_of)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Automation detection error: {exc}"
        ) from exc


@app.post("/api/v1/automation/trigger", tags=["Automation"])
def trigger_automation_run(
    db: Annotated[Session, Depends(get_db)],
):
    """Manually trigger all active automation detection rules and persist live alerts."""
    try:
        from app.automation.service import run_detection
        from app.automation.events import build_automation_events
        from app.automation.dispatcher import create_event_dispatcher
        from app.config import get_settings

        settings = get_settings()
        report = run_detection(db)
        dispatcher = create_event_dispatcher(settings)
        events = build_automation_events(report, delivery_mode=dispatcher.mode)
        dispatch_result = dispatcher.dispatch(events)
        dispatcher.close()

        return {
            "status": "triggered",
            "message": "Automation engine successfully evaluated all active HSE rules and dispatched alerts.",
            "mode": dispatcher.mode,
            "planned_count": dispatch_result.planned_count,
            "delivered_count": dispatch_result.delivered_count,
            "summary": report.get("summary", {}),
            "action_summary": dispatch_result.as_dict(),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Automation trigger error: {exc}"
        ) from exc


def evaluate_and_sync_all_automations(db: Session):
    """Evaluates all active HSE automation rules (AUT-001 to AUT-004) and generates live notifications."""
    try:
        from app.automation.service import run_detection
        from app.automation.events import build_automation_events
        from app.automation.dispatcher import DatabaseEventDispatcher

        report = run_detection(db)
        dispatcher = DatabaseEventDispatcher(session_factory=lambda: db)
        events = build_automation_events(report, delivery_mode="database")
        dispatcher.dispatch(events)
    except Exception as exc:
        logger.warning("evaluate_and_sync_all_automations error=%s", exc)


def check_and_apply_certificate_expiries(db: Session):
    """Backward-compatible wrapper for certificate expirations."""
    evaluate_and_sync_all_automations(db)


@app.get("/api/v1/notifications", tags=["Notifications"])
def get_live_notifications(
    db: Annotated[Session, Depends(get_db)],
    limit: int = 30,
    unread_only: bool = False,
):
    """Fetch real-time notifications directly from the Railway MySQL database."""
    try:
        try:
            query_str = """
                SELECT 
                    notification_id,
                    type,
                    entity_type,
                    entity_id,
                    title,
                    message,
                    status_id,
                    created_at
                FROM notifications
            """
            if unread_only:
                query_str += " WHERE status_id = 1"
            query_str += " ORDER BY created_at DESC, notification_id DESC LIMIT :limit"
            rows = db.execute(text(query_str), {"limit": limit}).fetchall()
        except Exception:
            db.rollback()
            query_str = """
                SELECT 
                    notification_id,
                    type,
                    entity_type,
                    entity_id,
                    title,
                    message,
                    status,
                    created_at
                FROM notifications
            """
            if unread_only:
                query_str += " WHERE UPPER(COALESCE(status, 'UNREAD')) = 'UNREAD'"
            query_str += " ORDER BY created_at DESC, notification_id DESC LIMIT :limit"
            rows = db.execute(text(query_str), {"limit": limit}).fetchall()

        route_map = {
            "AUTOMATION_PERMIT_OVERDUE": "/permits",
            "AUTOMATION_CERTIFICATE_EXPIRY": "/training",
            "AUTOMATION_CAPA_OVERDUE": "/incidents",
            "AUTOMATION_RISK_REVIEW": "/risk",
            "PERMIT": "/permits",
            "CERTIFICATE": "/training",
            "TRAINING": "/training",
            "CAPA": "/incidents",
            "RISK": "/risk",
            "INCIDENT": "/incidents",
            "FIRE_EQUIPMENT": "/fire-equipment",
            "HEALTH": "/occupational-health",
            "HEALTH_EXAM": "/occupational-health",
            "INSPECTION": "/inspections",
            "CHEMICAL": "/hazmat",
            "AI_EVENT": "/ai-iot",
        }

        results = []
        for r in rows:
            m = dict(r._mapping)
            ntype = m.get("type") or m.get("entity_type") or "GENERAL"
            sev = m.get("severity_id") if m.get("severity_id") is not None else 3
            color = "var(--safe)" if (sev == 1 or ntype == "TRAINING") else ("var(--crit)" if sev >= 3 else "var(--warn)")

            cat = m.get("created_at")
            time_str = cat.strftime("%Y-%m-%d %H:%M") if hasattr(cat, "strftime") else "الآن"
            is_unread = (m.get("status_id") == 1) or (str(m.get("status", "")).upper() == "UNREAD")

            raw_id = m.get("notification_id")
            str_id = str(raw_id) if raw_id is not None else ""
            display_id = str_id if str_id.startswith("NTF-") else f"NTF-{str_id}"

            results.append({
                "id": display_id,
                "notificationId": raw_id,
                "title": m.get("title") or "تنبيه سلامة",
                "body": m.get("message") or "",
                "type": ntype,
                "severityId": sev,
                "color": color,
                "unread": is_unread,
                "time": time_str,
                "createdAt": str(cat),
                "to": route_map.get(ntype, "/dashboard"),
            })
        return results
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Notifications fetch error: {exc}",
        ) from exc


@app.post("/api/v1/notifications/mark-read", tags=["Notifications"])
def mark_notification_read(
    payload: dict,
    db: Annotated[Session, Depends(get_db)],
):
    """Mark a specific notification as read (status_id = 2) in Railway database."""
    nid = payload.get("notificationId") or payload.get("id")
    if nid and str(nid).startswith("NTF-"):
        nid = int(str(nid).replace("NTF-", ""))
    if nid:
        db.execute(text("UPDATE notifications SET status_id = 2 WHERE notification_id = :nid"), {"nid": nid})
        db.commit()
    return {"success": True, "notificationId": nid}


@app.post("/api/v1/notifications/mark-all-read", tags=["Notifications"])
def mark_all_notifications_read(
    db: Annotated[Session, Depends(get_db)],
):
    """Mark all unread notifications as read (status_id = 2) in Railway database."""
    db.execute(text("UPDATE notifications SET status_id = 2 WHERE status_id = 1"))
    db.commit()
    return {"success": True, "message": "All notifications marked as read"}
