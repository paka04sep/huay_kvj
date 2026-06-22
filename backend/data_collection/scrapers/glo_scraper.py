import httpx
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timezone, timedelta
from backend.data_collection.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class GLOScraper(BaseScraper):
    """
    Scraper สำหรับสลากกินแบ่งรัฐบาลไทย (GLO)
    ดึงข้อมูลผลรางวัลโดยตรงจาก Official GLO API (glo.or.th)
    """

    def __init__(self):
        super().__init__(lottery_type="glo")
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.glo.or.th/"
        }

    async def fetch(self, draw_date: str) -> Dict[str, Any]:
        """
        ดึงข้อมูลตามวันที่ (draw_date ในฟอร์แมต YYYY-MM-DD)
        """
        url = "https://www.glo.or.th/api/checking/getLotteryResult"
        
        # แปลงวันที่ 'YYYY-MM-DD' แยกเป็น date, month, year (ค.ศ.)
        try:
            date_obj = datetime.strptime(draw_date, "%Y-%m-%d")
        except ValueError:
            # รองรับกรณีส่ง YYYYMMDD
            date_obj = datetime.strptime(draw_date, "%Y%m%d")

        payload = {
            "date": date_obj.strftime("%d"),
            "month": date_obj.strftime("%m"),
            "year": date_obj.strftime("%Y")
        }

        logger.info(f"Fetching Official GLO lottery results for: {draw_date} (Payload: {payload})")
        
        async with httpx.AsyncClient(headers=self.headers, verify=False, timeout=20) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                resp_json = response.json()
                
                if resp_json.get("status") is not True or "response" not in resp_json:
                    raise ValueError(f"API returned failed status or missing response: {resp_json}")
                
                resp_data = resp_json["response"]
                if not resp_data or "result" not in resp_data:
                    raise ValueError(f"No GLO results found for date {draw_date} (response is null)")
                
                result_data = resp_data["result"]
                if not result_data:
                    raise ValueError(f"No GLO results found for date {draw_date} (result is null)")
                
                return self._parse_api_response(result_data, url)
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error fetching GLO lottery for date {draw_date}: {e}")
                raise
            except Exception as e:
                logger.error(f"Error fetching/parsing GLO lottery for date {draw_date}: {e}")
                raise

    async def fetch_latest(self) -> Dict[str, Any]:
        """
        ดึงข้อมูลผลรางวัลหวยรัฐบาลล่าสุด
        """
        url = "https://www.glo.or.th/api/lottery/getLatestLottery"
        logger.info(f"Fetching latest GLO lottery results from Official GLO API")
        
        async with httpx.AsyncClient(headers=self.headers, verify=False, timeout=20) as client:
            try:
                response = await client.post(url)
                response.raise_for_status()
                resp_json = response.json()
                
                if resp_json.get("status") is not True or "response" not in resp_json:
                    raise ValueError(f"API response status was not successful: {resp_json}")
                
                response_data = resp_json["response"]
                if not response_data:
                    raise ValueError("No GLO latest results found (response is null)")
                
                return self._parse_api_response(response_data, url)
                
            except Exception as e:
                logger.error(f"Error fetching latest GLO lottery results: {e}")
                raise

    async def fetch_history_list(self) -> List[str]:
        """
        คำนวณและสแกนหา วันหวยออกย้อนหลัง 5 ปี จาก Official GLO API
        """
        logger.info("Generating and scanning GLO historical draw dates (5 years)...")
        draw_dates = []
        
        current_date = datetime.now()
        start_year = current_date.year - 5
        
        # วนลูปรายปีและรายเดือน
        for year in range(start_year, current_date.year + 1):
            for month in range(1, 13):
                # ในแต่ละเดือน หวยออก 2 ครั้ง (ยกเว้นธันวาคมออก 3 ครั้ง)
                
                # งวดที่ 1 (ต้นเดือน)
                date_g1 = await self._scan_draw_date(year, month, is_first_half=True)
                if date_g1:
                    draw_dates.append(date_g1)
                
                # งวดที่ 2 (กลางเดือน)
                date_g2 = await self._scan_draw_date(year, month, is_first_half=False)
                if date_g2:
                    draw_dates.append(date_g2)
                    
                # งวดพิเศษสิ้นปี (30 ธันวาคม)
                if month == 12:
                    date_g3 = await self._scan_draw_date(year, month, is_first_half=None) # None คือ งวดพิเศษสิ้นปี
                    if date_g3:
                        draw_dates.append(date_g3)
        
        # กรองเอาเฉพาะวันที่ไม่เกินวันนี้
        today_str = date.today().isoformat()
        valid_dates = [d for d in draw_dates if d <= today_str]
        
        logger.info(f"Generated {len(valid_dates)} valid historical draw dates.")
        return valid_dates

    async def _scan_draw_date(self, year: int, month: int, is_first_half: Optional[bool]) -> Optional[str]:
        """
        สแกนหาวันหวยออกจริงในรอบครึ่งแรก หรือ ครึ่งหลัง หรือสิ้นปี ของเดือนนั้นๆ
        """
        # ลำดับความน่าจะเป็นของวันหวยออกในแต่ละรอบ
        if is_first_half is True:
            # งวดต้นเดือน ปกติออกวันที่ 1 -> เลื่อนเป็น 2 -> เลื่อนเป็น 3 -> เลื่อนเป็น 30/31 ของเดือนที่แล้ว
            days_to_try = [1, 2, 3]
            # กรณีเลื่อนวันแรงงาน (1 พ.ค. -> 2 พ.ค.)
            if month == 5:
                days_to_try = [2, 3, 1]
        elif is_first_half is False:
            # งวดกลางเดือน ปกติออกวันที่ 16 -> เลื่อนเป็น 17 (วันครู ม.ค.) -> เลื่อนเป็น 15
            days_to_try = [16, 17, 15]
            if month == 1:
                days_to_try = [17, 16, 15]
        else:
            # งวดสิ้นปี (ธันวาคม) ปกติออกวันที่ 30 -> เลื่อนเป็น 29 -> เลื่อนเป็น 28
            days_to_try = [30, 29, 31, 28]

        url = "https://www.glo.or.th/api/checking/getLotteryResult"
        
        async with httpx.AsyncClient(headers=self.headers, verify=False, timeout=10) as client:
            for day in days_to_try:
                # ตรวจสอบขอบเขตวันที่ของเดือนก่อนหน้า (ในกรณีสแกนหาข้ามเดือนของวันที่ 30, 31)
                # สำหรับความง่ายในการพัฒนา โฟกัสเฉพาะวันหลักๆ ในเดือนนั้นก่อน
                payload = {
                    "date": f"{day:02d}",
                    "month": f"{month:02d}",
                    "year": str(year)
                }
                
                try:
                    response = await client.post(url, json=payload)
                    if response.status_code == 200:
                        resp_json = response.json()
                        resp_data = resp_json.get("response")
                        # ถ้ามีผลรางวัลจริง
                        if resp_data and resp_data.get("result"):
                            draw_date = resp_data["result"].get("date")
                            if draw_date:
                                logger.debug(f"Found drawing date: {draw_date}")
                                return draw_date
                except Exception as e:
                    logger.debug(f"Scan failed for {year}-{month:02d}-{day:02d}: {e}")
                
                # หน่วงสั้นๆ เพื่อไม่ให้กระแทกเซิร์ฟเวอร์
                await asyncio.sleep(0.1)
                
        return None

    def _parse_api_response(self, result_data: Dict[str, Any], source_url: str) -> Dict[str, Any]:
        """
        จัดเรียงและ parse ข้อมูลดิบจาก GLO API
        """
        lottery_data = result_data.get("data", {})
        draw_date = result_data.get("date") # '2026-06-16'
        
        # ดึงเลขรางวัลหลัก
        first_prize = lottery_data.get("first", {}).get("number", [{}])[0].get("value", "")
        last_2 = lottery_data.get("last2", {}).get("number", [{}])[0].get("value", "")
        
        # ดึงเลขรางวัลแบบ list
        first_3 = [n.get("value", "") for n in lottery_data.get("last3f", {}).get("number", [])]
        last_3 = [n.get("value", "") for n in lottery_data.get("last3b", {}).get("number", [])]
        near_first = [n.get("value", "") for n in lottery_data.get("near1", {}).get("number", [])]
        
        # ในบางงวด เลขหน้า 3 ตัว (last3f) หรือ เลขท้าย 3 ตัว (last3b) อาจจะเป็น null/ไม่มีข้อมูล (สำหรับงวดที่เก่ามากๆ)
        # กรองข้อมูลเอาเฉพาะที่เป็นตัวเลข
        first_3 = [x for x in first_3 if x and x.isdigit()]
        last_3 = [x for x in last_3 if x and x.isdigit()]
        near_first = [x for x in near_first if x and x.isdigit()]

        return {
            "lottery_type": "glo",
            "draw_date": draw_date,
            "draw_number": None,
            "numbers": {
                "first_prize": first_prize,
                "last_2": last_2,
                "first_3": first_3,
                "last_3": last_3,
                "near_first": near_first
            },
            "source_url": source_url,
            "fetched_at": datetime.now(timezone.utc)
        }
