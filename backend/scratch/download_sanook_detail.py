import httpx
import asyncio

async def main():
    url = "https://www.sanook.com/news/laolotto/19062569/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    async with httpx.AsyncClient(headers=headers, verify=False, timeout=15) as client:
        try:
            resp = await client.get(url)
            print(f"Status Code: {resp.status_code}")
            if resp.status_code == 200:
                with open("scratch/sanook_lao_detail.html", "w", encoding="utf-8") as f:
                    f.write(resp.text)
                print("Saved Sanook Lao Detail successfully.")
            else:
                print("Failed:", resp.status_code)
        except Exception as e:
            print("Error connecting:", e)

if __name__ == "__main__":
    asyncio.run(main())
