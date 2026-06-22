import httpx
import json
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

url = "https://www.sanook.com/news/laolotto/22062569/"
r = httpx.get(url, headers=headers, verify=False)
soup = BeautifulSoup(r.text, "html.parser")
script = soup.find("script", id="__NEXT_DATA__")
if script and script.string:
    next_data = json.loads(script.string)
    apollo_data = next_data["props"]["serverState"]["apollo"]["data"]
    for k, v in apollo_data.items():
        if isinstance(v, dict) and v.get("__typename") == "LaoLotto":
            prize_ref = v.get("prizeResult")
            print(f"Date: {v.get('dateSlug')}, prizeResult keys: {list(prize_ref.keys()) if prize_ref else None}, prizeResult value: {prize_ref}")
