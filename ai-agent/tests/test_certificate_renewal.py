import pytest
from datetime import date, datetime, timedelta
from sqlalchemy import text
from app.database import SessionLocal
from app.tools.handlers import create_certificate, update_certificate_status, delete_record
from app.nlp.keyword_parser import parse_user_hse_prompt, extract_entity_ids


def test_certificate_renewal_default_duration():
    """Verify that renewing a certificate without explicit date defaults to the accredited duration (+1 Year / 365 days)."""
    db = SessionLocal()
    try:
        # 1. Create a test certificate that is currently expired
        created = create_certificate(
            db=db,
            employee_name="عمر خالد",
            course_name="السلامة العامة",
            expiry_date="today",
            expiry_time="11:58"
        )
        assert created.get("success") is True
        cid = created["certificate_id"]
        assert created["status"] == "EXPIRED"

        # 2. Renew the certificate (simulating user saying "renew TRN-XXX" / "جدد الشهادة")
        renewed = update_certificate_status(
            db=db,
            certificate_id=cid,
            status="VALID"
        )
        assert renewed.get("success") is True
        assert renewed["status"] == "VALID"
        assert renewed["status_ar"] == "سارية ومعتمدة (VALID)"
        assert renewed["certificate_code"] == f"TRN-{cid:03d}"
        assert renewed["employee_name"] == "عمر خالد"
        assert renewed["days_remaining"] == 365
        assert renewed["days_remaining_text"] == "365 يوم"
        assert renewed["days_remaining_ar"] == "365 يوم"
        assert renewed["expiry_time"] == "11:58" or renewed["expiry_time"] == "23:59"

        expected_expiry = (date.today() + timedelta(days=365)).isoformat()
        assert renewed["new_expiry_date"] == expected_expiry

        # 3. Clean up
        delete_record(db=db, table_name="certificates", record_id=cid, reason="Test cleanup")
    finally:
        db.close()


def test_certificate_renewal_relative_durations():
    """Verify that renewing with relative durations (2 years, 6 months, 1 year) calculates exact target dates."""
    db = SessionLocal()
    try:
        created = create_certificate(
            db=db,
            employee_name="عمر خالد",
            course_name="السلامة العامة",
            expiry_date="today"
        )
        cid = created["certificate_id"]

        # Test 2 years
        ren_2y = update_certificate_status(
            db=db,
            certificate_id=cid,
            expiry_date="2 years",
            status="VALID"
        )
        assert ren_2y.get("success") is True
        assert ren_2y["status"] == "VALID"
        assert ren_2y["days_remaining"] >= 729
        assert "يوم" in ren_2y["days_remaining_text"]

        # Test 6 months
        ren_6m = update_certificate_status(
            db=db,
            certificate_id=cid,
            expiry_date="6 months",
            status="VALID"
        )
        assert ren_6m.get("success") is True
        assert ren_6m["days_remaining"] >= 179

        # Clean up
        delete_record(db=db, table_name="certificates", record_id=cid, reason="Test cleanup")
    finally:
        db.close()


def test_certificate_renewal_past_date_rejected():
    """Verify that attempting to renew with a past date is rejected with clear user guidance."""
    db = SessionLocal()
    try:
        created = create_certificate(
            db=db,
            employee_name="عمر خالد",
            course_name="السلامة العامة",
            expiry_date="today"
        )
        cid = created["certificate_id"]

        res = update_certificate_status(
            db=db,
            certificate_id=cid,
            expiry_date="2020-01-01",
            status="VALID"
        )
        assert "error" in res
        assert "يقع في الماضي" in res["error"] or "غير صحيحة" in res["error"]
        assert "guidance" in res

        # Clean up
        delete_record(db=db, table_name="certificates", record_id=cid, reason="Test cleanup")
    finally:
        db.close()


def test_certificate_id_extraction_and_nlp_routing():
    """Verify that domain IDs like TRN-063 and renewal phrasing are parsed properly."""
    ids1 = extract_entity_ids("renew TRN-063")
    assert ids1.get("certificate_id") == 63

    ids2 = extract_entity_ids("جدد شهادة TRN-063 للموظف عمر خالد")
    assert ids2.get("certificate_id") == 63

    parsed = parse_user_hse_prompt("جدد شهادة رقم TRN-063")
    assert parsed.entity_ids.get("certificate_id") == 63
    assert parsed.primary_intent == "RENEW_CERTIFICATE"
    assert "update_certificate_status" in parsed.recommended_tools
