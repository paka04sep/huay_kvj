import torch
import torch.nn as nn

class LottoLSTM(nn.Module):
    """
    โมเดล LSTM สำหรับทำนายตัวเลขหวย โดยจำลองเป็นโจทย์ Classification
    ทำนายผลลัพธ์เป็นเวกเตอร์ความน่าจะเป็นของแต่ละคลาส (เช่น 100 คลาส สำหรับเลขท้าย 2 ตัว 00-99)
    """
    def __init__(self, input_size: int = 1, hidden_size: int = 128, num_layers: int = 2, num_classes: int = 100):
        super(LottoLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM Layer
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2 if num_layers > 1 else 0.0
        )
        
        # Fully Connected Layer สำหรับทำนายความน่าจะเป็นของแต่ละคลาส
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        # x: (batch_size, sequence_length, input_size)
        out, _ = self.lstm(x)
        
        # ดึงผลลัพธ์จาก Time step สุดท้าย
        # out[:, -1, :]: (batch_size, hidden_size)
        out = self.fc(out[:, -1, :])
        return out
