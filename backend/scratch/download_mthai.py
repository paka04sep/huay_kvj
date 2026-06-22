import httpx
import asyncio

async def main():
    url = "https://lotto.mthai.com/lao"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    async with httpx.AsyncClient(headers=headers, verify=False, timeout=10) as client:
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                with open("scratch/mthai_lao.html", "w", encoding="utf-8") as f:
                    f.write(resp.text)
                print("Saved HTML to scratch/mthai_lao.html successfully.")
            else:
                print("Failed to fetch MThai:", resp.status_code)
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
