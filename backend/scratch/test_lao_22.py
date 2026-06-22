import asyncio
import json
from backend.data_collection.scrapers.lao_scraper import LaoScraper

async def main():
    scraper = LaoScraper()
    try:
        res = await scraper.fetch("2026-06-22")
        print("Success:")
        print(json.dumps(res, indent=2, default=str))
    except Exception as e:
        print("Expected Error or behavior:", e)

asyncio.run(main())
