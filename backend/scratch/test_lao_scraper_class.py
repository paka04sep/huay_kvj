import asyncio
import json
from backend.data_collection.scrapers.lao_scraper import LaoScraper

async def main():
    scraper = LaoScraper()
    
    # 1. ทดสอบแปลงวันที่ไทย
    test_dates = [
        "หวยลาว งวดวันศุกร์ 19 มิถุนายน 2569",
        "หวยลาว งวดวันพุธ 17 มิ.ย. 2569",
        "หวยลาว งวดวันจันทร์ 8 มิถุนายน 2569"
    ]
    print("Testing Thai date parsing:")
    for td in test_dates:
        parsed = scraper._parse_thai_date(td)
        print(f"  Raw: {td} -> Parsed: {parsed}")

    # 2. ทดสอบ fetch_latest
    print("\nTesting fetch_latest()...")
    try:
        result = await scraper.fetch_latest()
        print("Success! Latest Result:")
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    except Exception as e:
        print("Error fetching latest:", e)

    # 3. ทดสอบดึงข้อมูลเฉพาะวัน (เช่น 12 มิถุนายน 2026)
    target_date = "2026-06-12"
    print(f"\nTesting fetch('{target_date}')...")
    try:
        result = await scraper.fetch(target_date)
        print(f"Success! Result for {target_date}:")
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    except Exception as e:
        print(f"Error fetching for date {target_date}:", e)

if __name__ == "__main__":
    asyncio.run(main())
