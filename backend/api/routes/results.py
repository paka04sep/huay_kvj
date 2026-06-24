from fastapi import APIRouter, Depends, HTTPException, Query
import asyncpg
import json
from typing import Dict, Any, List, Optional
from datetime import date, datetime, timezone

from backend.api.database import get_db
from backend.api.cache import get_redis

router = APIRouter(prefix="/results", tags=["results"])

async def get_latest_result_by_code(db: asyncpg.Connection, redis_client, code: str) -> Optional[Dict[str, Any]]:
    """
    ดึงผลรางวัลล่าสุดของประเภทหวย โดยพยายามดึงจาก Redis ก่อน ถ้าไม่มีค่อยดึงจาก DB
    """
    cache_key = f"lottery:latest:{code}"
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            data = json.loads(cached)
            # ตรวจสอบว่ามีข้อมูลครบถ้วนหรือไม่ หากมีข้อมูลครบให้ใช้งานได้เลย
            if all(k in data for k in ["lottery_type", "draw_number", "primary", "secondary"]):
                return data
    except Exception as e:
        # หาก Redis มีปัญหายังทำงานต่อได้จาก DB
        pass

    # ดึงจาก DB
    row = await db.fetchrow("""
        SELECT r.draw_date, r.draw_number, r.result_json, r.source_url, r.fetched_at
        FROM lottery_results r
        JOIN lottery_types t ON r.lottery_type_id = t.id
        WHERE t.code = $1 AND r.status = 'active'
        ORDER BY r.draw_date DESC
        LIMIT 1
    """, code)

    if not row:
        return None

    # แปลงผลลัพธ์
    draw_date_str = row["draw_date"].isoformat()
    result_data = json.loads(row["result_json"])
    
    # ตรวจสอบว่า fetched_at เป็น datetime และแปลงเป็น isoformat
    fetched_at_str = None
    if row["fetched_at"]:
        # asyncpg คืนค่าเป็น timezone-aware datetime หรือ naive
        # เพื่อความชัวร์ ให้แปลง
        fetched_at_str = row["fetched_at"].isoformat()
        
    response_data = {
        "lottery_type": code,
        "draw_date": draw_date_str,
        "draw_number": row["draw_number"],
        "primary": result_data.get("primary"),
        "secondary": result_data.get("secondary", {}),
        "source_url": row["source_url"],
        "fetched_at": fetched_at_str
    }

    # บันทึกลง Redis Cache (มีอายุ 24 ชั่วโมง)
    try:
        # บันทึกรูปแบบเต็มของ response_data เพื่อให้การอ่านครั้งต่อไปดึงฟิลด์ได้ครบถ้วน
        await redis_client.set(cache_key, json.dumps(response_data), ex=86400)
    except Exception:
        pass

    return response_data

@router.get("/latest")
async def get_latest_results(
    type: Optional[str] = Query(None, description="ประเภทหวย: glo, lao"),
    db: asyncpg.Connection = Depends(get_db),
    redis = Depends(get_redis)
):
    """
    ดึงผลหวยล่าสุด (ดึงจาก Cache ก่อน)
    """
    # ดึงประเภทหวยที่รองรับทั้งหมดในระบบ
    types_rows = await db.fetch("SELECT code FROM lottery_types")
    supported_codes = [r["code"] for r in types_rows]

    if type:
        if type not in supported_codes:
            raise HTTPException(status_code=400, detail=f"Unsupported lottery type '{type}'. Choose from {supported_codes}")
        
        result = await get_latest_result_by_code(db, redis, type)
        if not result:
            raise HTTPException(status_code=404, detail=f"No results found for type '{type}'")
        return result

    # ดึงล่าสุดของทุกตัว
    results = {}
    for code in supported_codes:
        res = await get_latest_result_by_code(db, redis, code)
        if res:
            results[code] = res
    return results

