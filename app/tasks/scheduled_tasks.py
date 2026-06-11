"""
Scheduled Tasks Initialization
Connects proactive monitoring to APScheduler
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import logging

from app.tasks.proactive_monitoring import proactive_monitor

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def setup_scheduler():
    """Setup all proactive monitoring scheduled tasks"""
    logger.info("🚀 Setting up proactive AI scheduler...")

    # === CRITICAL: Streak Risk Monitoring (Every 5 minutes) ===
    scheduler.add_job(
        proactive_monitor.monitor_streak_risks,
        IntervalTrigger(minutes=5),
        id="monitor_streak_risks",
        replace_existing=True,
        max_instances=1
    )
    logger.info("✅ Streak risk monitoring: Every 5 minutes")

    # === Morning Check-ins (Every 5 minutes, checks user timezone) ===
    scheduler.add_job(
        proactive_monitor.send_morning_check_ins,
        IntervalTrigger(minutes=5),
        id="morning_check_ins",
        replace_existing=True,
        max_instances=1
    )
    logger.info("✅ Morning check-ins: Every 5 minutes (timezone-aware)")

    # === Burnout Detection (Every hour) ===
    scheduler.add_job(
        proactive_monitor.detect_burnout_patterns,
        IntervalTrigger(hours=1),
        id="burnout_detection",
        replace_existing=True,
        max_instances=1
    )
    logger.info("✅ Burnout detection: Every hour")

    # === Weekly Insights (Sundays at 8 PM) ===
    scheduler.add_job(
        proactive_monitor.send_weekly_insights,
        CronTrigger(day_of_week='sun', hour=20, minute=0),
        id="weekly_insights",
        replace_existing=True,
        max_instances=1
    )
    logger.info("✅ Weekly insights: Sundays at 8 PM")

    # === Milestone Celebrations (Every 10 minutes) ===
    scheduler.add_job(
        proactive_monitor.celebrate_milestones,
        IntervalTrigger(minutes=10),
        id="milestone_celebrations",
        replace_existing=True,
        max_instances=1
    )
    logger.info("✅ Milestone celebrations: Every 10 minutes")

    # === Time Optimization Suggestions (Daily at 7 AM) ===
    scheduler.add_job(
        proactive_monitor.optimize_writing_times,
        CronTrigger(hour=7, minute=0),
        id="time_optimization",
        replace_existing=True,
        max_instances=1
    )
    logger.info("✅ Time optimization: Daily at 7 AM")

    logger.info("✅ Proactive AI scheduler setup complete!")


def start_scheduler():
    """Start the scheduler"""
    if not scheduler.running:
        scheduler.start()
        logger.info("🚀 Proactive AI scheduler started!")
    else:
        logger.warning("Scheduler already running")


def shutdown_scheduler():
    """Shutdown the scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("🛑 Proactive AI scheduler stopped")
