import httpx
import asyncio
from bs4 import BeautifulSoup

async def test_url(url: str):
    print(f"\nTesting URL: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    # ใช้ follow_redirects=True
    async with httpx.AsyncClient(headers=headers, verify=False, timeout=10, follow_redirects=True) as client:
        try:
            resp = await client.get(url)
            print(f"Status Code: {resp.status_code}")
            print(f"Final URL: {resp.url}")
            if resp.status_code == 200:
                print("HTML Length:", len(resp.text))
                # ค้นหาคำที่เกี่ยวข้องกับหวยใน HTML
                soup = BeautifulSoup(resp.text, "html.parser")
                title = soup.title.string if soup.title else "No Title"
                print("Title:", title)
                # ค้นหาตัวเลข 4 หลักหรือเลขท้าย 2 ตัวที่อาจจะแสดงในหน้าแรก
                print(resp.text[:800])
            else:
                print(f"Failed: {resp.text[:200]}")
        except Exception as e:
            print("Error connecting:", e)

async def main():
    await test_url("https://www.sanook.com/lotto/lao/")
    await test_url("https://lotto.mthai.com/lao")
    await test_url("https://lotto.kapook.com/lao")

if __name__ == "__main__":
    asyncio.run(main())
