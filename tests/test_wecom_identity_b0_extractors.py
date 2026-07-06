"""Unit tests for Track B0.2 WeCom-local extractors (ZIP, delivery date, primary driver).

Governed by docs/p16/TRACK_B0_ACTIVE_WORKSPACE_CONTRACT.md §4.2 — adapter-local
regex extraction only, no triage import, no case_draft_engine.py reuse.
"""

from __future__ import annotations

from services.fiqa_api.wecom.identity import (
    extract_delivery_date_from_text,
    extract_phone_from_text,
    extract_primary_driver_from_text,
    extract_vin_from_text,
    extract_zip_from_text,
    wecom_customer_display_label,
)


class TestExtractZip:
    def test_marker_prefixed_zip_english(self) -> None:
        assert extract_zip_from_text("my zip code is 91101") == "91101"

    def test_marker_prefixed_zip_chinese(self) -> None:
        assert extract_zip_from_text("邮编：91101") == "91101"

    def test_bare_five_digit_token(self) -> None:
        assert extract_zip_from_text("我在 91101 附近") == "91101"

    def test_no_zip_in_text(self) -> None:
        assert extract_zip_from_text("hello there") is None

    def test_empty_text(self) -> None:
        assert extract_zip_from_text("") is None
        assert extract_zip_from_text(None) is None

    def test_does_not_pull_from_contiguous_phone_digits(self) -> None:
        # A 10-digit run has no internal word boundary, so no false 5-digit match.
        assert extract_zip_from_text("call 6265550101") is None


class TestExtractDeliveryDate:
    def test_iso_date(self) -> None:
        assert extract_delivery_date_from_text("delivery date 2026-08-01") == "2026-08-01"

    def test_slash_date(self) -> None:
        assert extract_delivery_date_from_text("提车日期 8/1/2026") == "8/1/2026"

    def test_no_date_in_text(self) -> None:
        assert extract_delivery_date_from_text("no dates here") is None

    def test_does_not_match_phone_number_format(self) -> None:
        assert extract_delivery_date_from_text("call 626-555-0101") is None

    def test_empty_text(self) -> None:
        assert extract_delivery_date_from_text("") is None


class TestExtractPrimaryDriver:
    def test_english_marker(self) -> None:
        assert extract_primary_driver_from_text("primary driver is Jane Smith") == "Jane Smith"

    def test_english_marker_short_form(self) -> None:
        assert extract_primary_driver_from_text("driver: John") == "John"

    def test_chinese_marker(self) -> None:
        assert extract_primary_driver_from_text("主驾驶人是张伟") == "张伟"

    def test_stops_at_punctuation(self) -> None:
        assert extract_primary_driver_from_text("driver is Jane Smith, thanks") == "Jane Smith"

    def test_no_marker_no_match(self) -> None:
        assert extract_primary_driver_from_text("I bought a new car") is None

    def test_empty_text(self) -> None:
        assert extract_primary_driver_from_text("") is None


class TestExtractorsCoexistInOneMessage:
    """All B0.2 extractors are independent adapter-local regex passes — none
    should clash when a message happens to contain several fields at once."""

    def test_vin_phone_zip_all_extracted_from_one_message(self) -> None:
        text = "VIN 5YJ3E1EA8PF123456 电话626-555-0101 邮编91101"
        assert extract_vin_from_text(text) == "5YJ3E1EA8PF123456"
        assert extract_phone_from_text(text) == "6265550101"
        assert extract_zip_from_text(text) == "91101"


class TestWecomCustomerDisplayLabel:
    def test_known_name_wins(self) -> None:
        assert wecom_customer_display_label("wm_x", customer_name="张先生") == "张先生"

    def test_external_userid_suffix(self) -> None:
        assert wecom_customer_display_label("wmtLevSgAA25eirbmJC3r-nfQBCrmxcw") == "WeCom · …mxcw"

    def test_generic_fallback(self) -> None:
        assert wecom_customer_display_label(None) == "WeCom Customer"
