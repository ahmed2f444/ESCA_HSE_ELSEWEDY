"""Validated runtime wiring for scheduled automation delivery."""

from __future__ import annotations

from functools import partial

from apscheduler.schedulers.base import BaseScheduler

from app.automation.dispatcher import create_event_dispatcher
from app.automation.events import build_automation_events
from app.automation.scheduler import AutomationSchedulerController
from app.config import Settings


def create_scheduler_controller(
    scheduler: BaseScheduler,
    settings: Settings,
) -> AutomationSchedulerController:
    """Wire event planning and dispatch to the same validated mode."""

    dispatcher = create_event_dispatcher(settings)
    event_builder = partial(
        build_automation_events,
        delivery_mode=dispatcher.mode,
    )
    return AutomationSchedulerController(
        scheduler=scheduler,
        event_builder=event_builder,
        dispatcher=dispatcher,
    )
