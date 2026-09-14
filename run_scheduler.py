"""Standalone process: runs the birthday job once a day, on its own schedule.

This is deliberately separate from run.py (the web dashboard). They are two
independent processes - stopping/restarting the dashboard (e.g. to pick up
a code change) must not skip a day's birthday check, and vice versa. Leave
this running (its own terminal tab, or eventually a system service) for the
daily check to actually fire.

Configure the time via BIRTHDAY_JOB_HOUR / BIRTHDAY_JOB_MINUTE in .env
(defaults to 19:00 Asia/Jerusalem time, i.e. after nightfall for most of
the year).
"""
import logging
import os

from apscheduler.schedulers.blocking import BlockingScheduler

from app import create_app
from app.jobs.birthday_job import run_birthday_job

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

JOB_HOUR = int(os.environ.get("BIRTHDAY_JOB_HOUR", 19))
JOB_MINUTE = int(os.environ.get("BIRTHDAY_JOB_MINUTE", 0))

app = create_app()


def run_job():
    with app.app_context():
        run_birthday_job()


def main():
    scheduler = BlockingScheduler(timezone="Asia/Jerusalem")
    scheduler.add_job(run_job, "cron", hour=JOB_HOUR, minute=JOB_MINUTE)
    logger.info(
        "Scheduler started - birthday job will run daily at %02d:%02d (Asia/Jerusalem)",
        JOB_HOUR, JOB_MINUTE,
    )
    scheduler.start()


if __name__ == "__main__":
    main()
