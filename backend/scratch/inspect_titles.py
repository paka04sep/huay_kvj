import httpx
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Let's inspect some of the news links on page 2 to see if they are indeed Lao Lotto posts
links = [
    "https://www.sanook.com/news/9895402/",
    "https://www.sanook.com/news/9895298/",
    "https://www.sanook.com/news/9895442/",
    "https://www.sanook.com/news/9895226/",
    "https://www.sanook.com/news/9895438/",
]

for l in links:
    r = httpx.get(l, headers=headers, verify=False)
    soup = BeautifulSoup(r.text, "html.parser")
    print(f"URL: {l} -> Title: {soup.title.string if soup.title else 'No Title'}")
