import json

def main():
    with open("scratch/sanook_lao_next_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    apollo_data = data["props"]["serverState"]["apollo"]["data"]
    
    print("Apollo Data Top-level Keys (first 20):")
    print(list(apollo_data.keys())[:20])
    
    # มองหาคีย์ที่มีคำว่า laoLotto
    print("\nKeys matching 'laoLotto' inside Apollo Data:")
    for k in apollo_data.keys():
        if "laoLotto" in k:
            print(f"  Key: {k}")
            print(f"  Value: {json.dumps(apollo_data[k], indent=2, ensure_ascii=False)[:300]}")
            
    # เช็คใน ROOT_QUERY
    if "$ROOT_QUERY" in apollo_data:
        print("\nROOT_QUERY keys matching 'laoLotto':")
        for k in apollo_data["$ROOT_QUERY"].keys():
            if "laoLotto" in k:
                print(f"  Key: {k}")
                print(f"  Value: {json.dumps(apollo_data['$ROOT_QUERY'][k], indent=2, ensure_ascii=False)[:300]}")

if __name__ == "__main__":
    main()
