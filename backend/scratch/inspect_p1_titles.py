import httpx
from bs4 import BeautifulSoup
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

url = "https://www.sanook.com/news/archive/laolotto/"
r = httpx.get(url, headers=headers, verify=False)
soup = BeautifulSoup(r.text, "html.parser")
links = [a.get("href") for a in soup.find_all("a") if a.get("href")]
news_links = [l for l in links if re.match(r"https://www.sanook.com/news/\d+/", l)]

print(f"Total news ID links on Page 1: {len(news_links)}")
for l in list(set(news_links))[:15]:
    r2 = httpx.get(l, headers=headers, verify=False)
    soup2 = BeautifulSoup(r2.text, "html.parser")
    print(f"URL: {l} -> Title: {soup2.title.string if soup2.title else 'No Title'}")
