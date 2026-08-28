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
from app.routers import chat

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

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Chat & Agent Routes
app.include_router(chat.router)


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
