## Phase 1 — รากฐาน

เริ่มจากข้อมูลก่อนทุกอย่าง ถ้าไม่มีข้อมูล ML ก็ทำอะไรไม่ได้เลย

- ขั้นที่ 1: ตั้ง project structure + database

สร้าง repo, โฟลเดอร์ตามโครงสร้าง
ติดตั้ง PostgreSQL + สร้าง schema (lottery_types, lottery_results)
ติดตั้ง Redis สำหรับ cache

- ขั้นที่ 2: เขียน scraper ตัวแรก (สลากรัฐบาลก่อน)

เลือกสลากรัฐบาลเพราะข้อมูลสะอาดที่สุด ออก 2 ครั้ง/เดือน ง่ายสุด
เขียน scraper → validator → normalizer → insert DB
ทดสอบดึงข้อมูลย้อนหลัง 5 ปี

- ขั้นที่ 3: ขยาย scraper ให้ครบ

เพิ่มหวยลาว → ฮานอย → ยี่กี ทีละตัว
ตั้ง Cron Job ให้ทำงานอัตโนมัติ

## Phase 2 — Backend API

- ขั้นที่ 4: สร้าง FastAPI

endpoint /results — ดึงผลล่าสุด
endpoint /history — ดึงย้อนหลัง filter ตามประเภท/วันที่
endpoint /stats — สถิติเลขร้อน/เย็น

ยังไม่ต้องมี prediction ตอนนี้ แค่ให้ frontend เรียกได้ก่อน

## Phase 3 — ML Engine

ทำหลัง data สะสมมาพอแล้ว

- ขั้นที่ 5: Frequency Analysis ก่อน (ง่ายสุด)

นับความถี่เลขแต่ละตัว, คำนวณ hot/cold numbers
เพิ่ม endpoint /predictions ที่ return ผลจาก frequency

- ขั้นที่ 6: เพิ่ม LSTM Model

train บน historical data
รวม output เข้ากับ frequency analysis (ensemble)

## Phase 4 — Frontend

- ขั้นที่ 7: สร้าง UI

Dashboard แสดงผลล่าสุด + countdown งวดถัดไป
หน้า Statistics กราฟ hot/cold
หน้า Prediction แสดงผลทำนาย

- ขั้นที่ 8: Deploy

Backend → Railway / Render
Frontend → Vercel
DB → Supabase
