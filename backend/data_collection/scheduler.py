import asyncio
import logging
import os
import sys
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

# เพิ่ม PYTHONPATH ให้หาโมดูลหลักเจอ
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.data_collection.pipeline import DataPipeline
from backend.data_collection.alerts import send_alert

# โหลดคอนฟิก
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("scheduler")

async def run_glo_task():
    logger.info("Scheduler Triggered GLO task...")
    pipeline = DataPipeline()
    await pipeline.initialize()
    try:
        from backend.data_collection.scrapers.glo_scraper import GLOScraper
        scraper = GLOScraper()
        latest = await scraper.fetch_latest()
        draw_date = latest["draw_date"]
        logger.info(f"Scheduler: GLO latest draw date detected: {draw_date}. Running pipeline...")
        success = await pipeline.run_single_draw_pipeline("glo", draw_date)
        if success:
            logger.info(f"Scheduler: GLO draw {draw_date} updated successfully.")
        else:
            logger.warning(f"Scheduler: GLO draw {draw_date} pipeline execution did not succeed.")
    except Exception as e:
        logger.error(f"Scheduler: GLO task failed: {e}")
        await send_alert(
            message=f"เกิดข้อผิดพลาดขณะรันกำหนดเวลาสแครปหวยรัฐบาล (GLO)\nรายละเอียด: {e}",
            title="Scheduled Task Error (GLO)"
        )
    finally:
        await pipeline.close()

async def run_lao_task():
    logger.info("Scheduler Triggered LAO task...")
    pipeline = DataPipeline()
    await pipeline.initialize()
    try:
        from backend.data_collection.scrapers.lao_scraper import LaoScraper
        scraper = LaoScraper()
        latest = await scraper.fetch_latest()
        draw_date = latest["draw_date"]
        logger.info(f"Scheduler: LAO latest draw date detected: {draw_date}. Running pipeline...")
        success = await pipeline.run_single_draw_pipeline("lao", draw_date)
        if success:
            logger.info(f"Scheduler: LAO draw {draw_date} updated successfully.")
        else:
            logger.warning(f"Scheduler: LAO draw {draw_date} pipeline execution did not succeed.")
    except Exception as e:
        logger.error(f"Scheduler: LAO task failed: {e}")
        await send_alert(
            message=f"เกิดข้อผิดพลาดขณะรันกำหนดเวลาสแครปหวยลาว (LAO)\nรายละเอียด: {e}",
            title="Scheduled Task Error (LAO)"
        )
    finally:
        await pipeline.close()

async def main():
    # รองรับการรันแบบทดสอบทันที (Manual Trigger)
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        logger.info("Starting scheduler in TEST mode (running tasks once immediately)...")
        await run_glo_task()
        await run_lao_task()
        logger.info("TEST mode execution finished.")
        return

    scheduler = AsyncIOScheduler()

    # 1. หวยรัฐบาลไทย (GLO)
    # ออกทุกวันที่ 1 และ 16 ของเดือน ในช่วงเวลา 15:00 น. - 18:00 น. เพื่อรองรับการอัปเดตช้า
    scheduler.add_job(
        run_glo_task,
        trigger=CronTrigger(day="1,16", hour="15", minute="*/10"),
        id="glo_scheduled_job_15",
        name="Scrape GLO Results (15:00-15:50 every 10 mins)",
        replace_existing=True
    )
    scheduler.add_job(
        run_glo_task,
        trigger=CronTrigger(day="1,16", hour="16", minute="*/20"),
        id="glo_scheduled_job_16",
        name="Scrape GLO Results (16:00-16:40 every 20 mins)",
        replace_existing=True
    )
    scheduler.add_job(
        run_glo_task,
        trigger=CronTrigger(day="1,16", hour="17", minute="0,30"),
        id="glo_scheduled_job_17",
        name="Scrape GLO Results (17:00, 17:30)",
        replace_existing=True
    )
    logger.info("Added GLO cron jobs: 1st/16th of month from 15:00 to 17:30.")

    # 2. หวยลาว (LAO)
    # ออกทุกวัน จันทร์ - ศุกร์ ช่วงเวลา 20:30 น. - 23:59 น. เพื่อรองรับการอัปเดตช้า
    scheduler.add_job(
        run_lao_task,
        trigger=CronTrigger(day_of_week="mon-fri", hour="20", minute="30-59/5"),
        id="lao_scheduled_job_20",
        name="Scrape LAO Results (20:30-20:55 every 5 mins)",
        replace_existing=True
    )
    scheduler.add_job(
        run_lao_task,
        trigger=CronTrigger(day_of_week="mon-fri", hour="21", minute="*/15"),
        id="lao_scheduled_job_21",
        name="Scrape LAO Results (21:00-21:45 every 15 mins)",
        replace_existing=True
    )
    scheduler.add_job(
        run_lao_task,
        trigger=CronTrigger(day_of_week="mon-fri", hour="22,23", minute="*/30"),
        id="lao_scheduled_job_22_23",
        name="Scrape LAO Results (22:00-23:30 every 30 mins)",
        replace_existing=True
    )
    logger.info("Added LAO cron jobs: Mon-Fri from 20:30 to 23:30.")

    logger.info("Starting APScheduler...")
    scheduler.start()

    try:
        # รักษาความต่อเนื่องของ Process หลักในการรัน Scheduler
        while True:
            await asyncio.sleep(1000)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
