"""
ESCA HSE AI Agent - Entity Extraction & ID Recognition Pipeline

Extracts domain entity IDs (TRN-085, INC-001, PTW-002, CAPA-003, JSA-004, FE-014,
CHEM-005, EMP-010, FND-006), quantities, severity levels, risk levels, and zone/dept mappings.
"""

import re
from typing import Dict, Any, Optional
from .constants import WORD_TO_QUANTITY, SEVERITY_KEYWORDS, RISK_LEVEL_KEYWORDS, STATUS_TARGET_KEYWORDS
from .normalization import normalize_text
from .equipment_library import extract_equipment_info
from .chemical_library import extract_chemical_info


ENTITY_PREFIX_PATTERNS = {
    "certificate_id": [
        re.compile(r"\b(?:trn|cert|certificate|شهادة|شهاده|دورة|تدريب)[-_\s#]*0*(\d+)\b", re.IGNORECASE),
        re.compile(r"\btrn[-_]?0*(\d+)\b", re.IGNORECASE),
    ],
    "incident_id": [
        re.compile(r"\b(?:inc|incident|حادث|بلاغ|اصابة|إصابة)[-_\s#]*0*(\d+)\b", re.IGNORECASE),
        re.compile(r"\binc[-_]?0*(\d+)\b", re.IGNORECASE),
    ],
    "permit_id": [
        re.compile(r"\b(?:ptw|permit|eptw|تصريح(?:\s+عمل)?)[-_\s#]*(?:رقم|no|id)?[-_\s#]*0*(\d+)\b", re.IGNORECASE),
        re.compile(r"\bptw[-_]?0*(\d+)\b", re.IGNORECASE),
    ],
    "capa_id": [
        re.compile(r"\b(?:capa|action|اجراء|إجراء|تصحيح)[-_\s#]*(?:رقم|no|id)?[-_\s#]*0*(\d+)\b", re.IGNORECASE),
        re.compile(r"\bcapa[-_]?0*(\d+)\b", re.IGNORECASE),
    ],
    "inspection_id": [
        re.compile(r"\b(?:insp|inspection|فحص|تفتيش|معاينة|جولة(?:\s+تفتيش|\s+سلامة)?)[-_\s#]*(?:رقم|no|id)?[-_\s#]*0*(\d+)\b", re.IGNORECASE),
        re.compile(r"\binsp[-_]?0*(\d+)\b", re.IGNORECASE),
    ],
    "jsa_id": [
        re.compile(r"\b(?:jsa|تحليل مهام|سلامة مهام)[-_\s#]*(?:رقم|no|id)?[-_\s#]*0*(\d+)\b", re.IGNORECASE),
        re.compile(r"\bjsa[-_]?0*(\d+)\b", re.IGNORECASE),
    ],
    "equipment_id": [
        re.compile(r"\b(?:qr[-_]?)?(?:fe|ext|hyd|fire|طفاية|طفايه|معدة|معدات|معدة\s+إطفاء|معدة\s+اطفاء|معدة\s+الإطفاء|معدة\s+الاطفاء|طفاية\s+حريق|طفاية\s+الحريق)[-_\s#]*(?:رقم|no|id)?[-_\s#]*0*(\d+)\b", re.IGNORECASE),
        re.compile(r"\b(?:qr[-_]?fe[-_]?[a-z0-9_\-]+)\b", re.IGNORECASE),
        re.compile(r"\bfe[-_]?0*(\d+)\b", re.IGNORECASE),
    ],
    "finding_id": [
        re.compile(r"\b(?:finding|fnd|ملاحظة|ملاحظه|مخالفة|مخالفه)(?:\s+عدم\s+مطابقة|\s+عدم\s+المطابقة)?[-_\s#]*(?:رقم|no|id)?[-_\s#]*0*(\d+)\b", re.IGNORECASE),
        re.compile(r"\bfnd[-_]?0*(\d+)\b", re.IGNORECASE),
    ],
    "employee_id": [
        re.compile(r"\b(?:emp|usr|موظف|عامل|مستخدم)[-_\s#]*0*(\d+)\b", re.IGNORECASE),
        re.compile(r"\bemp[-_]?0*(\d+)\b", re.IGNORECASE),
    ],
    "chemical_id": [
        re.compile(r"\b(?:chem|chemical|مادة|مادة كيميائية)[-_\s#]*0*(\d+)\b", re.IGNORECASE),
        re.compile(r"\bchem[-_]?0*(\d+)\b", re.IGNORECASE),
    ],
    "sensor_id": [
        re.compile(r"\b(?:sensor|حساس|مستشعر)[-_\s#]*0*(\d+)\b", re.IGNORECASE),
        re.compile(r"\bsensor[-_]?0*(\d+)\b", re.IGNORECASE),
    ],
    "exam_id": [
        re.compile(r"\b(?:exam|فحص طبي|كشف طبي)[-_\s#]*0*(\d+)\b", re.IGNORECASE),
    ],
    "zone_id": [
        re.compile(r"\b(?:zone|area|منطقة|عنبر|قطاع|ورشة)[-_\s#]*0*(\d+)\b", re.IGNORECASE),
        re.compile(r"\bzone[-_]?0*(\d+)\b", re.IGNORECASE),
    ],
}


