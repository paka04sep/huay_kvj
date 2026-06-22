import json

def main():
    with open("scratch/sanook_lao_next_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    apollo_data = data["props"]["serverState"]["apollo"]["data"]
    
    # มองหาคีย์ที่ขึ้นต้นด้วย $ROOT_QUERY.laoLotto(
    lao_lotto_key = None
    for k in apollo_data.get("$ROOT_QUERY", {}).keys():
        if k.startswith("laoLotto("):
            lao_lotto_key = k
            break
            
    if lao_lotto_key:
        print(f"Found Lao Lotto Key in ROOT_QUERY: {lao_lotto_key}")
        # ดึงผลรางวัล
        result_ref = apollo_data["$ROOT_QUERY"][lao_lotto_key]["prizeResult"]
        # ใน apollo cache จะอ้างอิง object อื่นโดยใช้ __ref
        # เช่น result_ref = {'__ref': 'LaoLottoPrizeResult:17864'}
        ref_id = result_ref["__ref"]
        print(f"Result Reference: {ref_id}")
        
        # ดึง object จริงจาก apollo cache
        result_obj = apollo_data.get(ref_id)
        if result_obj:
            print("Lao Lotto Prize Result Object:")
            print(json.dumps(result_obj, indent=2, ensure_ascii=False))
            
            # ลองหา object หลักของงวดนั้น (ซึ่งจะเก็บ วันที่ ชื่องวด ฯลฯ)
            lotto_ref = apollo_data["$ROOT_QUERY"][lao_lotto_key]
            # และดึงรายละเอียดอื่นๆ
            print("\nLao Lotto Details:")
            for key, val in lotto_ref.items():
                if not isinstance(val, (dict, list)):
                    print(f"  {key}: {val}")
    else:
        print("Lao Lotto Key not found in ROOT_QUERY.")

if __name__ == "__main__":
    main()
