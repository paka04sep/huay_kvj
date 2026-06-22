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
            SELECT r.id, r.draw_date, r.draw_number, r.result_json, r.status, r.error_reason, t.code
            FROM lottery_results r
            JOIN lottery_types t ON r.lottery_type_id = t.id
            ORDER BY r.draw_date DESC
            LIMIT 50
        """)
        print("All latest results in DB:")
        for r in rows:
            print(f"Code: {r['code']}, Date: {r['draw_date']}, Status: {r['status']}, Error: {r['error_reason']}, Result: {r['result_json']}")
    finally:
        await conn.close()

asyncio.run(main())
