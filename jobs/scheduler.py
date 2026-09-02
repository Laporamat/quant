"""
jobs/scheduler.py
APScheduler setup for periodic background jobs.
"""
from __future__ import annotations
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from config import settings

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone=settings.scheduler_timezone)
    return _scheduler


def start_scheduler() -> None:
    """Register all jobs and start the scheduler."""
    sched = get_scheduler()

    # Daily data refresh (weekdays at 18:00 local time)
    from jobs.data_refresh import refresh_all
    sched.add_job(
        refresh_all,
        trigger=CronTrigger.from_crontab(settings.data_refresh_cron,
                                          timezone=settings.scheduler_timezone),
        id="data_refresh",
        name="Daily Data Refresh",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    sched.start()
    logger.info("Scheduler started. Jobs: %s", [j.name for j in sched.get_jobs()])


def stop_scheduler() -> None:
    sched = get_scheduler()
    if sched.running:
        sched.shutdown(wait=False)
        logger.info("Scheduler stopped")


def list_jobs() -> list:
    return [
        {"id": j.id, "name": j.name, "next_run": str(j.next_run_time)}
        for j in get_scheduler().get_jobs()
    ]
