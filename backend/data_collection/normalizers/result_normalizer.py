from typing import Dict, Any, Union

def normalize_glo(numbers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizer สำหรับ สลากกินแบ่งรัฐบาล (GLO)
    """
    return {
        "primary": numbers["first_prize"],
        "secondary": {
            "last_2": numbers.get("last_2"),
            "first_3": numbers.get("first_3", []),
            "last_3": numbers.get("last_3", []),
            "near_first": numbers.get("near_first", []), # รางวัลข้างเคียงรางวัลที่ 1
        },
        "raw": numbers
    }

def normalize_lao(numbers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizer สำหรับ หวยลาว
    """
    digits_4 = numbers["digits_4"]
    return {
        "primary": digits_4,
        "secondary": {
            "digits_3": digits_4[1:],  # 3 ตัวท้าย
            "digits_2": digits_4[2:],  # 2 ตัวท้าย
        },
        "raw": numbers
    }

def normalize_hanoi(numbers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizer สำหรับ หวยฮานอย
    """
    # รองรับโครงสร้างข้อมูลที่หลากหลายของฮานอย
    primary = numbers.get("digits_4") or numbers.get("special_prize")
    return {
        "primary": primary,
        "secondary": {
            "digits_3": primary[1:] if primary and len(primary) >= 4 else None,
            "digits_2": primary[2:] if primary and len(primary) >= 4 else None,
        },
        "raw": numbers
    }

def normalize_yeekee(numbers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizer สำหรับ หวยยี่กี
    """
    return {
        "primary": numbers["top_3"],
        "secondary": {
            "bottom_2": numbers.get("bottom_2")
        },
        "raw": numbers
    }

def normalize_result(lottery_type: str, numbers: Dict[str, Any]) -> Dict[str, Any]:
    """
    ฟังก์ชันกลางในการ normalize ข้อมูลผลรางวัลหวยแต่ละประเภท
    """
    if lottery_type == "glo":
        return normalize_glo(numbers)
    elif lottery_type == "lao":
        return normalize_lao(numbers)
    elif lottery_type == "hanoi":
        return normalize_hanoi(numbers)
    elif lottery_type == "yeekee":
        return normalize_yeekee(numbers)
    else:
        raise ValueError(f"Unknown lottery type: {lottery_type}")
