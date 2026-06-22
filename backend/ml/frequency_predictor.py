from collections import Counter
from typing import List, Dict, Any

class FrequencyPredictor:
    """
    ทำนายผลลัพธ์โดยอ้างอิงความถี่จากสถิติประวัติการออกรางวัล (Hot Numbers)
    """
    
    def predict(self, data: List[int], target: str = "last_2", top_k: int = 5) -> List[Dict[str, Any]]:
        """
        วิเคราะห์ข้อมูลย้อนหลัง และแนะนำตัวเลขที่ความถี่สูงสุด top_k ตัวแรก
        data: ลิสต์ของตัวเลขประวัติการออกรางวัล
        """
        if not data:
            return []
            
        # เลือกข้อมูลล่าสุดไม่เกิน 100 งวดเพื่อความสดใหม่ของสถิติ
        recent_data = data[-100:]
        total_samples = len(recent_data)
        
        # นับความถี่
        counts = Counter(recent_data)
        
        # จัดฟอร์แมตความยาวตัวเลขเป้าหมาย
        fmt_len = 2 if target == "last_2" else 3
        
        predictions = []
        # เรียงลำดับความถี่สูงสุด
        for num, count in counts.most_common(top_k):
            prob = count / total_samples if total_samples > 0 else 0.0
            num_str = f"{num:0{fmt_len}d}"
            predictions.append({
                "number": num_str,
                "probability": float(prob),
                "count": count
            })
            
        # กรณีข้อมูลมีน้อยกว่าคีย์ที่ต้องการแนะนำ ให้แนะนำเลขเฉลี่ยเพิ่ม
        if len(predictions) < top_k:
            all_possible = set(range(100 if target == "last_2" else 1000))
            existing = set(counts.keys())
            remaining = list(all_possible - existing)[: top_k - len(predictions)]
            for r in remaining:
                num_str = f"{r:0{fmt_len}d}"
                predictions.append({
                    "number": num_str,
                    "probability": 0.0,
                    "count": 0
                })
                
        return predictions
