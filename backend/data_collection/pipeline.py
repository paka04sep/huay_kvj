import os
import json
import asyncio
import logging
import asyncpg
from datetime import datetime, date, timezone
import redis.asyncio as aioredis
from dotenv import load_dotenv

from backend.data_collection.scrapers.glo_scraper import GLOScraper
from backend.data_collection.scrapers.lao_scraper import LaoScraper
from backend.data_collection.validators.result_validator import LotteryResultModel
from backend.data_collection.normalizers.result_normalizer import normalize_result

# โหลด Environment Variables
load_dotenv()

# ตั้งค่า Logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("pipeline")

# ดึง Connection Strings
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# สำหรับ asyncpg หาก connection string เป็นแบบ standard postgresql+asyncpg://
# เราต้องแปลงเป็น postgresql:// เพื่อให้ asyncpg.connect เข้าใจได้
if DATABASE_URL and DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

class DataPipeline:
    def __init__(self):
        self.db_conn = None
        self.redis_client = None

    async def initialize(self):
        """
        เตรียมการเชื่อมต่อฐานข้อมูล PostgreSQL และ Redis
        """
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL is not set in environment variables.")
        
        logger.info("Connecting to PostgreSQL database...")
        # รองรับ SSL Mode สำหรับ Supabase ในบางครั้ง
        # ถ้าติดปัญหา SSL สามารถปรับแต่งตรงนี้เพิ่มเติมได้
        self.db_conn = await asyncpg.connect(DATABASE_URL, statement_cache_size=0)
        logger.info("PostgreSQL database connected.")

        logger.info("Connecting to Redis...")
        self.redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
        logger.info("Redis connected.")

    async def close(self):
        """
        ปิดการเชื่อมต่อทั้งหมด
        """
        if self.db_conn:
            await self.db_conn.close()
            logger.info("PostgreSQL connection closed.")
        if self.redis_client:
            await self.redis_client.aclose()
            logger.info("Redis connection closed.")

    async def get_lottery_type_id(self, code: str) -> str:
        """
        ดึง UUID ของประเภทหวยจาก code
        """
        row = await self.db_conn.fetchrow(
            "SELECT id FROM lottery_types WHERE code = $1", code
        )
        if not row:
            raise ValueError(f"Lottery type code '{code}' not found in lottery_types table.")
        return str(row["id"])

    async def save_result_to_db(self, lottery_type_id: str, draw_date: str, draw_number: str, normalized_data: dict, source_url: str) -> bool:
        """
        บันทึกหรืออัปเดตผลรางวัลลงใน PostgreSQL (Upsert)
        """
        try:
            # ใช้ ON CONFLICT เพื่ออัปเดตหากมีข้อมูลอยู่แล้ว
            query = """
                INSERT INTO lottery_results 
                (lottery_type_id, draw_date, draw_number, result_json, source_url, status, fetched_at)
                VALUES ($1, $2, $3, $4, $5, 'active', CURRENT_TIMESTAMP)
                ON CONFLICT (lottery_type_id, draw_date) 
                DO UPDATE SET 
                    draw_number = EXCLUDED.draw_number,
                    result_json = EXCLUDED.result_json,
                    source_url = EXCLUDED.source_url,
                    status = 'active',
                    error_reason = NULL,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id;
            """
            # แปลง DATE จาก string
            date_val = datetime.strptime(draw_date, "%Y-%m-%d").date()
            json_str = json.dumps(normalized_data)
            
            result = await self.db_conn.fetchval(query, lottery_type_id, date_val, draw_number, json_str, source_url)
            logger.info(f"Saved result to DB. ID: {result}")
            return True
        except Exception as e:
            logger.error(f"Failed to save result to DB: {e}")
            return False

    async def cache_latest_result_to_redis(self, code: str, normalized_data: dict, draw_date: str):
        """
        บันทึกข้อมูลผลรางวัลล่าสุดลงใน Redis Cache
        """
        try:
            cache_key = f"lottery:latest:{code}"
            cache_value = {
                "draw_date": draw_date,
                "primary": normalized_data["primary"],
                "secondary": normalized_data["secondary"],
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            # เซฟข้อมูลและตั้งค่า TTL เป็น 24 ชั่วโมง (86400 วินาที)
            await self.redis_client.set(cache_key, json.dumps(cache_value), ex=86400)
            logger.info(f"Cached latest result to Redis under key: {cache_key}")
        except Exception as e:
            logger.error(f"Failed to cache to Redis: {e}")

    async def run_single_draw_pipeline(self, code: str, draw_date: str) -> bool:
        """
        รัน Pipeline ดึงข้อมูลเพียงหนึ่งงวด
        """
        try:
            lottery_type_id = await self.get_lottery_type_id(code)
            date_val = datetime.strptime(draw_date, "%Y-%m-%d").date()
            existing = await self.db_conn.fetchrow(
                "SELECT id FROM lottery_results WHERE lottery_type_id = $1 AND draw_date = $2 AND status = 'active'",
                lottery_type_id, date_val
            )
            if existing:
                logger.info(f"Draw {draw_date} for {code.upper()} is already in database and active. Skipping pipeline.")
                return True
        except Exception as check_err:
            logger.warning(f"Failed to check existing active record in DB: {check_err}. Proceeding with pipeline.")

        if code == "glo":
            scraper = GLOScraper()
        elif code == "lao":
            scraper = LaoScraper()
        else:
            logger.warning(f"Pipeline currently does not support code: {code}")
            return False
        try:
            # 1. Scrape ข้อมูล
            raw_data = await scraper.fetch(draw_date)
            
            # 2. Validate ข้อมูลด้วย Pydantic
            validated_model = LotteryResultModel(**raw_data)
            
            # 3. Normalize ข้อมูลให้อยู่ใน Standard Format
            normalized_data = normalize_result(code, validated_model.numbers)
            
            # 4. บันทึกลง PostgreSQL
            lottery_type_id = await self.get_lottery_type_id(code)
            db_success = await self.save_result_to_db(
                lottery_type_id=lottery_type_id,
                draw_date=validated_model.draw_date.isoformat(),
                draw_number=validated_model.draw_number,
                normalized_data=normalized_data,
                source_url=validated_model.source_url
            )
            
            # 5. หากเป็นงวดล่าสุดของวันนี้ หรือเป็นงวดใหม่ ให้บันทึกลง Redis Cache ด้วย
            # (ตรวจสอบเงื่อนไขว่าเป็นข้อมูลล่าสุดหรือไม่ โดยดึงวันล่าสุดของระบบมาเทียบ)
            if db_success:
                # ลองดึงรางวัลล่าสุดเพื่อตรวจสอบ
                latest_date_row = await self.db_conn.fetchrow(
                    "SELECT draw_date FROM lottery_results WHERE lottery_type_id = $1 ORDER BY draw_date DESC LIMIT 1",
                    lottery_type_id
                )
                if latest_date_row and latest_date_row["draw_date"] == validated_model.draw_date:
                    await self.cache_latest_result_to_redis(
                        code=code,
                        normalized_data=normalized_data,
                        draw_date=validated_model.draw_date.isoformat()
                    )
                    # คำนวณและบันทึกผลทำนายงวดถัดไปลงฐานข้อมูลประวัติ
                    await self.save_predictions_for_next_draw(code, validated_model.draw_date.isoformat())
            
            return db_success
        except Exception as e:
            logger.error(f"Error executing pipeline for {code} on {draw_date}: {e}")
            # บันทึกข้อมูลแบบ Rejected ลง DB เพื่อทำการ Audit/แจ้งเตือน
            try:
                lottery_type_id = await self.get_lottery_type_id(code)
                # จัดรูปแบบวันที่ให้เป็นอ็อบเจกต์ Date
                clean_date_str = draw_date.replace("-", "")
                date_val = datetime.strptime(clean_date_str, "%Y%m%d").date()
                await self.db_conn.execute(
                    """
                    INSERT INTO lottery_results 
                    (lottery_type_id, draw_date, result_json, status, error_reason, fetched_at)
                    VALUES ($1, $2, '{}', 'rejected', $3, CURRENT_TIMESTAMP)
                    ON CONFLICT (lottery_type_id, draw_date) 
                    DO UPDATE SET status = 'rejected', error_reason = EXCLUDED.error_reason, updated_at = CURRENT_TIMESTAMP
                    """,
                    lottery_type_id, date_val, str(e)
                )
                logger.info(f"Logged failed draw execution as 'rejected' in DB.")
                
                # ส่งแจ้งเตือนผ่าน Discord Webhook / LINE Notify
                from backend.data_collection.alerts import send_alert
                await send_alert(
                    message=f"เกิดข้อผิดพลาดในการดึงข้อมูลประเภท {code.upper()} สำหรับงวด {draw_date}\nข้อผิดพลาด: {e}",
                    title=f"Scraper Error Alert ({code.upper()})"
                )
            except Exception as db_err:
                logger.error(f"Could not write failure log to DB or send alert: {db_err}")
            return False

    async def save_predictions_for_next_draw(self, code: str, current_draw_date: str):
        """
        คำนวณและบันทึกผลการทำนายล่วงหน้าสำหรับงวดถัดไปลงในตาราง lottery_predictions
        """
        try:
            logger.info(f"Pipeline: Calculating predictions for next draw of {code.upper()}...")
            # 1. หาวันงวดถัดไป
            from backend.api.routes.predictions import calculate_next_draw_date
            date_val = datetime.strptime(current_draw_date, "%Y-%m-%d").date()
            next_draw = calculate_next_draw_date(code, date_val)
            
            # 2. คำนวณ Predictions (ใช้ EnsemblePredictor)
            from backend.ml.ensemble_predictor import EnsemblePredictor
            predictor = EnsemblePredictor(weight_lstm=0.6, weight_freq=0.4)
            
            raw_last_2 = await predictor.predict_next(code=code, target="last_2", top_k=100)
            raw_last_3 = await predictor.predict_next(code=code, target="last_3", top_k=1000)
            
            p_last_2 = {item["number"]: item["probability"] for item in raw_last_2}
            p_last_3 = {item["number"]: item["probability"] for item in raw_last_3}
            
            # --- 1. ทำนาย 3 ตัวบน (3-digit direct) ---
            top_3_up = sorted(raw_last_3, key=lambda x: x["probability"], reverse=True)[:5]
            predictions_3_up = [{"number": item["number"], "probability": item["probability"]} for item in top_3_up]
            
            # --- 2. ทำนาย 3 ตัวโต๊ด (3-digit Todd) ---
            todd_probs = {}
            for num_str, prob in p_last_3.items():
                sorted_chars = "".join(sorted(list(num_str)))
                todd_probs[sorted_chars] = todd_probs.get(sorted_chars, 0.0) + prob
            top_todd = sorted(todd_probs.items(), key=lambda x: x[1], reverse=True)[:5]
            predictions_todd = [{"number": num, "probability": prob} for num, prob in top_todd]
            
            # --- 3. ทำนาย 2 ตัวบน (2-digit top) ---
            two_up_probs = {}
            for num_str, prob in p_last_3.items():
                two_digit_suffix = num_str[1:]
                two_up_probs[two_digit_suffix] = two_up_probs.get(two_digit_suffix, 0.0) + prob
            top_2_up = sorted(two_up_probs.items(), key=lambda x: x[1], reverse=True)[:5]
            predictions_2_up = [{"number": num, "probability": prob} for num, prob in top_2_up]
            
            # --- 4. ทำนาย 2 ตัวล่าง (2-digit bottom) ---
            top_2_down = sorted(raw_last_2, key=lambda x: x["probability"], reverse=True)[:5]
            predictions_2_down = [{"number": item["number"], "probability": item["probability"]} for item in top_2_down]
            
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
            predictions_run_up = [{"number": num, "probability": prob} for num, prob in top_run_up]
            
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
            predictions_run_down = [{"number": num, "probability": prob} for num, prob in top_run_down]
            
            predictions_data = {
                "three_up": predictions_3_up,
                "three_todd": predictions_todd,
                "two_up": predictions_2_up,
                "two_down": predictions_2_down,
                "run_up": predictions_run_up,
                "run_down": predictions_run_down
            }
            
            # 3. บันทึกคำทำนายลงตาราง lottery_predictions
            lottery_type_id = await self.get_lottery_type_id(code)
            query = """
                INSERT INTO lottery_predictions (lottery_type_id, draw_date, predictions_json, updated_at)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                ON CONFLICT (lottery_type_id, draw_date)
                DO UPDATE SET
                    predictions_json = EXCLUDED.predictions_json,
                    updated_at = CURRENT_TIMESTAMP;
            """
            await self.db_conn.execute(query, lottery_type_id, next_draw, json.dumps(predictions_data))
            logger.info(f"Pipeline: Saved next draw predictions for {code.upper()} on date {next_draw} successfully.")
        except Exception as e:
            logger.error(f"Pipeline: Failed to calculate and save predictions: {e}")

    async def run_historical_pipeline(self, code: str, years: int = 5, limit: int = None):
        """
        ดึงข้อมูลย้อนหลังตามจำนวนปีที่กำหนด และจำกัดจำนวนงวดได้
        """
        if code == "glo":
            scraper = GLOScraper()
        elif code == "lao":
            scraper = LaoScraper()
        else:
            logger.warning(f"Historical pipeline does not support code: {code}")
            return
        try:
            # ดึงประวัติ draw_id (YYYYMMDD) ทั้งหมดจาก API
            all_draw_ids = await scraper.fetch_history_list()
            logger.info(f"Found {len(all_draw_ids)} total {code.upper()} draws from API.")

            # คำนวณช่วงเวลาที่ต้องการเก็บ (ย้อนหลัง X ปี)
            current_year = datetime.now().year
            min_year = current_year - years
            
            # กรองเอาเฉพาะงวดที่อยู่ในช่วงปีที่กำหนด
            target_draws = []
            for draw_id in all_draw_ids:
                draw_year = int(draw_id[:4])
                if draw_year >= min_year:
                    target_draws.append(draw_id)
            
            # หากต้องการจำกัดจำนวนงวด ให้เลือกจากงวดล่าสุดย้อนหลังลงไป
            if limit:
                target_draws.sort(reverse=True)
                target_draws = target_draws[:limit]
            
            # เรียงจากงวดเก่าไปงวดใหม่สำหรับการนำเข้า
            target_draws.sort()
            logger.info(f"Filtering draws from year >= {min_year} (Limit: {limit}). Total target draws to process: {len(target_draws)}")

            success_count = 0
            for idx, draw_id in enumerate(target_draws):
                if "-" in draw_id:
                    draw_date_str = draw_id
                else:
                    draw_date_str = f"{draw_id[:4]}-{draw_id[4:6]}-{draw_id[6:8]}"
                    
                logger.info(f"[{idx+1}/{len(target_draws)}] Processing {code.upper()} draw date: {draw_date_str}")
                
                success = await self.run_single_draw_pipeline(code, draw_date_str)
                if success:
                    success_count += 1
                
                # หน่วงเวลา 1 วินาที เพื่อหลีกเลี่ยงการโดน Block IP หรือ Rate Limiting
                await asyncio.sleep(1.0)
            
            logger.info(f"Historical {code.upper()} import finished. Success: {success_count}/{len(target_draws)} draws.")
            
        except Exception as e:
            logger.error(f"Error running historical pipeline for {code}: {e}")

async def main():
    # สคริปต์นี้เขียนให้สามารถรันโดยตรงเพื่อทดสอบหรือดึงข้อมูลงวดล่าสุดได้
    import sys
    
    pipeline = DataPipeline()
    await pipeline.initialize()
    
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--history":
            # รูปแบบ: python pipeline.py --history [glo/lao] [years] [limit]
            code = sys.argv[2] if len(sys.argv) > 2 else "glo"
            years = int(sys.argv[3]) if len(sys.argv) > 3 else 5
            limit = int(sys.argv[4]) if len(sys.argv) > 4 else None
            logger.info(f"Running historical data import for {code.upper()} ({years} years, limit={limit})...")
            await pipeline.run_historical_pipeline(code, years=years, limit=limit)
        else:
            # ดึงงวดล่าสุดของแต่ละประเภท
            # รูปแบบ: python pipeline.py --latest [glo/lao] หรือไม่มี arg (รันทุกประเภท)
            target_types = ["glo", "lao"]
            if len(sys.argv) > 1 and sys.argv[1] == "--latest" and len(sys.argv) > 2:
                target_types = [sys.argv[2]]
            elif len(sys.argv) > 1 and sys.argv[1] in ["glo", "lao"]:
                target_types = [sys.argv[1]]
                
            for code in target_types:
                logger.info(f"Running pipeline to fetch latest {code.upper()} result...")
                if code == "glo":
                    scraper = GLOScraper()
                elif code == "lao":
                    scraper = LaoScraper()
                else:
                    continue
                    
                try:
                    latest = await scraper.fetch_latest()
                    draw_date = latest["draw_date"]
                    logger.info(f"Latest {code.upper()} draw date detected: {draw_date}")
                    await pipeline.run_single_draw_pipeline(code, draw_date)
                except Exception as err:
                    logger.error(f"Failed to fetch latest for {code.upper()}: {err}")
    finally:
        await pipeline.close()

if __name__ == "__main__":
    asyncio.run(main())
