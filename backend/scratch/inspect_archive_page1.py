import httpx
import re
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

url = "https://www.sanook.com/news/archive/laolotto/"
r = httpx.get(url, headers=headers, verify=False)
soup = BeautifulSoup(r.text, "html.parser")
print("Title:", soup.title.string if soup.title else "No Title")

# Find all links
links = [a.get("href") for a in soup.find_all("a") if a.get("href")]
sanook_news_links = [l for l in links if "sanook.com/news/" in l]
print("Some news links on Page 1:")
for l in list(set(sanook_news_links))[:30]:
    print("  ", l)
