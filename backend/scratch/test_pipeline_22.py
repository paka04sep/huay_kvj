import asyncio
import logging
import sys
from backend.data_collection.pipeline import DataPipeline

# Enable logging
logging.basicConfig(level=logging.INFO)

async def main():
    pipeline = DataPipeline()
    await pipeline.initialize()
    try:
        # Run pipeline for 2026-06-22
        print("Running pipeline for 2026-06-22...")
        success = await pipeline.run_single_draw_pipeline("lao", "2026-06-22")
        print("Pipeline run success:", success)
        
        # Check what is in DB for 2026-06-22
        row = await pipeline.db_conn.fetchrow("""
            SELECT r.id, r.draw_date, r.status, r.result_json, r.error_reason
            FROM lottery_results r
            JOIN lottery_types t ON r.lottery_type_id = t.id
            WHERE t.code = 'lao' AND r.draw_date = '2026-06-22'
        """)
        if row:
            print("DB Record for 2026-06-22:")
            print(f"  ID: {row['id']}")
            print(f"  Date: {row['draw_date']}")
            print(f"  Status: {row['status']}")
            print(f"  Error: {row['error_reason']}")
            print(f"  Result: {row['result_json']}")
        else:
            print("No DB record found for 2026-06-22.")
    finally:
        await pipeline.close()

if __name__ == "__main__":
    asyncio.run(main())
