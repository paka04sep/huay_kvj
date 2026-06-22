import pytest
from datetime import date
from pydantic import ValidationError
from backend.data_collection.validators.result_validator import LotteryResultModel
from backend.data_collection.normalizers.result_normalizer import normalize_result

def test_glo_validator_success():
    """
    ทดสอบ GLO Validator เมื่อข้อมูลถูกต้อง
    """
    valid_data = {
        "lottery_type": "glo",
        "draw_date": date(2026, 6, 16),
        "draw_number": None,
        "numbers": {
            "first_prize": "123456",
            "last_2": "56",
            "first_3": ["123", "456"],
            "last_3": ["789", "012"],
            "near_first": ["123455", "123457"]
        },
        "source_url": "https://test-source.com",
    }
    model = LotteryResultModel(**valid_data)
    assert model.lottery_type == "glo"
    assert model.numbers["first_prize"] == "123456"

def test_glo_validator_missing_first_prize():
    """
    ทดสอบ GLO Validator เมื่อไม่มีรางวัลที่ 1
    """
    invalid_data = {
        "lottery_type": "glo",
        "draw_date": date(2026, 6, 16),
        "numbers": {
            "last_2": "56"
        },
        "source_url": "https://test-source.com",
    }
    with pytest.raises(ValidationError) as excinfo:
        LotteryResultModel(**invalid_data)
    assert "Missing 'first_prize'" in str(excinfo.value)

def test_glo_validator_invalid_first_prize_digits():
    """
    ทดสอบ GLO Validator เมื่อรางวัลที่ 1 มีหลักไม่ครบ
    """
    invalid_data = {
        "lottery_type": "glo",
        "draw_date": date(2026, 6, 16),
        "numbers": {
            "first_prize": "12345", # 5 หลัก
            "last_2": "56"
        },
        "source_url": "https://test-source.com",
    }
    with pytest.raises(ValidationError) as excinfo:
        LotteryResultModel(**invalid_data)
    assert "must be a 6-digit numeric string" in str(excinfo.value)

def test_glo_normalizer():
    """
    ทดสอบ GLO Normalizer
    """
    raw_numbers = {
        "first_prize": "123456",
        "last_2": "56",
        "first_3": ["123", "456"],
        "last_3": ["789", "012"],
        "near_first": ["123455", "123457"]
    }
    normalized = normalize_result("glo", raw_numbers)
    assert normalized["primary"] == "123456"
    assert normalized["secondary"]["last_2"] == "56"
    assert len(normalized["secondary"]["first_3"]) == 2
    assert normalized["raw"] == raw_numbers

def test_lao_normalizer():
    """
    ทดสอบ Lao Normalizer
    """
    raw_numbers = {
        "digits_4": "4567"
    }
    normalized = normalize_result("lao", raw_numbers)
    assert normalized["primary"] == "4567"
    assert normalized["secondary"]["digits_3"] == "567"
    assert normalized["secondary"]["digits_2"] == "67"
