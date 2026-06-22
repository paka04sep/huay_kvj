import httpx

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

url = "https://www.sanook.com/news/laolotto/"
r = httpx.get(url, headers=headers, verify=False)
print("graphql" in r.text.lower())
print("gq.sanook" in r.text.lower())
# Print all URLs in script tags or matching sanook.com
import re
urls = re.findall(r'https?://[^\s"\'>]+', r.text)
for u in set(urls):
    if "graphql" in u or "gq" in u or "api" in u:
        print(u)
