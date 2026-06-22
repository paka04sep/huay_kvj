import asyncio
import httpx
import json
from datetime import datetime, timedelta

async def check_date(client, date_str):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    thai_year = date_obj.year + 543
    date_slug = f"{date_obj.day:02d}{date_obj.month:02d}{thai_year}"
    url = f"https://www.sanook.com/news/laolotto/{date_slug}/"
    try:
        # We can just do a HEAD request or a GET request with limited bytes to save bandwidth
        resp = await client.head(url, timeout=5)
        if resp.status_code == 200:
            return date_str
    except Exception:
        pass
    return None

async def main():
    # Generate all Mon, Wed, Fri from 2021-01-01 to 2026-06-22
    start_date = datetime(2021, 1, 1)
    end_date = datetime(2026, 6, 22)
    
    current = start_date
    candidates = []
    while current <= end_date:
        if current.weekday() in (0, 2, 4): # Mon, Wed, Fri
            candidates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
        
    print(f"Total candidate dates: {len(candidates)}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
    async with httpx.AsyncClient(headers=headers, verify=False, limits=limits) as client:
        # Use semaphore to limit concurrency
        sem = asyncio.Semaphore(30)
        
        async def worker(d):
            async with sem:
                return await check_date(client, d)
                
        tasks = [worker(d) for d in candidates]
        results = await asyncio.gather(*tasks)
        
    valid_dates = [r for r in results if r]
    print(f"Found {len(valid_dates)} valid draw dates on Sanook:")
    print(valid_dates[:20])
    print("...")
    print(valid_dates[-20:])
    
    # Save to a temporary file
    with open("valid_lao_dates.json", "w") as f:
        json.dump(valid_dates, f)

if __name__ == "__main__":
    asyncio.run(main())
