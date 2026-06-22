import os
import asyncpg
import json
import numpy as np
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

async def load_historical_sequences(code: str, target: str = "last_2") -> list:
    """
    ดึงข้อมูลประวัติหวยเรียงจากเก่าไปใหม่ และดึงตัวเลขในตำแหน่งที่สนใจ
    target: "last_2" หรือ "last_3"
    """
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not set.")

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # ดึงประเภทหวย
        type_row = await conn.fetchrow("SELECT id FROM lottery_types WHERE code = $1", code)
        if not type_row:
            raise ValueError(f"Lottery type {code} not found.")
        type_id = type_row["id"]

        # ดึงผลรางวัลเรียงจากเก่าไปใหม่ (ASC) เพื่อทำเป็น Time-Series Sequence
        rows = await conn.fetch("""
            SELECT draw_date, result_json
            FROM lottery_results
            WHERE lottery_type_id = $1 AND status = 'active'
            ORDER BY draw_date ASC
        """, type_id)

        values = []
        for r in rows:
            res_data = json.loads(r["result_json"])
            primary = res_data.get("primary")
            secondary = res_data.get("secondary", {})

            if not primary:
                continue

            if code == "glo":
                if target == "last_2":
                    val = secondary.get("last_2")
                    if val and val.isdigit():
                        values.append(int(val))
                elif target == "last_3":
                    # สำหรับ GLO: 3 ตัวบน คือ 3 หลักสุดท้ายของรางวัลที่ 1
                    if len(primary) == 6:
                        values.append(int(primary[-3:]))
            elif code == "lao":
                if target == "last_2":
                    val = secondary.get("digits_2")
                    if val and val.isdigit():
                        values.append(int(val))
                elif target == "last_3":
                    val = secondary.get("digits_3")
                    if val and val.isdigit():
                        values.append(int(val))
        
        return values
    finally:
        await conn.close()

def create_sequences(data: list, window_size: int = 12):
    """
    แปลงข้อมูลลิสต์เป็นคู่ Input Sequence (X) และ Target (y)
    """
    X = []
    y = []
    
    if len(data) <= window_size:
        return np.array([]), np.array([])
        
    for i in range(len(data) - window_size):
        X.append(data[i : i + window_size])
        y.append(data[i + window_size])
        
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)
