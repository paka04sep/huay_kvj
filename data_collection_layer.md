# Data Collection Layer — เอกสารฉบับสมบูรณ์

## ภาพรวม

Data Collection Layer คือชั้นแรกของระบบที่ทำหน้าที่ **ดึงข้อมูลผลหวยจากทุกแหล่ง → ตรวจสอบ → จัดรูปแบบ → บันทึกลงฐานข้อมูล** โดยทำงานอัตโนมัติผ่าน Scheduler ไม่ต้องมีคนดูแล

---

## 1. ประเภทหวยและวิธีดึงข้อมูล

### 1.1 สลากกินแบ่งรัฐบาล

| รายละเอียด | ข้อมูล |
|---|---|
| ออกทุก | วันที่ 1 และ 16 ของทุกเดือน |
| เลขที่เก็บ | รางวัลที่ 1, เลขหน้า 3 ตัว, เลขท้าย 3 ตัว, เลขท้าย 2 ตัว, รางวัลข้างเคียง |
| วิธีดึง | HTTP GET จาก `www.glo.or.th` หรือ API สำเร็จรูป |
| เวลาออกผล | ประมาณ 15:00 น. |

```python
import httpx
from bs4 import BeautifulSoup

async def fetch_glo_result(draw_date: str) -> dict:
    url = f"https://www.glo.or.th/result/lottery/{draw_date}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10)
    soup = BeautifulSoup(resp.text, "html.parser")
    return {
        "type": "glo",
        "draw_date": draw_date,
        "first_prize": soup.select_one(".first-prize").text.strip(),
        "last_3": [el.text.strip() for el in soup.select(".last-3")],
        "last_2": soup.select_one(".last-2").text.strip(),
    }
```

---

### 1.2 หวยลาว

| รายละเอียด | ข้อมูล |
|---|---|
| ออกทุก | จันทร์–ศุกร์ |
| เลขที่เก็บ | 4 ตัว (ผลรวม), 3 ตัว, 2 ตัว |
| วิธีดึง | Scraping เว็บ `lotto.vip` / `laolottery.com` |
| เวลาออกผล | ประมาณ 20:30 น. (เวลาลาว) |

```python
async def fetch_lao_result(draw_date: str) -> dict:
    url = f"https://www.laolottery.com/result/{draw_date}"
    async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"}) as client:
        resp = await client.get(url, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")
    return {
        "type": "lao",
        "draw_date": draw_date,
        "4_digits": soup.select_one(".result-4d").text.strip(),
        "3_digits": soup.select_one(".result-3d").text.strip(),
        "2_digits": soup.select_one(".result-2d").text.strip(),
    }
```

---

### 1.3 หวยฮานอย / หวยฮานอยพิเศษ

| รายละเอียด | ข้อมูล |
|---|---|
| ออกทุก | ทุกวัน (ปกติ) / วันพิเศษตามประกาศ |
| เลขที่เก็บ | 4 ตัว, 3 ตัว, 2 ตัว |
| วิธีดึง | Scraping เว็บฮานอย หรือ API บุคคลที่สาม |

---

### 1.4 หวยยี่กี

| รายละเอียด | ข้อมูล |
|---|---|
| ออกทุก | 88 รอบ/วัน (ทุก 15 นาที) |
| เลขที่เก็บ | 3 ตัวบน, 2 ตัวล่าง |
| วิธีดึง | API บุคคลที่สาม หรือ Huay.com |
| หมายเหตุ | ต้องใช้ Rate Limiting เพื่อไม่ให้ request ถี่เกินไป |

---

### 1.5 หวยใต้ดิน (กลางวัน / บ่าย / เย็น)

| รายละเอียด | ข้อมูล |
|---|---|
| ออกทุก | 3 รอบ/วัน |
| เลขที่เก็บ | 3 ตัวบน, 2 ตัวล่าง (อิงจากสลากรัฐบาล / หวยลาว) |
| วิธีดึง | Manual Input หรือ Scraping เว็บเดิมพัน |

---

## 2. โครงสร้าง Data Collection Layer

```
data-collection/
├── schedulers/
│   ├── glo_scheduler.py        # cron: 0 15 1,16 * *
│   ├── lao_scheduler.py        # cron: 30 20 * * 1-5
│   ├── hanoi_scheduler.py      # cron: 30 18 * * *
│   └── yeekee_scheduler.py     # cron: */15 * * * *
├── scrapers/
│   ├── base_scraper.py         # abstract class
│   ├── glo_scraper.py
│   ├── lao_scraper.py
│   └── hanoi_scraper.py
├── validators/
│   └── result_validator.py     # ตรวจสอบความถูกต้อง
├── normalizers/
│   └── result_normalizer.py    # จัดรูปแบบให้ตรงกัน
└── pipeline.py                 # ประกอบทุกส่วนเข้าด้วยกัน
```

---

## 3. Pipeline การทำงาน (ทีละขั้น)

```
[Trigger: Cron Job / Manual]
        |
        v
[Scraper / API Fetch]
  - ส่ง HTTP request
  - รับ HTML / JSON กลับมา
        |
        v
[Parser]
  - ดึงเลขออกจาก HTML
  - map field ให้ถูกต้อง
        |
        v
[Validator]
  - ตรวจว่าเลขครบ
  - ตรวจ format ถูกต้อง
  - ตรวจซ้ำกับที่มีอยู่
        |
     [ผ่าน?]
    /       \
  NO        YES
   |          |
[Alert]   [Normalizer]
[Log]       - แปลงเป็น schema กลาง
            - เพิ่ม metadata
                |
                v
          [Database Write]
          PostgreSQL + Redis Cache
                |
                v
          [Trigger ML Engine]
          ส่งสัญญาณให้ retrain / predict
```

