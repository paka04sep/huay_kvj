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
        # Check all results with null fields, e.g., result_json has null values inside or raw is null
        rows = await conn.fetch("""
            SELECT id, draw_date, status, result_json::text, error_reason
            FROM lottery_results
            WHERE result_json IS NULL 
               OR result_json::text = '{}' 
               OR result_json::text LIKE '%null%'
               OR status = 'rejected'
        """)
        print(f"Found {len(rows)} potentially null or rejected or null-containing rows:")
        for r in rows[:20]:
            print(f"ID: {r['id']}, Date: {r['draw_date']}, Status: {r['status']}, Error: {r['error_reason']}, Result: {r['result_json']}")
            
        # Let's delete all rows that have null result_json, or empty result_json '{}', or status = 'rejected'
        # Wait, let's count first.
        cnt_null = await conn.fetchval("SELECT COUNT(*) FROM lottery_results WHERE result_json IS NULL")
        cnt_empty = await conn.fetchval("SELECT COUNT(*) FROM lottery_results WHERE result_json::text = '{}'")
        cnt_rejected = await conn.fetchval("SELECT COUNT(*) FROM lottery_results WHERE status = 'rejected'")
        print(f"Null count: {cnt_null}, Empty count: {cnt_empty}, Rejected count: {cnt_rejected}")
        
    finally:
        await conn.close()

asyncio.run(main())
