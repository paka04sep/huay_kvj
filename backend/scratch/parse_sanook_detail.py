from bs4 import BeautifulSoup
import re

def main():
    with open("scratch/sanook_lao_detail.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    soup = BeautifulSoup(html, "html.parser")
    
    # 1. แสดงหัวข้อข่าว (title)
    print("Page Title:", soup.title.text if soup.title else "No Title")
    
    # 2. ลองค้นหาตัวหนา (strong) ที่มีตัวเลข 4-6 หลัก
    print("\nLooking for strong elements with 4-6 digits:")
    for strong in soup.find_all("strong"):
        text = strong.text.strip().replace(" ", "").replace("-", "")
        if text.isdigit() and 4 <= len(text) <= 6:
            print(f"  Found strong digit: '{strong.text.strip()}' (len={len(text)})")
            
    # 3. ลองค้นหา class หรือ id ที่เกี่ยวกับ lotto หรือ prize
    print("\nLooking for elements with class/id matching 'lotto' or 'prize':")
    for el in soup.find_all(class_=re.compile("lotto|prize|result", re.I)):
        text = el.text.strip()
        if text and len(text) < 100:
            print(f"  Class: {el.get('class')} | Text: '{text[:50]}...'")
            
    # 4. แสดงข้อความที่มีคำว่า "เลข 6 ตัว" หรือ "เลข 4 ตัว" หรือ "เลขท้าย 2 ตัว" ในเนื้อหาข่าว
    print("\nSearching paragraphs for Lao lottery terms:")
    for p in soup.find_all(["p", "div", "span"]):
        p_text = p.text.strip()
        if any(term in p_text for term in ["เลข 6 ตัว", "เลข 5 ตัว", "เลข 4 ตัว", "เลข 3 ตัว", "เลข 2 ตัว"]):
            print(f"  Tag: {p.name} | Content: '{p_text[:120]}...'")

if __name__ == "__main__":
    main()
