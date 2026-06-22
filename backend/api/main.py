from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from backend.api.database import init_db_pool, close_db_pool
from backend.api.cache import init_redis, close_redis
from backend.api.routes import results, stats, predictions

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: สร้าง connection pools
    await init_db_pool()
    await init_redis()
    yield
    # Shutdown: ปิด connection pools
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
