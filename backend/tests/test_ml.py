import pytest
import torch
import numpy as np

from backend.ml.lstm_model import LottoLSTM
from backend.ml.dataset import create_sequences
from backend.ml.frequency_predictor import FrequencyPredictor

def test_lstm_model_instantiation():
    """
    ทดสอบการสร้างโมเดล LSTM และรันมิติอินพุต (Forward pass shapes)
    """
    model = LottoLSTM(num_classes=100)
    # Batch=4, Seq_len=12, Input_size=1
    dummy_input = torch.randn(4, 12, 1)
    output = model(dummy_input)
    assert output.shape == (4, 100)

def test_create_sequences():
    """
    ทดสอบการสร้างลำดับข้อมูลตามขนาด Window
    """
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    X, y = create_sequences(data, window_size=5)
    
    # 10 - 5 = 5 ตัวอย่าง
    assert X.shape == (5, 5)
    assert y.shape == (5,)
    # ตรวจความถูกต้องของค่า
    # ตัวอย่างแรก: [1,2,3,4,5] -> target: 6
    np.testing.assert_array_equal(X[0], [1, 2, 3, 4, 5])
    assert y[0] == 6

def test_frequency_predictor():
    """
    ทดสอบสถิติความถี่และการแนะนำเลข Hot Numbers
    """
    predictor = FrequencyPredictor()
    # ส่งตัวเลขประวัติการออกรางวัล (เลข 56 ออกมากสุด)
    data = [10, 20, 56, 56, 56, 30, 40, 56, 56, 99]
    preds = predictor.predict(data, target="last_2", top_k=3)
    
    assert len(preds) == 3
    # อันดับแรกต้องเป็นเลข "56"
    assert preds[0]["number"] == "56"
    assert preds[0]["count"] == 5
    assert preds[0]["probability"] == 0.5 # 5 ใน 10
