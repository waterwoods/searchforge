"""vehicle_key must not stringify boolean slot flags (ymz:True|true|True regression)."""

from services.fiqa_api.inbox_triage.triage import (
    _derive_vehicle_key_from_add_car_text,
    _extract_add_car_fields,
    _extract_vehicle_identity_for_key,
)


def test_vehicle_key_uses_literals_not_boolean_slot_dict():
    """_extract_add_car_fields uses booleans — vehicle_key must not consume that dict."""
    bogus = _extract_add_car_fields(
        "[客户] 2024 Honda Civic 90210 下周提车"
    )
    assert bogus.get("year") is True
    assert _derive_vehicle_key_from_add_car_text(
        "[客户] 2024 Honda Civic 90210 下周提车"
    ) == "ymz:2024|honda_civic|90210"


def test_vehicle_key_multi_vehicle_first_segment():
    text = (
        "[客户] 我想同时给两辆车报价：2024 Honda Civic 90210 下周提车 我开；"
        "还有一辆2021 Toyota Prius 同地址 给我老婆开。电话 408-555-0404，姓名孙八。"
    )
    # Multi-vehicle: key follows scoped primary vehicle (see vehicle disambiguation policy).
    assert _derive_vehicle_key_from_add_car_text(text) == "ym:2021|toyota_prius"


def test_vehicle_identity_extracts_vin_prefix():
    t = "[客户] VIN 1HGBH41JXMN109186 邮编 94105"
    ident = _extract_vehicle_identity_for_key(t)
    assert ident["vin"] == "1HGBH41JXMN109186"
    assert _derive_vehicle_key_from_add_car_text(t) == "vin:1HGBH41JXMN109186"


def test_vehicle_key_year_model_without_zip():
    assert (
        _derive_vehicle_key_from_add_car_text("[客户] 加车 2024 Subaru Outback 95814")
        == "ymz:2024|subaru_outback|95814"
    )


def test_vehicle_key_year_followed_by_kuan_zh():
    """Year + 款 (no ASCII word boundary) must still parse."""
    t = "[客户] 我想给2024款BMW 330i做加车报价，邮编90210，下周三提车。"
    assert _derive_vehicle_key_from_add_car_text(t) == "ymz:2024|bmw_330i|90210"


def test_vehicle_key_strips_phone_before_zip():
    t = "[客户] 加车 2024 Tesla Model Y 650-111-2222 邮编 94107 下周提车 主驾本人 姓名陈九"
    assert _derive_vehicle_key_from_add_car_text(t) == "ymz:2024|tesla_model_y|94107"


def test_vehicle_key_follows_vehicle_correction_bubble():
    """Last-bubble correction must update y/m in vehicle_key (aligned with office summary)."""
    t = (
        "[客户] 加车 2024 BMW X5 邮编90210 下周三提车 我开\n\n"
        "[客户] 不是X5，是2023宝马X3，其它不变。"
    )
    # Model slug is tokenized from correction bubble (year must not stay on old X5).
    assert _derive_vehicle_key_from_add_car_text(t) == "ymz:2023|x3|90210"


def test_vehicle_key_scrubs_partial_vin_after_keyword_from_model_slug():
    t = "[客户] 2024 Toyota Camry zip 90210 VIN 12345"
    assert _derive_vehicle_key_from_add_car_text(t) == "ymz:2024|toyota_camry|90210"


def test_vehicle_key_keeps_inline_full_vin_after_keyword_in_model_path():
    vin = "1HGBH41JXMN109186"
    t = f"[客户] 2024 Toyota Camry zip 90210 VIN {vin}"
    assert _derive_vehicle_key_from_add_car_text(t) == f"vin:{vin}"
