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
        # Check counts before deletion
        null_cnt = await conn.fetchval("SELECT COUNT(*) FROM lottery_results WHERE result_json IS NULL")
        empty_cnt = await conn.fetchval("SELECT COUNT(*) FROM lottery_results WHERE result_json::text = '{}'")
        rejected_cnt = await conn.fetchval("SELECT COUNT(*) FROM lottery_results WHERE status = 'rejected'")
        
        print(f"Before cleanup:")
        print(f"  Null result_json rows: {null_cnt}")
        print(f"  Empty result_json ('{{}}') rows: {empty_cnt}")
        print(f"  Rejected status rows: {rejected_cnt}")
        
        # Perform cleanup
        deleted = await conn.execute("""
            DELETE FROM lottery_results 
            WHERE result_json IS NULL 
               OR result_json::text = '{}' 
               OR status = 'rejected'
        """)
        print(f"\nCleanup query executed: {deleted}")
        
        # Check counts after deletion
        null_cnt = await conn.fetchval("SELECT COUNT(*) FROM lottery_results WHERE result_json IS NULL")
        empty_cnt = await conn.fetchval("SELECT COUNT(*) FROM lottery_results WHERE result_json::text = '{}'")
        rejected_cnt = await conn.fetchval("SELECT COUNT(*) FROM lottery_results WHERE status = 'rejected'")
        
        print(f"\nAfter cleanup:")
        print(f"  Null result_json rows: {null_cnt}")
        print(f"  Empty result_json ('{{}}') rows: {empty_cnt}")
        print(f"  Rejected status rows: {rejected_cnt}")
        
    finally:
        await conn.close()

asyncio.run(main())
