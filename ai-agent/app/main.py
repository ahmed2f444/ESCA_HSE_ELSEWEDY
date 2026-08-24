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


@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler
    if settings.enable_scheduler:
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from app.automation.scheduler import AutomationSchedulerController

            background_scheduler = BackgroundScheduler()
            controller = AutomationSchedulerController(scheduler=background_scheduler)
            controller.refresh_schedules()
            background_scheduler.start()
            scheduler = background_scheduler
            logger.info("APScheduler automation background worker started successfully.")
        except Exception as exc:
            logger.warning(f"Could not start APScheduler background worker: {exc}")

    yield

    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler background worker stopped.")


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