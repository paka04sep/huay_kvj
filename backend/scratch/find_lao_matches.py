import httpx
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

url = "https://www.sanook.com/news/archive/laolotto/"
r = httpx.get(url, headers=headers, verify=False)
lao_matches = re.findall(r'href="([^"]*laolotto[^"]*)"', r.text)
print("Lao matches on Page 1:")
for m in set(lao_matches):
    print("  ", m)
