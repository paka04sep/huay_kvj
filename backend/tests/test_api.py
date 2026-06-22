import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from datetime import date, datetime

from backend.api.main import app
from backend.api.database import get_db
from backend.api.cache import get_redis

# ใช้ anyio หรือ asyncio สำหรับ async tests
pytestmark = pytest.mark.anyio

# 1. ทดสอบ Root Endpoint
async def test_root_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"

# 2. ทดสอบ GET /api/results/latest แบบส่งประเภทผิด
async def test_latest_results_invalid_type():
    mock_db = MagicMock()
    mock_db.fetch = AsyncMock(return_value=[{"code": "glo"}, {"code": "lao"}])
    
    app.dependency_overrides[get_db] = lambda: mock_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/results/latest?type=invalid_type")
    
    assert resp.status_code == 400
    assert "Unsupported lottery type" in resp.json()["detail"]
    app.dependency_overrides.clear()

# 3. ทดสอบ GET /api/results/history แบบไม่ได้ส่งประเภทหวย
async def test_history_results_missing_type():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/results/history")
    assert resp.status_code == 422 # Unprocessable Entity จาก FastAPI

# 4. ทดสอบดึงข้อมูลสำเร็จจาก DB
async def test_latest_results_success_from_db():
    mock_db = MagicMock()
    mock_db.fetch = AsyncMock(return_value=[{"code": "glo"}, {"code": "lao"}])
    mock_db.fetchrow = AsyncMock(return_value={
        "draw_date": date(2026, 6, 16),
        "draw_number": "12",
        "result_json": '{"primary": "123456", "secondary": {"last_2": "56"}}',
        "source_url": "http://test.com",
        "fetched_at": datetime(2026, 6, 16, 15, 30)
    })
    
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock()

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_redis] = lambda: mock_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/results/latest?type=glo")
        
    assert resp.status_code == 200
    data = resp.json()
    assert data["lottery_type"] == "glo"
    assert data["draw_date"] == "2026-06-16"
    assert data["primary"] == "123456"
    assert data["secondary"]["last_2"] == "56"

    app.dependency_overrides.clear()

# 5. ทดสอบ Stats Endpoint
async def test_stats_endpoint_success():
    mock_db = MagicMock()
    mock_db.fetchrow = AsyncMock(return_value={"id": "some-uuid"})
    mock_db.fetch = AsyncMock(return_value=[
        {"draw_date": date(2026, 6, 16), "result_json": '{"primary": "123456", "secondary": {"last_2": "56"}}'},
        {"draw_date": date(2026, 6, 1), "result_json": '{"primary": "123455", "secondary": {"last_2": "55"}}'},
        {"draw_date": date(2026, 5, 16), "result_json": '{"primary": "123454", "secondary": {"last_2": "56"}}'},
    ])

    app.dependency_overrides[get_db] = lambda: mock_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/stats/hot-cold?type=glo&position=last_2&stat_type=numbers")
        
    assert resp.status_code == 200
    data = resp.json()
    assert data["lottery_type"] == "glo"
    assert data["position"] == "last_2"
    assert data["stat_type"] == "numbers"
    # เลข "56" ต้องเป็นเลขที่ฮอตที่สุด (ออก 2 ครั้ง)
    assert data["hot_numbers"][0]["number"] == "56"
    assert data["hot_numbers"][0]["count"] == 2
    # อัตราส่วน คู่/คี่ ต้องถูกต้อง (56 เป็นคู่, 55 เป็นคี่)
    # รวม 3 ตัวอย่าง: 56, 55, 56 -> คู่ 2, คี่ 1
    assert data["even_odd_ratio"]["even_count"] == 2
    assert data["even_odd_ratio"]["odd_count"] == 1

    app.dependency_overrides.clear()

# 6. ทดสอบ Predictions Endpoint
from unittest.mock import patch

@patch("backend.api.routes.predictions.EnsemblePredictor.predict_next")
async def test_predictions_endpoint_success(mock_predict_next):
    # จำลองผลการทำนาย
    mock_predict_next.return_value = [
        {"number": "12", "probability": 0.4, "lstm_prob": 0.3, "freq_prob": 0.5}
    ]
    
    mock_db = MagicMock()
    mock_db.fetchrow = AsyncMock(return_value={"id": "some-uuid"})
    mock_db.fetchval = AsyncMock(return_value=date(2026, 6, 16))
    
    app.dependency_overrides[get_db] = lambda: mock_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/predictions?type=glo")
        
    assert resp.status_code == 200
    data = resp.json()
    assert data["lottery_type"] == "glo"
    assert data["latest_draw_date"] == "2026-06-16"
    assert data["next_draw_date"] == "2026-07-01" # 16th June -> 1st July
    assert "predictions" in data
    assert data["predictions"]["two_down"][0]["number"] == "12"
    
    app.dependency_overrides.clear()

