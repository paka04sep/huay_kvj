import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

# Connection Pool ของ asyncpg
_pool = None

async def init_db_pool():
    """
    เริ่มต้นสร้าง Connection Pool ของ PostgreSQL
    """
    global _pool
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not set in environment variables.")
    
    # พิมพ์ Log เพื่อตรวจสอบความถูกต้องของ Host ปลายทางในระบบคลาวด์
    import urllib.parse
    try:
        # Normalizing URL scheme for parsing
        url_to_parse = DATABASE_URL
        if not url_to_parse.startswith("postgresql://") and "://" in url_to_parse:
            url_to_parse = "postgresql" + url_to_parse[url_to_parse.find("://"):]
        parsed = urllib.parse.urlparse(url_to_parse)
        print(f"[DB_CONNECT] Host: {parsed.hostname} | Port: {parsed.port}", flush=True)
    except Exception as e:
        print(f"[DB_CONNECT] Parsing Error: {e}", flush=True)

    if _pool is None:
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=2,
            max_size=10,
            max_inactive_connection_lifetime=300
        )
    return _pool

async def close_db_pool():
    """
    ปิดการเชื่อมต่อทั้งหมดใน Connection Pool
    """
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None

async def get_db():
    """
    Dependency สำหรับใช้งานใน FastAPI Route เพื่อดึง Connection ไปใช้งาน
    และคืน Connection เข้า Pool เมื่อทำงานเสร็จสิ้น
    """
    global _pool
    if _pool is None:
        await init_db_pool()
    
    async with _pool.acquire() as connection:
        yield connection
