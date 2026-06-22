from fastapi import APIRouter, Depends, HTTPException, Query
import asyncpg
import json
from typing import Dict, Any, List
from datetime import date, datetime, timedelta

from backend.api.database import get_db
from backend.ml.ensemble_predictor import EnsemblePredictor

router = APIRouter(prefix="/predictions", tags=["predictions"])

def calculate_next_draw_date(code: str, latest_date: date) -> date:
    """
    คำนวณวันออกรางวัลในงวดถัดไปโดยประมาณอิงจากงวดล่าสุด
    """
    if code == "glo":
        # หวยไทยออกวันที่ 1 และ 16 ของเดือน
        if latest_date.day == 16:
            # งวดถัดไปคือวันที่ 1 ของเดือนถัดไป
            if latest_date.month == 12:
                return date(latest_date.year + 1, 1, 1)
            else:
                return date(latest_date.year, latest_date.month + 1, 1)
        else:
            # งวดถัดไปคือวันที่ 16 ของเดือนเดียวกัน
            return date(latest_date.year, latest_date.month, 16)
            
    elif code == "lao":
        # หวยลาวออก จันทร์ - ศุกร์
        curr = latest_date + timedelta(days=1)
        while curr.weekday() not in (0, 1, 2, 3, 4): # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri
            curr += timedelta(days=1)
        return curr
        
    return latest_date + timedelta(days=1)

