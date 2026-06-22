from fastapi import APIRouter, Depends, HTTPException, Query
import asyncpg
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
        # หวยลาวออก จันทร์, พุธ, ศุกร์
        # หาว่าวันถัดไปคือวันอะไร
        curr = latest_date + timedelta(days=1)
        while curr.weekday() not in (0, 2, 4): # 0=Mon, 2=Wed, 4=Fri
            curr += timedelta(days=1)
        return curr
        
    return latest_date + timedelta(days=1)

@router.get("")
async def get_predictions(
    type: str = Query(..., description="ประเภทหวย: glo, lao"),
    db: asyncpg.Connection = Depends(get_db)
):
    """
    ทำนายผลเลขเด่นสำหรับงวดถัดไป โดยผสานโมเดล LSTM และ Frequency Stats (Ensemble Method)
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
        # ทำนายเลขท้าย 2 ตัว และ 3 ตัวท้าย
        predictions_2 = await predictor.predict_next(code=type, target="last_2", top_k=5)
        predictions_3 = await predictor.predict_next(code=type, target="last_3", top_k=5)
        
        return {
            "lottery_type": type,
            "latest_draw_date": latest_date_row.isoformat(),
            "next_draw_date": next_draw_date.isoformat(),
            "predictions": {
                "last_2": predictions_2,
                "last_3": predictions_3
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running prediction engine: {e}")
