import os
import sys
import torch
import numpy as np
from typing import List, Dict, Any

# เพิ่ม PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.ml.dataset import load_historical_sequences
from backend.ml.lstm_model import LottoLSTM
from backend.ml.frequency_predictor import FrequencyPredictor

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "models"))

class EnsemblePredictor:
    """
    ประสานการทำงานระหว่าง LSTM Model และ Frequency Predictor (สถิติความถี่สะสม)
    """
    def __init__(self, weight_lstm: float = 0.6, weight_freq: float = 0.4):
        self.weight_lstm = weight_lstm
        self.weight_freq = weight_freq
        self.freq_predictor = FrequencyPredictor()

    async def predict_next(self, code: str, target: str = "last_2", window_size: int = 12, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        ทำนายเลขในงวดถัดไป โดยส่งเลขแนะนำที่ดีที่สุดเรียงลำดับความน่าจะเป็นจากมากไปน้อย
        """
        # 1. โหลดข้อมูลประวัติรางวัล
        raw_data = await load_historical_sequences(code, target)
        if len(raw_data) < window_size:
            raise ValueError(f"Insufficient historical data for {code.upper()}. Need at least {window_size} draws.")

        num_classes = 100 if target == "last_2" else 1000
        fmt_len = 2 if target == "last_2" else 3

        # --- ส่วนที่ 1: การทำนายด้วย Frequency Predictor ---
        # ดึงความถี่แบบกระจายตัวของคลาสทั้งหมดในประวัติ
        freq_results = self.freq_predictor.predict(raw_data, target=target, top_k=num_classes)
        freq_probs = {item["number"]: item["probability"] for item in freq_results}

        # --- ส่วนที่ 2: การทำนายด้วย LSTM ---
        # เตรียม input ล่าสุด ขนาดเท่ากับ window_size
        latest_sequence = np.array(raw_data[-window_size:], dtype=np.float32)
        # Normalize scale [0, 1]
        latest_seq_normalized = latest_sequence / num_classes
        
        # แปลงเป็น PyTorch Tensor รูปแบบ (batch=1, seq_len=window_size, input_size=1)
        input_tensor = torch.tensor(latest_seq_normalized, dtype=torch.float32).unsqueeze(0).unsqueeze(-1)

        # โหลดโมเดล LSTM
        model_name = f"{code}_{target}_lstm.pth"
        model_path = os.path.join(MODELS_DIR, model_name)
        
        lstm_probs = {}
        if os.path.exists(model_path):
            try:
                model = LottoLSTM(num_classes=num_classes)
                model.load_state_dict(torch.load(model_path, map_location=torch.device("cpu")))
                model.eval()
                
                with torch.no_grad():
                    logits = model(input_tensor)
                    probabilities = torch.softmax(logits, dim=1).squeeze(0).numpy()
                    
                for i, prob in enumerate(probabilities):
                    num_str = f"{i:0{fmt_len}d}"
                    lstm_probs[num_str] = float(prob)
            except Exception as e:
                print(f"Error loading/evaluating LSTM model: {e}. Falling back to frequency only.")
                # หากดึงโมเดลล้มเหลว ให้ใช้น้ำหนัก Frequency = 1.0
                self.weight_freq = 1.0
                self.weight_lstm = 0.0
        else:
            print(f"Model file {model_path} not found. Using frequency predictor only.")
            self.weight_freq = 1.0
            self.weight_lstm = 0.0

        # --- ส่วนที่ 3: การรวบรวมแบบ Ensemble (Weighted Average) ---
        ensemble_scores = []
        for i in range(num_classes):
            num_str = f"{i:0{fmt_len}d}"
            
            p_lstm = lstm_probs.get(num_str, 1.0 / num_classes)
            p_freq = freq_probs.get(num_str, 0.0)
            
            p_ensemble = (self.weight_lstm * p_lstm) + (self.weight_freq * p_freq)
            
            ensemble_scores.append({
                "number": num_str,
                "probability": float(p_ensemble),
                "lstm_prob": float(p_lstm) if self.weight_lstm > 0 else 0.0,
                "freq_prob": float(p_freq)
            })

        # เรียงลำดับจากสูงไปต่ำ และเลือกตัวเลขเด่นสุด top_k ชุด
        ensemble_scores.sort(key=lambda x: x["probability"], reverse=True)
        return ensemble_scores[:top_k]
