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
    
    # Print the specific key for 22062569 result
    target_key = '$ROOT_QUERY.laoLotto({"date":"22062569"}).prizeResult'
    print(f"Key: {target_key}")
    print(apollo_data.get(target_key))
    
    # Print another one for 19062569 to compare
    comp_key = '$ROOT_QUERY.laoLottoes({"first":6}).edges.1.node.prizeResult'
    print(f"Key: {comp_key}")
    print(apollo_data.get(comp_key))
    
    # Print what keys are actually in prizeResult dict for 22062569 node
    node_key = '$ROOT_QUERY.laoLotto({"date":"22062569"})'
    print(f"Node: {node_key}")
    print(apollo_data.get(node_key))
