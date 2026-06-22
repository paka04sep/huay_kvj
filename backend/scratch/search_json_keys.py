import json

def search_value_in_dict(d, target, path=""):
    results = []
    if isinstance(d, dict):
        for k, v in d.items():
            current_path = f"{path}.{k}" if path else k
            if v == target:
                results.append((current_path, v))
            elif isinstance(v, (dict, list)):
                results.extend(search_value_in_dict(v, target, current_path))
    elif isinstance(d, list):
        for i, item in enumerate(d):
            current_path = f"{path}[{i}]"
            if item == target:
                results.append((current_path, item))
            elif isinstance(item, (dict, list)):
                results.extend(search_value_in_dict(item, target, current_path))
    return results

def main():
    with open("scratch/sanook_lao_next_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print("Searching for '4240' inside JSON...")
    results = search_value_in_dict(data, "4240")
    for path, val in results:
        print(f"Path: {path} -> {val}")

if __name__ == "__main__":
    main()
