from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from backend.api.database import init_db_pool, close_db_pool
from backend.api.cache import init_redis, close_redis
from backend.api.routes import results, stats, predictions

# นำเข้าเครื่องมือสแครปผลหวยและตัวรันงานอัตโนมัติ (Scheduler)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from backend.data_collection.scheduler import run_glo_task, run_lao_task

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: สร้าง connection pools
    await init_db_pool()
    await init_redis()

    # เริ่มงานตั้งเวลาดึงข้อมูลหวย (Scheduler) ภายในโปรเซสเดียวกัน
    scheduler = AsyncIOScheduler()
    
    # 1. หวยรัฐบาลไทย (GLO) รันทุกๆ 10 นาทีในช่วงเวลาออกผล
    scheduler.add_job(
        run_glo_task,
        trigger=CronTrigger(day="1,16", hour="15", minute="*/10"),
        id="glo_scheduled_job",
        replace_existing=True
    )
    
    # 2. หวยลาว (LAO) รันทุกๆ 5 นาทีในช่วงเวลาออกผล
    scheduler.add_job(
        run_lao_task,
        trigger=CronTrigger(day_of_week="mon-fri", hour="20", minute="30-59/5"),
        id="lao_scheduled_job",
        replace_existing=True
    )
    scheduler.add_job(
        run_lao_task,
        trigger=CronTrigger(day_of_week="mon-fri", hour="21", minute="0"),
        id="lao_scheduled_job_21",
        replace_existing=True
    )
    
    scheduler.start()
    print("[+] Lifespan: FastAPI and APScheduler started together successfully.", flush=True)

    yield

    # Shutdown: ปิดระบบตั้งเวลาและ Connection pools
    scheduler.shutdown()
    await close_db_pool()
    await close_redis()

# สร้างแอป FastAPI
app = FastAPI(
    title="Huay KVJ API",
    description="Backend REST API สำหรับระเบียบวิเคราะห์ และตรวจผลหวยรัฐบาลและหวยลาว",
    version="1.0.0",
    lifespan=lifespan
)

# ตั้งค่า CORS เพื่อเชื่อมกับ Next.js Frontend
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.1.118:3000",
]

# อนุญาตให้เปิดกำหนด origins ผ่าน env ได้
env_origins = os.getenv("ALLOWED_ORIGINS")
if env_origins:
    origins.extend([o.strip() for o in env_origins.split(",")])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# นำ Router เข้ามาเชื่อมโยง
app.include_router(results.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(predictions.router, prefix="/api")

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "app": "Huay KVJ Backend API",
        "version": "1.0.0"
    }
