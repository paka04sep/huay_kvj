from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseScraper(ABC):
    """
    Abstract Base Class สำหรับ Scraper ทุกตัวของระบบหวย
    """
    
    def __init__(self, lottery_type: str):
        self.lottery_type = lottery_type

    @abstractmethod
    async def fetch(self, draw_date: str) -> Dict[str, Any]:
        """
        ดึงข้อมูลผลรางวัลของประเภทหวยตามวันที่ระบุ
        
        Args:
            draw_date (str): วันที่ออกรางวัลในฟอร์แมต YYYY-MM-DD
            
        Returns:
            Dict[str, Any]: ข้อมูลดิบที่ดึงมาจากแหล่งข้อมูล
        """
        pass

    @abstractmethod
    async def fetch_latest(self) -> Dict[str, Any]:
        """
        ดึงข้อมูลผลรางวัลล่าสุด
        
        Returns:
            Dict[str, Any]: ข้อมูลดิบที่ดึงมาจากแหล่งข้อมูล
        """
        pass
