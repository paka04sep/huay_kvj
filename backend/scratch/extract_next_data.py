from bs4 import BeautifulSoup
import json

def main():
    with open("scratch/sanook_lao_detail.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    
    if script:
        data = json.loads(script.string)
        with open("scratch/sanook_lao_next_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("Successfully extracted NEXT_DATA JSON!")
        # ลองสแกนหาข้อความข่าวหรือรางวัล
        # ปกติเนื้อหาหลักจะอยู่ใน props -> pageProps
        page_props = data.get("props", {}).get("pageProps", {})
        print("PageProps keys:", list(page_props.keys()))
        
        # ลองสแกนหา key ที่น่าจะเก็บผลหวย
        # บางทีอาจจะอยู่ใน 'lotto' หรือ 'newsDetail' หรือ 'channel'
        # ลองหาคำว่า "4240" ใน JSON ที่แปลงเป็น string ว่าอยู่ภายใต้คีย์ไหน
    else:
        print("Could not find __NEXT_DATA__ script.")

if __name__ == "__main__":
    main()
