import httpx
import logging
import asyncio
import json
import re
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from backend.data_collection.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

THAI_MONTHS = {
    "มกราคม": 1, "กุมภาพันธ์": 2, "มีนาคม": 3, "เมษายน": 4,
    "พฤษภาคม": 5, "มิถุนายน": 6, "กรกฎาคม": 7, "สิงหาคม": 8,
    "กันยายน": 9, "ตุลาคม": 10, "พฤศจิกายน": 11, "ธันวาคม": 12,
    "ม.ค.": 1, "ก.พ.": 2, "มี.ค.": 3, "เม.ย.": 4,
    "พ.ค.": 5, "มิ.ย.": 6, "ก.ค.": 7, "ส.ค.": 8,
    "ก.ย.": 9, "ต.ค.": 10, "พ.ย.": 11, "ธ.ค.": 12
}

class LaoScraper(BaseScraper):
    """
    Scraper สำหรับหวยลาว (หวยพัฒนา)
    ดึงข้อมูลจาก Sanook (www.sanook.com/news/laolotto)
    """

    def __init__(self):
        super().__init__(lottery_type="lao")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def _parse_thai_date(self, text: str) -> Optional[str]:
        """
        แปลงวันที่ภาษาไทย (เช่น '19 มิถุนายน 2569') เป็น ISO format 'YYYY-MM-DD'
        """
        words = text.replace("งวด", "").replace("วัน", "").replace("ประจำ", "").replace("จันทร์", "").replace("อังคาร", "").replace("พุธ", "").replace("พฤหัสบดี", "").replace("ศุกร์", "").replace("เสาร์", "").replace("อาทิตย์", "").split()
        
        day = None
        month = None
        year = None
        
        for i, word in enumerate(words):
            word_clean = word.strip()
            if word_clean.isdigit() and len(word_clean) <= 2:
                day = int(word_clean)
            elif word_clean in THAI_MONTHS:
                month = THAI_MONTHS[word_clean]
                if i > 0 and words[i-1].strip().isdigit():
                    day = int(words[i-1].strip())
                if i < len(words) - 1 and words[i+1].strip().isdigit():
                    year = int(words[i+1].strip()) - 543
            elif word_clean.isdigit() and len(word_clean) == 4:
                year = int(word_clean) - 543
                
        if day and month and year:
            return f"{year:04d}-{month:02d}-{day:02d}"
        return None

    def _extract_next_data(self, html: str) -> Optional[Dict[str, Any]]:
        """
        ดึงข้อมูล NEXT_DATA JSON จาก HTML
        """
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", id="__NEXT_DATA__")
        if script and script.string:
            try:
                return json.loads(script.string)
            except Exception as e:
                logger.error(f"Failed to parse NEXT_DATA JSON: {e}")
        return None

    def _extract_lao_from_cache(self, next_data: Dict[str, Any], target_date_slug: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        สกัดผลรางวัลหวยลาวจาก Apollo cache โดยเชื่อมโยง Date และ Result ใน Node เดียวกัน
        """
        try:
            apollo_data = next_data["props"]["serverState"]["apollo"]["data"]
            
            # 1. ค้นหา node ทั้งหมดที่เป็นประเภท LaoLotto
            lotto_nodes = []
            for k, v in apollo_data.items():
                if isinstance(v, dict) and v.get("__typename") == "LaoLotto":
                    lotto_nodes.append(v)
            
            # 2. วนลูปและเชื่อมโยงผลรางวัล
            valid_results = []
            for node in lotto_nodes:
                date_slug = node.get("dateSlug")
                prize_ref = node.get("prizeResult")
                
                # หากระบุเป้าหมาย และ date_slug ไม่ตรง ก็ข้าม
                if target_date_slug and date_slug != target_date_slug:
                    continue
                    
                if date_slug and len(date_slug) == 8 and prize_ref:
                    ref_id = prize_ref.get("__ref") or prize_ref.get("id")
                    if ref_id and ref_id in apollo_data:
                        prize_obj = apollo_data[ref_id]
                        digits_4 = prize_obj.get("last4Prize")
                        
                        # กรองข้อมูลที่มีผลรางวัลแล้วจริง
                        if digits_4 and digits_4.isdigit() and digits_4 != "รอผล":
                            day = int(date_slug[:2])
                            month = int(date_slug[2:4])
                            year = int(date_slug[4:]) - 543
                            draw_date = f"{year:04d}-{month:02d}-{day:02d}"
                            
                            valid_results.append({
                                "draw_date": draw_date,
                                "digits_4": digits_4,
                                "date_slug": date_slug
                            })
                            
            if valid_results:
                # เรียงลำดับตามความใหม่ และคืนค่ารางวัลล่าสุด
                valid_results.sort(key=lambda x: x["draw_date"], reverse=True)
                return valid_results[0]
                
        except Exception as e:
            logger.error(f"Error extracting Lao lotto from cache: {e}")
        return None

    async def _fetch_latest_mthai(self) -> Optional[Dict[str, Any]]:
        """
        ดึงผลหวยลาวงวดล่าสุดจาก MThai
        """
        url = "https://lotto.mthai.com/lao"
        logger.info(f"Trying to fetch latest Lao lottery from MThai: {url}")
        
        async with httpx.AsyncClient(headers=self.headers, verify=False, timeout=10) as client:
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return None
                
                html = resp.content.decode('utf-8', errors='replace')
                soup = BeautifulSoup(html, 'html.parser')
                articles = soup.find_all('article')
                
                for article in articles[:5]:
                    title_tag = article.find('h2') or article.find('h3') or article.find('a')
                    title_text = title_tag.text.strip() if title_tag else ""
                    
                    if "หวยลาว" not in title_text:
                        continue
                        
                    draw_date = self._parse_thai_date(title_text)
                    if not draw_date:
                        continue
                        
                    content_text = article.text
                    match_6d = re.search(r"เลข\s*6\s*ตัว\s*(\d{6})", content_text)
                    match_5d = re.search(r"เลข\s*5\s*ตัว\s*(\d{5})", content_text)
                    match_4d = re.search(r"เลข\s*4\s*ตัว\s*(\d{4})", content_text)
                    
                    digits_4 = None
                    if match_4d:
                        digits_4 = match_4d.group(1)
                    elif match_5d:
                        digits_4 = match_5d.group(1)[-4:]
                    elif match_6d:
                        digits_4 = match_6d.group(1)[-4:]
                        
                    if not digits_4:
                        nums = re.findall(r"\d{4,6}", content_text)
                        for n in nums:
                            if len(n) == 6:
                                digits_4 = n[-4:]
                                break
                            elif len(n) == 4:
                                digits_4 = n
                                break
                                
                    if digits_4:
                        detail_url = title_tag.get('href') if title_tag and title_tag.name == 'a' else url
                        return {
                            "lottery_type": "lao",
                            "draw_date": draw_date,
                            "draw_number": None,
                            "numbers": {
                                "digits_4": digits_4
                            },
                            "source_url": detail_url,
                            "fetched_at": datetime.now(timezone.utc)
                        }
            except Exception as e:
                logger.error(f"Error fetching from MThai: {e}")
        return None

    async def _fetch_date_mthai(self, draw_date: str) -> Optional[Dict[str, Any]]:
        """
        ดึงผลหวยลาวตามวันที่จากหน้าแรก MThai (หากยังไม่ตกรอบหน้าแรก)
        """
        url = "https://lotto.mthai.com/lao"
        logger.info(f"Searching for Lao lottery date {draw_date} on MThai: {url}")
        
        async with httpx.AsyncClient(headers=self.headers, verify=False, timeout=10) as client:
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return None
                
                html = resp.content.decode('utf-8', errors='replace')
                soup = BeautifulSoup(html, 'html.parser')
                articles = soup.find_all('article')
                
                for article in articles[:10]:
                    title_tag = article.find('h2') or article.find('h3') or article.find('a')
                    title_text = title_tag.text.strip() if title_tag else ""
                    
                    if "หวยลาว" not in title_text:
                        continue
                        
                    candidate_date = self._parse_thai_date(title_text)
                    if candidate_date != draw_date:
                        continue
                        
                    content_text = article.text
                    match_6d = re.search(r"เลข\s*6\s*ตัว\s*(\d{6})", content_text)
                    match_5d = re.search(r"เลข\s*5\s*ตัว\s*(\d{5})", content_text)
                    match_4d = re.search(r"เลข\s*4\s*ตัว\s*(\d{4})", content_text)
                    
                    digits_4 = None
                    if match_4d:
                        digits_4 = match_4d.group(1)
                    elif match_5d:
                        digits_4 = match_5d.group(1)[-4:]
                    elif match_6d:
                        digits_4 = match_6d.group(1)[-4:]
                        
                    if not digits_4:
                        nums = re.findall(r"\d{4,6}", content_text)
                        for n in nums:
                            if len(n) == 6:
                                digits_4 = n[-4:]
                                break
                            elif len(n) == 4:
                                digits_4 = n
                                break
                                
                    if digits_4:
                        detail_url = title_tag.get('href') if title_tag and title_tag.name == 'a' else url
                        return {
                            "lottery_type": "lao",
                            "draw_date": draw_date,
                            "draw_number": None,
                            "numbers": {
                                "digits_4": digits_4
                            },
                            "source_url": detail_url,
                            "fetched_at": datetime.now(timezone.utc)
                        }
            except Exception as e:
                logger.error(f"Error searching date {draw_date} on MThai: {e}")
        return None

    async def _fetch_sanook(self, draw_date: str) -> Dict[str, Any]:
        """
        ดึงข้อมูลผลหวยลาวจาก Sanook ตามวันที่เจาะจง (ฟังก์ชันเดิมที่ดึงผ่าน URL date_slug)
        """
        date_obj = datetime.strptime(draw_date, "%Y-%m-%d")
        thai_year = date_obj.year + 543
        date_slug = f"{date_obj.day:02d}{date_obj.month:02d}{thai_year}"
        
        url = f"https://www.sanook.com/news/laolotto/{date_slug}/"
        logger.info(f"Fetching Lao lottery results from Sanook: {url}")
        
        async with httpx.AsyncClient(headers=self.headers, verify=False, timeout=15) as client:
            response = await client.get(url)
            if response.status_code == 404:
                raise ValueError(f"Lao lottery result for date {draw_date} not found on Sanook (404)")
            response.raise_for_status()
            
            next_data = self._extract_next_data(response.text)
            if not next_data:
                raise ValueError("Could not extract NEXT_DATA from Sanook page")
                
            lotto_info = self._extract_lao_from_cache(next_data, target_date_slug=date_slug)
            if not lotto_info:
                raise ValueError(f"Could not extract Lao lottery result from NEXT_DATA for {draw_date}")
                
            return {
                "lottery_type": "lao",
                "draw_date": draw_date,
                "draw_number": None,
                "numbers": {
                    "digits_4": lotto_info["digits_4"]
                },
                "source_url": url,
                "fetched_at": datetime.now(timezone.utc)
            }

    async def _fetch_latest_sanook(self) -> Dict[str, Any]:
        """
        ดึงข้อมูลผลหวยลาวงวดล่าสุดจาก Sanook (ฟังก์ชันเดิม)
        """
        url = "https://www.sanook.com/news/laolotto/"
        logger.info(f"Fetching latest Lao lottery results from Sanook: {url}")
        
        async with httpx.AsyncClient(headers=self.headers, verify=False, timeout=15) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            next_data = self._extract_next_data(response.text)
            if not next_data:
                raise ValueError("Could not extract NEXT_DATA from Sanook page")
                
            lotto_info = self._extract_lao_from_cache(next_data)
            if not lotto_info:
                raise ValueError("Could not extract latest Lao lottery result from NEXT_DATA")
                
            return {
                "lottery_type": "lao",
                "draw_date": lotto_info["draw_date"],
                "draw_number": None,
                "numbers": {
                    "digits_4": lotto_info["digits_4"]
                },
                "source_url": url,
                "fetched_at": datetime.now(timezone.utc)
            }

    async def fetch(self, draw_date: str) -> Dict[str, Any]:
        """
        ดึงข้อมูลตามวันที่ (ดึงจาก Sanook เท่านั้น)
        """
        return await self._fetch_sanook(draw_date)

    async def fetch_latest(self) -> Dict[str, Any]:
        """
        ดึงข้อมูลผลหวยลาวงวดล่าสุด (ดึงจาก Sanook เท่านั้น)
        """
        return await self._fetch_latest_sanook()

    async def fetch_history_list(self) -> List[str]:
        """
        ดึงรายการ draw_date (YYYY-MM-DD) ทั้งหมดย้อนหลัง 5 ปีจาก Sanook
        โดยสร้างวัน จันทร์, พุธ, ศุกร์ ทั้งหมดและตรวจสอบว่ามีหน้านั้นอยู่จริงบน Sanook
        """
        logger.info("Generating and validating historical Lao draw dates (last 5 years)...")
        from datetime import timedelta
        
        # 1. สร้างวันจันทร์ พุธ ศุกร์ ย้อนหลัง 5 ปี
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5*365)
        
        candidates = []
        curr = start_date
        while curr <= end_date:
            if curr.weekday() in (0, 2, 4): # Mon, Wed, Fri
                candidates.append(curr.strftime("%Y-%m-%d"))
            curr += timedelta(days=1)
            
        logger.info(f"Generated {len(candidates)} candidate dates. Verifying against Sanook...")
        
        valid_dates = []
        
        async def check_date(client: httpx.AsyncClient, date_str: str, sem: asyncio.Semaphore):
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            thai_year = date_obj.year + 543
            date_slug = f"{date_obj.day:02d}{date_obj.month:02d}{thai_year}"
            url = f"https://www.sanook.com/news/laolotto/{date_slug}/"
            
            async with sem:
                try:
                    resp = await client.head(url, timeout=5)
                    if resp.status_code == 200:
                        return date_str
                except Exception:
                    pass
            return None

        # จำกัด Concurrency ป้องกันการโดนบล็อก
        sem = asyncio.Semaphore(15)
        
        limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
        async with httpx.AsyncClient(headers=self.headers, verify=False, limits=limits) as client:
            tasks = [check_date(client, d, sem) for d in candidates]
            results = await asyncio.gather(*tasks)
            
        valid_dates = sorted([r for r in results if r])
        logger.info(f"Total valid historical Lao draw dates verified: {len(valid_dates)}")
        return valid_dates