@router.get("/history")
async def get_history_results(
    type: str = Query(..., description="ประเภทหวย: glo, lao"),
    page: int = Query(1, ge=1, description="หน้าของข้อมูล"),
    limit: int = Query(20, ge=1, le=100, description="จำนวนรายการต่อหน้า"),
    start_date: Optional[date] = Query(None, description="วันที่เริ่ม (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="วันที่สิ้นสุด (YYYY-MM-DD)"),
    db: asyncpg.Connection = Depends(get_db)
):
    """
    ดึงประวัติผลหวยย้อนหลังแบบแบ่งหน้า (Pagination)
    """
    # ตรวจสอบประเภทหวย
    type_id_row = await db.fetchrow("SELECT id FROM lottery_types WHERE code = $1", type)
    if not type_id_row:
        raise HTTPException(status_code=400, detail=f"Unsupported lottery type '{type}'")
    
    type_id = type_id_row["id"]
    offset = (page - 1) * limit

    # สร้าง Query และ Parameters
    query_conditions = ["lottery_type_id = $1", "status = 'active'"]
    params = [type_id]
    
    if start_date:
        params.append(start_date)
        query_conditions.append(f"draw_date >= ${len(params)}")
        
    if end_date:
        params.append(end_date)
        query_conditions.append(f"draw_date <= ${len(params)}")

    condition_str = " AND ".join(query_conditions)

    # 1. นับจำนวนแถวทั้งหมดเพื่อคำนวณ Pagination metadata
    count_query = f"SELECT COUNT(*) FROM lottery_results WHERE {condition_str}"
    total_count = await db.fetchval(count_query, *params)

    # 2. ดึงข้อมูลจริงแบบแบ่งหน้า
    select_query = f"""
        SELECT draw_date, draw_number, result_json, source_url, fetched_at
        FROM lottery_results
        WHERE {condition_str}
        ORDER BY draw_date DESC
        LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}
    """
    
    # เพิ่ม limit และ offset ลงในพารามิเตอร์
    params.extend([limit, offset])
    
    rows = await db.fetch(select_query, *params)

    results = []
    for r in rows:
        result_data = json.loads(r["result_json"])
        results.append({
            "draw_date": r["draw_date"].isoformat(),
            "draw_number": r["draw_number"],
            "primary": result_data.get("primary"),
            "secondary": result_data.get("secondary", {}),
            "source_url": r["source_url"],
            "fetched_at": r["fetched_at"].isoformat() if r["fetched_at"] else None
        })

    total_pages = (total_count + limit - 1) // limit

    return {
        "lottery_type": type,
        "page": page,
        "limit": limit,
        "total_count": total_count,
        "total_pages": total_pages,
        "results": results
    }

@router.post("/scrape")
async def trigger_scrape(
    type: str = Query(..., description="ประเภทหวยที่ต้องการดึง: glo, lao"),
    draw_date: Optional[str] = Query(None, description="วันที่ของงวด (YYYY-MM-DD) หากไม่ใส่จะดึงงวดล่าสุด")
):
    """
    บังคับรันสแครปเปอร์เพื่ออัปเดตข้อมูลผลหวยเข้าระบบทันที (Manual Trigger)
    """
    if type not in ["glo", "lao"]:
        raise HTTPException(status_code=400, detail="Unsupported lottery type. Choose 'glo' or 'lao'.")
        
    from backend.data_collection.pipeline import DataPipeline
    from backend.data_collection.scrapers.glo_scraper import GLOScraper
    from backend.data_collection.scrapers.lao_scraper import LaoScraper
    
    pipeline = DataPipeline()
    await pipeline.initialize()
    
    try:
        if draw_date:
            # ตรวจสอบรูปแบบวันที่เบื้องต้น
            try:
                datetime.strptime(draw_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid draw_date format. Must be YYYY-MM-DD.")
        else:
            # ดึงงวดล่าสุดจาก scraper
            if type == "glo":
                scraper = GLOScraper()
            else:
                scraper = LaoScraper()
            
            latest = await scraper.fetch_latest()
            draw_date = latest["draw_date"]
            
        # รัน pipeline
        success = await pipeline.run_single_draw_pipeline(type, draw_date)
        
        # ค้นหาผลลัพธ์ใน DB อีกครั้งเพื่อส่งคืนให้ผู้ใช้เห็น
        row = await pipeline.db_conn.fetchrow("""
            SELECT r.draw_number, r.result_json, r.status, r.source_url
            FROM lottery_results r
            JOIN lottery_types t ON r.lottery_type_id = t.id
            WHERE t.code = $1 AND r.draw_date = $2
        """, type, datetime.strptime(draw_date, "%Y-%m-%d").date())
        
        result_details = {}
        if row:
            result_details = {
                "draw_number": row["draw_number"],
                "status": row["status"],
                "source_url": row["source_url"],
                "data": json.loads(row["result_json"])
            }
            
        return {
            "status": "success",
            "message": f"Scraped and processed {type.upper()} for date {draw_date} successfully.",
            "draw_date": draw_date,
            "pipeline_success": success,
            "result": result_details
        }
        
    except Exception as e:
        import logging
        logging.getLogger("api.results").error(f"Manual scrape failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to scrape: {str(e)}")
    finally:
        await pipeline.close()
