import httpx
import json
import re
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

url = "https://www.sanook.com/news/laolotto/22062569/"
print(f"Fetching {url}...")
r = httpx.get(url, headers=headers, verify=False)
print("Status code:", r.status_code)

soup = BeautifulSoup(r.text, "html.parser")
script = soup.find("script", id="__NEXT_DATA__")
if script and script.string:
    next_data = json.loads(script.string)
    print("Found NEXT_DATA!")
    
    apollo_data = next_data["props"]["serverState"]["apollo"]["data"]
    
    # Let's find all LaoLotto nodes
    lotto_nodes = []
    for k, v in apollo_data.items():
        if isinstance(v, dict) and v.get("__typename") == "LaoLotto":
            print(f"Key: {k}, dateSlug: {v.get('dateSlug')}, prizeResult: {v.get('prizeResult')}")
            lotto_nodes.append((k, v))
            
    for k, node in lotto_nodes:
        prize_ref = node.get("prizeResult")
        if prize_ref:
            ref_id = prize_ref.get("__ref")
            if ref_id in apollo_data:
                prize_obj = apollo_data[ref_id]
                print(f"  Ref: {ref_id}, last4Prize: {prize_obj.get('last4Prize')}, last2Prize: {prize_obj.get('last2Prize')}")
else:
    print("NEXT_DATA not found!")
