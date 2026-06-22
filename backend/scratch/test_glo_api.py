import httpx
import asyncio
import json

async def main():
    url_date = "https://www.glo.or.th/api/checking/getLotteryResult"
    headers = {"Content-Type": "application/json"}
    
    # 15 มิถุนายน 2026 (ไม่มีหวยออก หวยออก 16)
    payload = {
        "date": "15",
        "month": "06",
        "year": "2026"
    }
    print("Testing getLotteryResult for non-drawing date (15 June 2026)...")
    async with httpx.AsyncClient(verify=False) as client:
        try:
            resp = await client.post(url_date, json=payload, headers=headers)
            print(f"Status Code: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print("Response JSON:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                print("Failed:", resp.text)
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
