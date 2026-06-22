import httpx
import asyncio
from bs4 import BeautifulSoup

async def main():
    url = "https://lotto.mthai.com/lottery/lao/17852.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    async with httpx.AsyncClient(headers=headers, verify=False, timeout=10) as client:
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                with open("scratch/lao_detail.html", "w", encoding="utf-8") as f:
                    f.write(resp.text)
                print("Saved detail HTML successfully.")
                
                # ลอง parse และแสดงเนื้อหาเบื้องต้น
                soup = BeautifulSoup(resp.text, "html.parser")
                # หา tag ที่มีผลเลขรางวัล (เช่น table หรือ div)
                # เราลองหา table
                tables = soup.find_all("table")
                print(f"Found {len(tables)} tables.")
                for idx, t in enumerate(tables):
                    print(f"\nTable {idx+1}:")
                    print(t.text[:1000].strip())
            else:
                print("Failed:", resp.status_code)
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
