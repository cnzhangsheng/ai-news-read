# app/core/scheduler.py
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import app_config
from app.services.fetcher import fetch_all_sources

scheduler = AsyncIOScheduler()
_scheduler_running = False
_next_fetch_time: datetime | None = None


async def scheduled_fetch() -> None:
    global _next_fetch_time
    await fetch_all_sources()
    _next_fetch_time = datetime.now() + timedelta(minutes=app_config.settings.fetch_interval)


def start_scheduler() -> None:
    global _scheduler_running, _next_fetch_time

    if _scheduler_running:
        return

    scheduler.add_job(
        scheduled_fetch,
        trigger=IntervalTrigger(minutes=app_config.settings.fetch_interval),
        id="fetch_all_sources",
        replace_existing=True
    )

    scheduler.start()
    _scheduler_running = True
    _next_fetch_time = datetime.now() + timedelta(minutes=app_config.settings.fetch_interval)


def stop_scheduler() -> None:
    global _scheduler_running
    scheduler.shutdown()
    _scheduler_running = False


def get_scheduler_status() -> tuple[bool, datetime | None]:
    return _scheduler_running, _next_fetch_time