---

## 4. Validator — ตรวจสอบข้อมูล

```python
from pydantic import BaseModel, validator
from datetime import date

class LotteryResult(BaseModel):
    type: str               # "glo" | "lao" | "hanoi" | "yeekee"
    draw_date: date
    numbers: dict           # {"first_prize": "123456", "last_2": "56", ...}
    source_url: str
    fetched_at: datetime

    @validator("numbers")
    def validate_numbers(cls, v, values):
        lottery_type = values.get("type")
        if lottery_type == "glo":
            assert "first_prize" in v, "Missing first_prize"
            assert len(v["first_prize"]) == 6, "first_prize must be 6 digits"
        if lottery_type in ["lao", "hanoi"]:
            assert "4_digits" in v, "Missing 4_digits"
        return v

    @validator("draw_date")
    def no_future_date(cls, v):
        assert v <= date.today(), "draw_date cannot be in the future"
        return v
```

---

## 5. Normalizer — จัดรูปแบบกลาง

ข้อมูลจากแต่ละแหล่งมี format ต่างกัน Normalizer จะแปลงให้อยู่ใน schema เดียวกันก่อน insert:

```python
def normalize(raw: dict) -> dict:
    return {
        "lottery_type_id": LOTTERY_TYPE_MAP[raw["type"]],
        "draw_date": raw["draw_date"],
        "result_json": {
            "primary": raw["numbers"].get("first_prize") or raw["numbers"].get("4_digits"),
            "secondary": extract_secondary(raw),
            "raw": raw["numbers"],
        },
        "source": raw["source_url"],
        "fetched_at": raw["fetched_at"].isoformat(),
    }
```

---

## 6. Scheduler — ตัวอย่าง Cron Expression

```bash
# สลากกินแบ่ง — วันที่ 1 และ 16 เวลา 15:05 น.
5 15 1,16 * * python run_collector.py --type=glo

# หวยลาว — จันทร์–ศุกร์ เวลา 20:35 น.
35 20 * * 1-5 python run_collector.py --type=lao

# หวยฮานอย — ทุกวัน 18:35 น.
35 18 * * * python run_collector.py --type=hanoi

# หวยยี่กี — ทุก 15 นาที
*/15 * * * * python run_collector.py --type=yeekee
```

สำหรับ Cloud ใช้ **Google Cloud Scheduler** หรือ **GitHub Actions** (`schedule:`) แทน cron บน server ตรงๆ เพื่อความเสถียร

---

## 7. Error Handling และ Retry

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=30)
)
async def fetch_with_retry(scraper_fn, draw_date: str):
    try:
        result = await scraper_fn(draw_date)
        return result
    except httpx.TimeoutException:
        await notify_slack(f"Timeout: {scraper_fn.__name__} {draw_date}")
        raise
    except Exception as e:
        await log_error(scraper_fn.__name__, draw_date, str(e))
        raise
```

**กรณีที่ต้อง handle:**

| กรณี | การจัดการ |
|---|---|
| เว็บล่ม / timeout | Retry 3 ครั้ง → แจ้ง Slack |
| ผลออกช้ากว่าปกติ | Retry ทุก 5 นาที สูงสุด 2 ชั่วโมง |
| ข้อมูลซ้ำ (duplicate) | Skip และ log warning |
| Format เปลี่ยน | Alert ทีม → Manual fix scraper |
| เลขไม่ผ่าน validate | บันทึก `status=rejected` พร้อม reason |

---

## 8. Tech Stack ที่แนะนำ

| ส่วน | เทคโนโลยี | เหตุผล |
|---|---|---|
| Scraping | `httpx` + `BeautifulSoup4` | async, เร็ว, เบา |
| JS-heavy sites | `Playwright` | รองรับ React/SPA |
| Scheduling | `APScheduler` หรือ Cloud Scheduler | จัดการ cron ง่าย |
| Validation | `Pydantic v2` | type-safe, error ชัด |
| Retry Logic | `tenacity` | retry pattern สำเร็จรูป |
| Queue (optional) | `Redis Queue (RQ)` | กระจาย task หลาย worker |
| Monitoring | `Sentry` + `Prometheus` | track error + latency |

---

## 9. ข้อควรระวัง

- **Rate Limiting** — อย่า request ถี่เกินไป อาจโดน block IP ควรใส่ `asyncio.sleep()` ระหว่าง request
- **User-Agent Rotation** — เปลี่ยน header เพื่อไม่ให้ถูกตรวจจับว่าเป็น bot
- **IP Rotation / Proxy** — สำหรับเว็บที่ block IP บ่อย ควรใช้ rotating proxy
- **Legal** — การ scrape บางเว็บอาจขัดกับ Terms of Service ให้ตรวจสอบก่อนใช้งานจริง
- **Timezone** — หวยแต่ละประเภทใช้ timezone ต่างกัน ควร store เป็น UTC ทุกครั้ง แล้วค่อย convert ตอนแสดงผล
