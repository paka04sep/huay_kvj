# (Huay KVJ Deployment Guide)

## ภาพรวมสถาปัตยกรรมระบบ (System Architecture)

ระบบแบ่งออกเป็น 4 ส่วนหลัก โดยทั้งหมดใช้งานใน **แพ็กเกจฟรี (Free Tier)**:

```
[ Frontend: Next.js ] (Vercel)
         │
         ▼ (API Request / Rewrite)
[ Backend: FastAPI + APScheduler ] (Railway - 1 Service)
         │
         ├─► [ Database: PostgreSQL ] (Supabase Cloud)
         └─► [ Cache: Serverless Redis ] (Upstash Redis)
```

---

## รายละเอียดการ Deploy แต่ละส่วน

### 1. Database (Supabase)

- **สถานะ**: ทำงานอยู่บน Cloud ของ Supabase อยู่
- **การเชื่อมต่อใน Production**: ให้ใช้ **Connection Pooler (พอร์ต 6543 - Transaction Mode)** เพื่อประหยัด Connection และเข้ากันได้กับระบบ IPv4
- **รูปแบบ URL**:
  `postgresql+asyncpg://postgres.vcmiglzjvckjjyiivwys:[PASSWORD]@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres`

### 2. Cache / Queue (Upstash Redis)

- **ผู้ให้บริการ**: [Upstash](https://upstash.com/) (สมัครใช้บริการ Redis ฟรีตลอดชีพ จำกัด 10,000 requests/วัน)
- **การเชื่อมต่อ**: เลือกเชื่อมต่อแบบ **Redis Client** (ไม่ใช่แบบ HTTPS/REST)
- **รูปแบบ URL**:
  `redis://default:[PASSWORD]@xxxx.upstash.io:6379`

### 3. Backend API & Scheduler (Railway)

- **โฟลเดอร์ใน Repo**: `/backend`
- **จำนวน Service ที่รัน**: **1 Service** (รันทั้ง API และบอท Scheduler ใน Container เดียวกันเพื่อประหยัดแรมและเครดิตฟรี)
- **ขั้นตอนการตั้งค่าบน Railway**:
  1. สร้าง Service ใหม่จาก GitHub Repo เดียวกัน
  2. ตั้งค่า **Settings** -> **Root Directory** = `/backend`
  3. ตั้งค่า **Settings** -> **Start Command** =
     `sh -c "uvicorn backend.api.main:app --host 0.0.0.0 --port \$PORT"`
  4. เพิ่ม **Variables** ระบบ:
     - `DATABASE_URL` (ใช้ลิงก์ Pooler ข้อ 1)
     - `REDIS_URL` (ใช้ลิงก์ Upstash ข้อ 2)
  5. กด **Generate Domain** ในหน้า Settings เพื่อรับลิงก์ API จริง (เช่น `https://huay-backend.up.railway.app`)

### 4. Frontend (Vercel)

- **โฟลเดอร์ใน Repo**: `/` (โฟลเดอร์นอกสุดของโปรเจกต์)
- **ผู้ให้บริการ**: [Vercel](https://vercel.com/) (ฟรีตลอดชีพ เชื่อมต่ออัตโนมัติจาก GitHub)
- **ขั้นตอนการตั้งค่าบน Vercel**:
  1. สร้าง Project ใหม่ เชื่อมกับ GitHub Repo ของคุณ
  2. เพิ่ม **Environment Variables**:
     - `BACKEND_API_URL` = ลิงก์ URL ของหลังบ้านที่ได้จาก Railway (เช่น `https://huay-backend.up.railway.app`)
  3. กด **Deploy**

---

## การรันระบบภายในเครื่องตัวเอง (Local Development)

1.  **หลังบ้าน (Docker Compose)**:
    เปิดเครื่องคอมหลักของคุณและรันคำสั่งด้านล่างนี้ ระบบจะเปิดรัน Redis จำลอง และ Backend (FastAPI + Scheduler) ทันที:
    ```bash
    docker compose up --build
    ```
2.  **หน้าบ้าน (Local Node)**:
    เปิดรันหน้าเว็บในเครื่องหลักเชื่อมหา Docker หลังบ้าน:
    ```bash
    npm install
    npm run dev
    ```
    เปิดดูผลลัพธ์ผ่าน [http://localhost:3000](http://localhost:3000)
