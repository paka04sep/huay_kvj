from fastapi import APIRouter, Depends, HTTPException, Query
import asyncpg
import json
from collections import Counter
from typing import Dict, Any, List, Optional

from backend.api.database import get_db

router = APIRouter(prefix="/stats", tags=["statistics"])

@router.get("/hot-cold")
async def get_hot_cold_stats(
    type: str = Query(..., description="ประเภทหวย: glo, lao"),
    limit_draws: int = Query(100, ge=10, le=1000, description="จำนวนงวดล่าสุดที่ต้องการวิเคราะห์"),
    position: str = Query("last_2", description="ตำแหน่งเลข: first_prize, last_2, last_3, first_3 (สำหรับ glo) หรือ digits_4, digits_3, digits_2 (สำหรับ lao)"),
    stat_type: str = Query("numbers", description="ประเภทสถิติ: numbers (เลขชุดเต็มเช่น 00-99) หรือ digits (ความถี่เลขเดี่ยว 0-9)"),
    db: asyncpg.Connection = Depends(get_db)
):
    """
    วิเคราะห์เลขร้อน/เย็น (Hot/Cold Numbers), สรุปสถิติ คู่/คี่, สูง/ต่ำ
    """
    # 1. ตรวจสอบประเภทหวย
    type_row = await db.fetchrow("SELECT id FROM lottery_types WHERE code = $1", type)
    if not type_row:
        raise HTTPException(status_code=400, detail=f"Unsupported lottery type '{type}'")
    type_id = type_row["id"]

    # 2. ตรวจสอบ position ที่เลือกให้เหมาะกับประเภทหวย
    supported_positions = {
        "glo": ["first_prize", "last_2", "last_3", "first_3"],
        "lao": ["digits_4", "digits_3", "digits_2"]
    }
    
    if position not in supported_positions.get(type, []):
        raise HTTPException(
            status_code=400, 
            detail=f"Position '{position}' is not supported for type '{type}'. Choose from {supported_positions.get(type)}"
        )

    # 3. ดึงข้อมูลงวดล่าสุดตามจำนวนที่กำหนด
    rows = await db.fetch("""
        SELECT draw_date, result_json
        FROM lottery_results
        WHERE lottery_type_id = $1 AND status = 'active'
        ORDER BY draw_date DESC
        LIMIT $2
    """, type_id, limit_draws)

    if not rows:
        raise HTTPException(status_code=404, detail=f"No active results found to calculate stats.")

    # 4. สกัดค่ารางวัลในตำแหน่งที่เลือก
    values_list = []
    
    for r in rows:
        res_data = json.loads(r["result_json"])
        
        # กรณีวิเคราะห์รางวัลหลัก (primary)
        if position == "first_prize" and type == "glo":
            val = res_data.get("primary")
            if val:
                values_list.append(val)
        elif position == "digits_4" and type == "lao":
            val = res_data.get("primary")
            if val:
                values_list.append(val)
                
        # กรณีวิเคราะห์รางวัลย่อย (secondary)
        else:
            sec = res_data.get("secondary", {})
            # สำหรับ glo
            if type == "glo":
                if position in ["last_3", "first_3"]:
                    # เลขหน้า/ท้าย 3 ตัวของ GLO จะเป็นลิสต์ของ string เช่น ["123", "456"]
                    val_list = sec.get(position, [])
                    if isinstance(val_list, list):
                        values_list.extend(val_list)
                else:
                    val = sec.get(position)
                    if val:
                        values_list.append(val)
            # สำหรับ lao
            elif type == "lao":
                val = sec.get(position)
                if val:
                    values_list.append(val)

    if not values_list:
        raise HTTPException(status_code=404, detail=f"No values found for position '{position}'.")

    # 5. คำนวณสถิติ
    total_samples = len(values_list)
    even_count = 0
    odd_count = 0
    high_count = 0  # เลขสูง 5-9
    low_count = 0   # เลขต่ำ 0-4

    all_tokens = []  # ตัวเลขที่จะนำไปนับความถี่ (สามารถเป็นเลขชุด หรือเลขเดี่ยว)

    for val in values_list:
        # ตรวจสอบคู่/คี่ และ สูง/ต่ำ
        if val.isdigit():
            # ตรวจสอบจากเลขหลักหน่วย (ตัวสุดท้าย) ของเลขชุด
            last_digit = int(val[-1])
            if last_digit % 2 == 0:
                even_count += 1
            else:
                odd_count += 1
                
            # ตรวจสอบส่วนสูง/ต่ำ (เทียบกับค่ากลาง)
            # เลข 2 หลัก -> 00-49 (ต่ำ), 50-99 (สูง)
            # เลข 3 หลัก -> 000-499 (ต่ำ), 500-999 (สูง)
            # เลขเดี่ยว -> 0-4 (ต่ำ), 5-9 (สูง)
            val_int = int(val)
            max_val = 10 ** len(val)
            if val_int >= (max_val / 2):
                high_count += 1
            else:
                low_count += 1

        # จัดเตรียมข้อมูลนับความถี่ตาม stat_type
        if stat_type == "digits":
            # แยกระเบิดออกเป็นเลขเดี่ยวตัวสลาก เช่น "56" -> ["5", "6"]
            all_tokens.extend(list(val))
        else:
            # ใช้เลขชุดดั้งเดิม
            all_tokens.append(val)

    # นับความถี่ตัวเลข
    freq_counter = Counter(all_tokens)
    
    # ดึงตัวอย่างตัวเลขทั้งหมดที่เป็นไปได้เพื่อหาตัวที่ไม่ออกเลย (Cold Numbers)
    # สำหรับ digits: 0-9
    # สำหรับ numbers: 00-99 (สำหรับ 2 ตัว), 000-999 (สำหรับ 3 ตัว)
    expected_range = []
    if stat_type == "digits":
        expected_range = [str(i) for i in range(10)]
    else:
        sample_len = len(values_list[0]) if values_list else 2
        if sample_len == 2:
            expected_range = [f"{i:02d}" for i in range(100)]
        elif sample_len == 3:
            expected_range = [f"{i:03d}" for i in range(1000)]
        elif sample_len == 4:
            expected_range = [f"{i:04d}" for i in range(10000)]
        elif sample_len == 6:
            expected_range = [f"{i:06d}" for i in range(1000000)]

    # เติมตัวที่ความถี่เป็น 0
    full_frequencies = {}
    for num_str in expected_range:
        full_frequencies[num_str] = freq_counter.get(num_str, 0)
    
    # หากไม่ได้อยู่ในช่วงมาตรฐาน หรือมีจำนวนเยอะเกินไป ให้ใช้เฉพาะตัวที่ออกจริง
    if not full_frequencies:
        full_frequencies = dict(freq_counter)

    # เรียงลำดับความถี่
    sorted_freqs = sorted(full_frequencies.items(), key=lambda x: x[1], reverse=True)
    
    # จัดกลุ่ม Hot / Cold
    # Hot: 10 อันดับแรกที่มีความถี่สูงสุด
    # Cold: 10 อันดับแรกที่มีความถี่ต่ำสุด (รวมถึงตัวที่ไม่ออกเลย)
    hot_numbers = [{"number": num, "count": cnt} for num, cnt in sorted_freqs[:10]]
    cold_numbers = [{"number": num, "count": cnt} for num, cnt in sorted_freqs[-10:]]

    return {
        "lottery_type": type,
        "position": position,
        "stat_type": stat_type,
        "limit_draws": limit_draws,
        "total_draws_analyzed": len(rows),
        "total_numbers_sampled": total_samples,
        "hot_numbers": hot_numbers,
        "cold_numbers": cold_numbers,
        "even_odd_ratio": {
            "even_count": even_count,
            "odd_count": odd_count,
            "even_percentage": round((even_count / total_samples) * 100, 2) if total_samples > 0 else 0,
            "odd_percentage": round((odd_count / total_samples) * 100, 2) if total_samples > 0 else 0
        },
        "high_low_ratio": {
            "high_count": high_count,
            "low_count": low_count,
            "high_percentage": round((high_count / total_samples) * 100, 2) if total_samples > 0 else 0,
            "low_percentage": round((low_count / total_samples) * 100, 2) if total_samples > 0 else 0
        },
        "all_frequencies": full_frequencies
    }
