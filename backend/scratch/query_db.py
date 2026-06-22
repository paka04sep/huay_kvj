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
        # Get all results for lao
        rows = await conn.fetch("""
            SELECT r.id, r.draw_date, r.draw_number, r.result_json, r.status, r.error_reason, t.code
            FROM lottery_results r
            JOIN lottery_types t ON r.lottery_type_id = t.id
            WHERE t.code = 'lao'
            ORDER BY r.draw_date DESC
            LIMIT 20
        """)
        print("Lao results:")
        for r in rows:
            print(f"ID: {r['id']}, Date: {r['draw_date']}, Draw Num: {r['draw_number']}, Status: {r['status']}, Error: {r['error_reason']}, Result: {r['result_json']}")
            
        # Get count of null results (or results with null/empty result_json/numbers)
        null_rows = await conn.fetch("""
            SELECT COUNT(*) as cnt
            FROM lottery_results
            WHERE result_json IS NULL OR result_json::text = '{}' OR status = 'rejected'
        """)
        print(f"\nNull/Rejected results count: {null_rows[0]['cnt']}")
        
    finally:
        await conn.close()

asyncio.run(main())
