from bs4 import BeautifulSoup

def main():
    with open("scratch/sanook_lao_detail.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    soup = BeautifulSoup(html, "html.parser")
    
    # ค้นหาคำว่า "4240" ใน HTML
    targets = soup.find_all(string=lambda text: text and "4240" in text)
    print(f"Found '4240' in {len(targets)} places:")
    
    for i, t in enumerate(targets):
        parent = t.parent
        print(f"\nPlace {i+1}:")
        print(f"  Tag: {parent.name}")
        print(f"  Class: {parent.get('class')}")
        print(f"  Parent Chain: {[p.name for p in parent.parents][:3]}")
        # แสดงเนื้อหาของ parent
        print(f"  Parent content (short): {parent.text[:150].strip()}")

if __name__ == "__main__":
    main()