def extract_quantity(text: str) -> int:
    """Extracts integer quantity from prompt (e.g. 'give one safety glasses' -> 1, 'صرف 2 خوذة' -> 2)."""
    if not text:
        return 1
    t = normalize_text(text)

    # 1. Regex search for numerical values preceded or followed by transaction verbs
    m = re.search(
        r"\b(?:give|dispense|issue|صرف|إرجاع|ارجاع|عدد|qty|quantity|count)?\s*(\d+)\s*(?:pieces?|units?|items?|قطعة|قطع|حبة|خوذة|نظارة|حذاء|قفاز)?\b",
        t,
    )
    if m:
        try:
            val = int(m.group(1))
            if val > 0:
                return val
        except ValueError:
            pass

    # 2. Look for word numerals (e.g. 'واحدة', 'قطعتين', 'two', 'three')
    for word, num in WORD_TO_QUANTITY.items():
        norm_word = normalize_text(word)
        if f" {norm_word} " in f" {t} " or norm_word == t:
            return num

    return 1


def extract_severity_level(text: str) -> Optional[str]:
    """Extracts HSE incident / observation severity level (FATAL, CRITICAL, MAJOR, MODERATE, MINOR)."""
    if not text:
        return None
    clean = normalize_text(text)
    for sev, keywords in SEVERITY_KEYWORDS.items():
        for kw in keywords:
            norm_kw = normalize_text(kw)
            if f" {norm_kw} " in f" {clean} " or norm_kw in clean:
                return sev
    return None


def extract_risk_level(text: str) -> Optional[str]:
    """Extracts risk level (CRITICAL, HIGH, MEDIUM, LOW)."""
    if not text:
        return None
    clean = normalize_text(text)
    for r_level, keywords in RISK_LEVEL_KEYWORDS.items():
        for kw in keywords:
            norm_kw = normalize_text(kw)
            if f" {norm_kw} " in f" {clean} " or norm_kw in clean:
                return r_level
    return None


def extract_status_target(text: str) -> Optional[str]:
    """Extracts desired entity status (VALID, EXPIRED, APPROVED, SUSPENDED, CLOSED, DRAFT)."""
    if not text:
        return None
    clean = normalize_text(text)
    for status, keywords in STATUS_TARGET_KEYWORDS.items():
        for kw in keywords:
            norm_kw = normalize_text(kw)
            if f" {norm_kw} " in f" {clean} " or norm_kw in clean:
                return status
    return None


def extract_zone_info(text: str) -> Optional[Dict[str, Any]]:
    """Extracts factory zone / line info from prompt (e.g. Line A, Area 2, عنبر 1, خط الإنتاج C)."""
    if not text:
        return None
    clean = normalize_text(text)

    # 1. Arabic: عنبر X, خط الإنتاج X, منطقة X
    ar_match = re.search(r"\b(?:عنبر|منطقة|منطقه|خط|قطاع)\s+([0-9a-zأ-ي]+)\b", clean)
    if ar_match:
        zone_val = ar_match.group(1)
        return {"raw_zone": zone_val, "zone_identifier": zone_val.upper()}

    # 2. English: Area X, Line X, Zone X
    en_match = re.search(r"\b(?:area|line|zone|sector)\s+([0-9a-z]+)\b", clean)
    if en_match:
        zone_val = en_match.group(1)
        return {"raw_zone": zone_val, "zone_identifier": zone_val.upper()}

    return None


def extract_entity_ids(text: str) -> Dict[str, Any]:
    """
    Comprehensive entity ID extraction across all 15 HSE modules.
    Extracts permit_id, incident_id, capa_id, inspection_id, jsa_id, equipment_id,
    ppe_item_id, asset_summary_id, chemical_id, sensor_id, employee_id, quantity.
    """
    results: Dict[str, Any] = {}
    if not text:
        return results

    # 1. Regex prefix extraction
    for entity_name, patterns in ENTITY_PREFIX_PATTERNS.items():
        for pat in patterns:
            match = pat.search(text)
            if match:
                try:
                    val = int(match.group(1))
                    if val > 0:
                        results[entity_name] = val
                        break
                except (ValueError, IndexError):
                    pass

    # 2. Extract Equipment Entity Info
    eq_info = extract_equipment_info(text)
    if eq_info:
        if eq_info.get("ppe_item_id"):
            results["ppe_item_id"] = eq_info["ppe_item_id"]
        if eq_info.get("equipment_id"):
            results["equipment_id"] = eq_info["equipment_id"]
        if eq_info.get("asset_summary_id"):
            results["asset_summary_id"] = eq_info["asset_summary_id"]
        results["matched_equipment"] = eq_info

    # 3. Extract Chemical Entity Info
    chem_info = extract_chemical_info(text)
    if chem_info:
        if chem_info.get("chemical_id"):
            results["chemical_id"] = chem_info["chemical_id"]
        results["matched_chemical"] = chem_info

    # 4. Extract Quantity
    results["quantity"] = extract_quantity(text)

    # 5. Extract Zone
    zone_info = extract_zone_info(text)
    if zone_info:
        results["zone_info"] = zone_info
        if zone_info.get("raw_zone", "").isdigit():
            results["zone_id"] = int(zone_info["raw_zone"])

    return results


def extract_all_hse_entities(text: str) -> Dict[str, Any]:
    """Returns an exhaustive dictionary of all parsed entities, attributes, and tags."""
    ids = extract_entity_ids(text)
    ids["severity"] = extract_severity_level(text)
    ids["risk_level"] = extract_risk_level(text)
    ids["status_target"] = extract_status_target(text)
    return ids
