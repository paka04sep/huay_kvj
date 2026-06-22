from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime, timezone
from typing import Dict, Any, Optional, List

class LotteryResultModel(BaseModel):
    lottery_type: str = Field(..., description="ประเภทหวย: glo, lao, hanoi, yeekee")
    draw_date: date = Field(..., description="วันที่ออกรางวัล (YYYY-MM-DD)")
    draw_number: Optional[str] = Field(None, description="งวดที่ / รอบที่ (ถ้ามี)")
    numbers: Dict[str, Any] = Field(..., description="ผลการออกรางวัลในรูปแบบ JSON")
    source_url: str = Field(..., description="URL แหล่งข้อมูลที่สแครปมา")
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="เวลาที่ดึงข้อมูล")

    @field_validator("draw_date")
    @classmethod
    def no_future_date(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("draw_date cannot be in the future")
        return v

    @field_validator("numbers")
    @classmethod
    def validate_numbers_by_type(cls, v: Dict[str, Any], info) -> Dict[str, Any]:
        # เข้าถึง lottery_type จาก validation values
        # ใน Pydantic v2 ใช้ info.data เพื่อดึงค่าฟิลด์อื่น
        lottery_type = info.data.get("lottery_type")
        if not lottery_type:
            return v

        if lottery_type == "glo":
            # ตรวจสอบรางวัลหลักของสลากรัฐบาล
            if "first_prize" not in v:
                raise ValueError("Missing 'first_prize' for GLO lottery")
            if not isinstance(v["first_prize"], str) or len(v["first_prize"]) != 6 or not v["first_prize"].isdigit():
                raise ValueError("GLO 'first_prize' must be a 6-digit numeric string")
            
            if "last_2" not in v:
                raise ValueError("Missing 'last_2' for GLO lottery")
            if not isinstance(v["last_2"], str) or len(v["last_2"]) != 2 or not v["last_2"].isdigit():
                raise ValueError("GLO 'last_2' must be a 2-digit numeric string")

            # เลขหน้า 3 ตัว (มี 2 รางวัล) และ เลขท้าย 3 ตัว (มี 2 รางวัล)
            for k in ["first_3", "last_3"]:
                if k in v:
                    if not isinstance(v[k], list) or len(v[k]) != 2:
                        raise ValueError(f"GLO '{k}' must be a list containing exactly 2 items")
                    for num in v[k]:
                        if not isinstance(num, str) or len(num) != 3 or not num.isdigit():
                            raise ValueError(f"Each item in GLO '{k}' must be a 3-digit numeric string")

        elif lottery_type == "lao":
            # หวยลาว (ผล 4 ตัวหลัก)
            if "digits_4" not in v:
                raise ValueError("Missing 'digits_4' (4-digit result) for Lao lottery")
            if not isinstance(v["digits_4"], str) or len(v["digits_4"]) != 4 or not v["digits_4"].isdigit():
                raise ValueError("Lao 'digits_4' must be a 4-digit numeric string")

        elif lottery_type == "hanoi":
            # หวยฮานอย (ปกติเก็บเลข 4 ตัว หรือรางวัลพิเศษ/รางวัลที่ 1)
            if "digits_4" not in v and "special_prize" not in v:
                raise ValueError("Missing 'digits_4' or 'special_prize' for Hanoi lottery")

        elif lottery_type == "yeekee":
            # หวยยี่กี (3 ตัวบน, 2 ตัวล่าง)
            if "top_3" not in v:
                raise ValueError("Missing 'top_3' for Yeekee lottery")
            if not isinstance(v["top_3"], str) or len(v["top_3"]) != 3 or not v["top_3"].isdigit():
                raise ValueError("Yeekee 'top_3' must be a 3-digit numeric string")
                
            if "bottom_2" not in v:
                raise ValueError("Missing 'bottom_2' for Yeekee lottery")
            if not isinstance(v["bottom_2"], str) or len(v["bottom_2"]) != 2 or not v["bottom_2"].isdigit():
                raise ValueError("Yeekee 'bottom_2' must be a 2-digit numeric string")

        return v