@router.get("")
async def get_predictions(
    type: str = Query(..., description="ประเภทหวย: glo, lao"),
    db: asyncpg.Connection = Depends(get_db)
):
    """
    ทำนายผลเลขเด่นสำหรับงวดถัดไป โดยแบ่งออกเป็นหลายประเภทรางวัลเชิงลึก
    """
    # 1. ตรวจสอบความถูกต้องของประเภทหวย
    type_row = await db.fetchrow("SELECT id FROM lottery_types WHERE code = $1", type)
    if not type_row:
        raise HTTPException(status_code=400, detail=f"Unsupported lottery type '{type}'")
    
    # 2. หาวันล่าสุดใน DB เพื่ออ้างอิงวันงวดถัดไป
    latest_date_row = await db.fetchval("""
        SELECT draw_date 
        FROM lottery_results 
        WHERE lottery_type_id = $1 AND status = 'active'
        ORDER BY draw_date DESC 
        LIMIT 1
    """, type_row["id"])
    
    if not latest_date_row:
        raise HTTPException(status_code=404, detail="No historical active data found to calculate predictions.")
 
    # 3. คำนวณวันงวดถัดไป
    next_draw_date = calculate_next_draw_date(type, latest_date_row)
 
    # 4. เรียกใช้งาน EnsemblePredictor
    predictor = EnsemblePredictor(weight_lstm=0.6, weight_freq=0.4)
    
    try:
        # ดึงความน่าจะเป็นดิบทั้งหมด (100 ตัวสำหรับ last_2, 1000 ตัวสำหรับ last_3)
        raw_last_2 = await predictor.predict_next(code=type, target="last_2", top_k=100)
        raw_last_3 = await predictor.predict_next(code=type, target="last_3", top_k=1000)
        
        # แปลงเป็น dict เพื่อความสะดวกในการคำนวณ marginal probability
        p_last_2 = {item["number"]: item["probability"] for item in raw_last_2}
        p_last_3 = {item["number"]: item["probability"] for item in raw_last_3}
        
        # --- 1. ทำนาย 3 ตัวบน (3-digit direct) ---
        top_3_up = sorted(raw_last_3, key=lambda x: x["probability"], reverse=True)[:5]
        predictions_3_up = [
            {"number": item["number"], "probability": item["probability"], "model": "ensemble"}
            for item in top_3_up
        ]
        
        # --- 2. ทำนาย 3 ตัวโต๊ด (3-digit Todd) ---
        todd_probs = {}
        for num_str, prob in p_last_3.items():
            # เรียงหลักจากน้อยไปมาก เพื่อจับกลุ่มตัวเลขเซ็ตเดียวกัน เช่น '321' และ '123' -> '123'
            sorted_chars = "".join(sorted(list(num_str)))
            todd_probs[sorted_chars] = todd_probs.get(sorted_chars, 0.0) + prob
            
        top_todd = sorted(todd_probs.items(), key=lambda x: x[1], reverse=True)[:5]
        predictions_todd = [
            {"number": num, "probability": prob, "model": "ensemble"}
            for num, prob in top_todd
        ]
        
        # --- 3. ทำนาย 2 ตัวบน (2-digit top) ---
        two_up_probs = {}
        for num_str, prob in p_last_3.items():
            two_digit_suffix = num_str[1:] # ดึง 2 หลักสุดท้าย
            two_up_probs[two_digit_suffix] = two_up_probs.get(two_digit_suffix, 0.0) + prob
            
        top_2_up = sorted(two_up_probs.items(), key=lambda x: x[1], reverse=True)[:5]
        predictions_2_up = [
            {"number": num, "probability": prob, "model": "ensemble"}
            for num, prob in top_2_up
        ]
        
        # --- 4. ทำนาย 2 ตัวล่าง (2-digit bottom) ---
        top_2_down = sorted(raw_last_2, key=lambda x: x["probability"], reverse=True)[:5]
        predictions_2_down = [
            {"number": item["number"], "probability": item["probability"], "model": "ensemble"}
            for item in top_2_down
        ]
        
        # --- 5. ทำนาย วิ่งบน (Run 3-up) ---
        run_up_probs = {}
        for d in range(10):
            d_str = str(d)
            prob_sum = 0.0
            for num_str, prob in p_last_3.items():
                if d_str in num_str:
                    prob_sum += prob
            run_up_probs[d_str] = prob_sum
            
        top_run_up = sorted(run_up_probs.items(), key=lambda x: x[1], reverse=True)[:3]
        predictions_run_up = [
            {"number": num, "probability": prob, "model": "ensemble"}
            for num, prob in top_run_up
        ]
        
        # --- 6. ทำนาย วิ่งล่าง (Run 2-down) ---
        run_down_probs = {}
        for d in range(10):
            d_str = str(d)
            prob_sum = 0.0
            for num_str, prob in p_last_2.items():
                if d_str in num_str:
                    prob_sum += prob
            run_down_probs[d_str] = prob_sum
            
        top_run_down = sorted(run_down_probs.items(), key=lambda x: x[1], reverse=True)[:3]
        predictions_run_down = [
            {"number": num, "probability": prob, "model": "ensemble"}
            for num, prob in top_run_down
        ]
        
        return {
            "lottery_type": type,
            "latest_draw_date": latest_date_row.isoformat(),
            "next_draw_date": next_draw_date.isoformat(),
            "predictions": {
                "three_up": predictions_3_up,
                "three_todd": predictions_todd,
                "two_up": predictions_2_up,
                "two_down": predictions_2_down,
                "run_up": predictions_run_up,
                "run_down": predictions_run_down
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running prediction engine: {e}")

@router.get("/history")
async def get_predictions_history(
    type: str = Query(..., description="ประเภทหวย: glo, lao"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: asyncpg.Connection = Depends(get_db)
):
    """
    ดึงประวัติการทำนายปัญญาประดิษฐ์ย้อนหลังเปรียบเทียบกับผลรางวัลจริง
    """
    type_row = await db.fetchrow("SELECT id FROM lottery_types WHERE code = $1", type)
    if not type_row:
        raise HTTPException(status_code=400, detail=f"Unsupported lottery type '{type}'")
    
    type_id = type_row["id"]
    offset = (page - 1) * limit
    
    total_count = await db.fetchval("""
        SELECT COUNT(*) FROM lottery_predictions 
        WHERE lottery_type_id = $1
    """, type_id)
    
    query = """
        SELECT 
            p.draw_date,
            p.predictions_json,
            r.result_json,
            r.draw_number
        FROM lottery_predictions p
        LEFT JOIN lottery_results r ON p.lottery_type_id = r.lottery_type_id AND p.draw_date = r.draw_date
        WHERE p.lottery_type_id = $1
        ORDER BY p.draw_date DESC
        LIMIT $2 OFFSET $3
    """
    rows = await db.fetch(query, type_id, limit, offset)
    
    results = []
    for row in rows:
        pred_data = json.loads(row["predictions_json"])
        result_data = json.loads(row["result_json"]) if row["result_json"] else None
        
        results.append({
            "draw_date": row["draw_date"].isoformat(),
            "draw_number": row["draw_number"],
            "predictions": pred_data,
            "actual_result": result_data
        })
        
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0
    
    return {
        "lottery_type": type,
        "page": page,
        "limit": limit,
        "total_count": total_count,
        "total_pages": total_pages,
        "results": results
    }


