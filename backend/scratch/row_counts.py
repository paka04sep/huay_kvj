import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch("""
            SELECT t.code, COUNT(*) as cnt
            FROM lottery_results r
            JOIN lottery_types t ON r.lottery_type_id = t.id
            GROUP BY t.code
        """)
        print("Row counts by type:")
        for r in rows:
            print(f"Code: {r['code']}, Count: {r['cnt']}")
    finally:
        await conn.close()

asyncio.run(main())
