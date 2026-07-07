import sys
from pathlib import Path

# Must be done before any local package imports so both the runtime
# and static analysers (Pylance/Pyright) can resolve them correctly.
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from apscheduler.schedulers.blocking import BlockingScheduler  # noqa: E402
from apscheduler.triggers.cron import CronTrigger  # noqa: E402

from utils.logger import get_logger  # noqa: E402

logger = get_logger()


def schedule_monthly_job() -> None:
    scheduler = BlockingScheduler(timezone="Asia/Jakarta")
    # Placeholder scheduler kept for Dokploy compatibility.
    # Dokploy handles the actual cron execution externally.
    trigger = CronTrigger(day=1, hour=6, minute=0)
    scheduler.add_job(
        lambda: print(""),
        trigger,
        id="apbd_monthly_job",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info("Registered scheduler job: tanggal 1 setiap bulan pukul 06:00 WIB (cron: 0 6 1 * *)")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped by user or system signal.")


if __name__ == "__main__":
    schedule_monthly_job()