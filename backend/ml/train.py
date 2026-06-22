import os
import sys
import argparse
import asyncio
import torch
import torch.nn as nn
import numpy as np

# เพิ่ม PYTHONPATH ให้หาโมดูลหลักเจอ
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.ml.dataset import load_historical_sequences, create_sequences
from backend.ml.lstm_model import LottoLSTM

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "models"))
os.makedirs(MODELS_DIR, exist_ok=True)

async def train_model(code: str, target: str = "last_2", window_size: int = 12, epochs: int = 80, batch_size: int = 16):
    """
    ฟังก์ชันสำหรับเทรนโมเดล LSTM สำหรับหวยและตำแหน่งที่ต้องการ
    """
    print(f"\n--- Starting Training for {code.upper()} ({target}) ---")
    
    # 1. โหลดข้อมูลจาก DB
    raw_data = await load_historical_sequences(code, target)
    
    if len(raw_data) <= window_size + 5:
        print(f"Warning: Not enough active data to train {code.upper()} {target}. Got {len(raw_data)} draws, need > {window_size + 5}.")
        return False

    num_classes = 100 if target == "last_2" else 1000
    
    # 2. เตรียม Sequence
    X_np, y_np = create_sequences(raw_data, window_size=window_size)
    if X_np.size == 0:
        print(f"Error creating sequences for {code.upper()} {target}.")
        return False
        
    # Scale ข้อมูล Input (หารด้วยจำนวนคลาสเพื่อให้สเกลอยู่ในช่วง [0, 1])
    X_normalized = X_np / num_classes
    
    # แปลงเป็น PyTorch Tensors
    X_tensor = torch.tensor(X_normalized, dtype=torch.float32).unsqueeze(-1) # Shape: (batch, seq_len, 1)
    y_tensor = torch.tensor(y_np, dtype=torch.long) # Shape: (batch) -> ใช้ Long สำหรับ CrossEntropyLoss
    
    # 3. สร้างโมเดล
    model = LottoLSTM(num_classes=num_classes)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    
    # 4. ลูปการฝึกฝน
    dataset_size = X_tensor.size(0)
    print(f"Training on {dataset_size} sequences...")
    
    model.train()
    for epoch in range(epochs):
        # สุ่มลำดับการเรียนรู้ต่อ Batch แบบง่าย
        permutation = torch.randperm(dataset_size)
        epoch_loss = 0.0
        
        for i in range(0, dataset_size, batch_size):
            indices = permutation[i : i + batch_size]
            batch_x, batch_y = X_tensor[indices], y_tensor[indices]
            
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item() * batch_x.size(0)
            
        epoch_loss /= dataset_size
        if (epoch + 1) % 20 == 0 or epoch == 0:
            print(f"Epoch {epoch+1:02d}/{epochs:02d} - Loss: {epoch_loss:.4f}")
            
    # 5. บันทึก Model Weights
    model_name = f"{code}_{target}_lstm.pth"
    model_path = os.path.join(MODELS_DIR, model_name)
    torch.save(model.state_dict(), model_path)
    print(f"Saved model to {model_path}")
    return True

async def main():
    parser = argparse.ArgumentParser(description="Train LSTM models for lottery prediction.")
    parser.add_argument("--type", choices=["glo", "lao"], default="glo", help="Lottery type to train (glo or lao)")
    parser.add_argument("--target", choices=["last_2", "last_3", "all"], default="all", help="Target output (last_2, last_3, or all)")
    parser.add_argument("--epochs", type=int, default=80, help="Number of training epochs")
    
    # ดักกรณีกรันด้วย pytest (ไม่ต้องการ parse argv)
    if "pytest" in sys.modules or any("test" in arg for arg in sys.argv):
        # รันค่าดีฟอลต์สำหรับเทส
        args = parser.parse_args([])
    else:
        args = parser.parse_args()
    
    targets = ["last_2", "last_3"] if args.target == "all" else [args.target]
    
    for t in targets:
        await train_model(code=args.type, target=t, epochs=args.epochs)

if __name__ == "__main__":
    asyncio.run(main())
