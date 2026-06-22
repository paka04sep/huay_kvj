import os
import redis.asyncio as aioredis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_redis_client = None

async def init_redis():
    """
    เริ่มต้นการเชื่อมต่อ Redis
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client

async def close_redis():
    """
    ปิดการเชื่อมต่อ Redis
    """
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None

async def get_redis():
    """
    Dependency สำหรับใช้งานใน FastAPI Route เพื่อดึง Redis Client ไปใช้งาน
    """
    global _redis_client
    if _redis_client is None:
        await init_redis()
    return _redis_client
