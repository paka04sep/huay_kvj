from bs4 import BeautifulSoup
import re

def main():
    with open("scratch/sanook_lao_archive.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    soup = BeautifulSoup(html, "html.parser")
    
    # ลองหาทุกลิงก์ที่มีคำว่า laolotto หรือลิงก์ที่เป็นข่าวหวยลาว
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.text.strip()
        
        # กรองเฉพาะลิงก์ที่เข้าข่ายข่าวหวยลาว (มักมีคีย์เวิร์ด หรือ url format เฉพาะ)
        if "laolotto" in href or "laolot" in href or "หวยลาว" in text:
            links.append((text, href))
            
    print(f"Total links found: {len(links)}")
    # แสดงตัวอย่างลิงก์ 30 อันแรก
    for idx, (text, href) in enumerate(links[:30]):
        print(f"[{idx+1}] Text: '{text}'")
        print(f"    URL:  {href}")

if __name__ == "__main__":
    main()
