"""
ESCA HSE AI Agent - Date, Time, Duration & Temporal Range Parser

Parses exact dates (ISO YYYY-MM-DD, DD/MM/YYYY, Named Month), relative dates
(+1 year, next week, غداً, بعد شهر, لسنة قادمة), 12h/24h digital times, colloquial
Arabic times, duration hours, and industrial factory shifts.
"""

import re
from datetime import date, datetime, time, timedelta
from typing import Optional, Tuple
from .constants import RELATIVE_DAY_KEYWORDS, ARABIC_MONTHS, ENGLISH_MONTHS
from .normalization import normalize_text


def parse_relative_or_exact_date(
    text: str, base_date: Optional[date] = None
) -> Tuple[Optional[date], Optional[int], Optional[str]]:
    """
    Extracts exact or relative date from prompt.
    Returns: (resolved_date, days_delta_from_today, match_type)
    """
    today = base_date or date.today()
    if not text:
        return None, None, None

    clean = normalize_text(text)

    # 1. ISO format: YYYY-MM-DD or YYYY/MM/DD
    iso_match = re.search(r"\b(20\d{2})[-/.](0[1-9]|1[0-2])[-/.](0[1-9]|[12]\d|3[01])\b", clean)
    if iso_match:
        try:
            d = date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
            return d, (d - today).days, "iso"
        except ValueError:
            pass

    # 2. DD-MM-YYYY or DD/MM/YYYY format
    dmy_match = re.search(r"\b(0[1-9]|[12]\d|3[01])[-/.](0[1-9]|1[0-2])[-/.](20\d{2})\b", clean)
    if dmy_match:
        try:
            d = date(int(dmy_match.group(3)), int(dmy_match.group(2)), int(dmy_match.group(1)))
            return d, (d - today).days, "dmy"
        except ValueError:
            pass

    # 3. Arabic Named Date: e.g. "15 مايو 2026" or "15 مايو"
    ar_named_match = re.search(r"\b(0?[1-9]|[12]\d|3[01])\s+([أ-ي]+)(?:\s+(20\d{2}))?\b", clean)
    if ar_named_match:
        day_val = int(ar_named_match.group(1))
        month_name = ar_named_match.group(2)
        year_val = int(ar_named_match.group(3)) if ar_named_match.group(3) else today.year
        norm_month = normalize_text(month_name)
        for m_name, m_num in ARABIC_MONTHS.items():
            if normalize_text(m_name) == norm_month:
                try:
                    d = date(year_val, m_num, day_val)
                    return d, (d - today).days, "arabic_named"
                except ValueError:
                    pass

    # 4. English Named Date: e.g. "15 May 2026", "May 15, 2026", "15th of June"
    en_named_match = re.search(r"\b(0?[1-9]|[12]\d|3[01])(?:st|nd|rd|th)?\s+(?:of\s+)?([a-z]+)(?:\s+(20\d{2}))?\b", clean)
    if en_named_match:
        day_val = int(en_named_match.group(1))
        month_name = en_named_match.group(2)
        year_val = int(en_named_match.group(3)) if en_named_match.group(3) else today.year
        if month_name in ENGLISH_MONTHS:
            try:
                d = date(year_val, ENGLISH_MONTHS[month_name], day_val)
                return d, (d - today).days, "english_named"
            except ValueError:
                pass

    # 5. Relative phrases match (Ordered by length descending for longest phrase priority)
    for phrase, days in sorted(RELATIVE_DAY_KEYWORDS.items(), key=lambda x: len(x[0]), reverse=True):
        norm_phrase = normalize_text(phrase)
        if f" {norm_phrase} " in f" {clean} " or norm_phrase == clean:
            target = today + timedelta(days=days)
            return target, days, "relative_keyword"

    # Substring search for relative keywords if boundary didn't catch attached prefix
    for phrase, days in sorted(RELATIVE_DAY_KEYWORDS.items(), key=lambda x: len(x[0]), reverse=True):
        norm_phrase = normalize_text(phrase)
        if len(norm_phrase) > 3 and norm_phrase in clean:
            target = today + timedelta(days=days)
            return target, days, "relative_keyword"

    return None, None, None


def parse_exact_or_colloquial_time(text: str) -> Tuple[Optional[time], Optional[str]]:
    """
    Extracts exact or colloquial time from text.
    Handles 12h meridiem (AM/PM, ص/م), 24h digital (17:30), and colloquial Arabic expressions.
    """
    if not text:
        return None, None
    clean = normalize_text(text)

    # 1. 12-hour with AM/PM or ص/م (Priority over raw 24h to avoid misidentifying 5:31 م as 05:31)
    match_12 = re.search(
        r"(?:الساع[ةه]\s+)?\b([1-9]|1[0-2])(?::([0-5]\d))?\s*(am|pm|a\.m\.|p\.m\.|صباحا|صباحاً|مساء|مساءً|ص|م)\b",
        clean,
    )
    if match_12:
        h = int(match_12.group(1))
        m = int(match_12.group(2)) if match_12.group(2) else 0
        mer = match_12.group(3).lower()
        if any(p in mer for p in ["pm", "مساء", "م"]) and h < 12:
            h += 12
        elif any(p in mer for p in ["am", "صباح", "ص"]) and h == 12:
            h = 0
        return time(h, m), "12h_meridiem"

    # 2. 24-hour HH:MM (e.g. "17:30", "08:45", "14:00")
    match_24 = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", clean)
    if match_24:
        h = int(match_24.group(1))
        m = int(match_24.group(2))
        return time(h, m), "24h_digital"

    # 3. Colloquial Arabic Time Phrases: e.g. "الساعة 5 ونصف", "الساعة 8 وربع", "الساعة 3 الا ربع"
    colloquial_match = re.search(
        r"(?:الساع[ةه]\s+)?\b([1-9]|1[0-2])\b(?:\s+(ونصف|ونص|وربع|وثلث|الا ربع|إلا ربع|الا ثلث|إلا ثلث))(?:\s+(صباحا|مساء|عصرا|ليلا))?",
        clean,
    )
    if colloquial_match:
        h = int(colloquial_match.group(1))
        fraction = colloquial_match.group(2) or ""
        period = colloquial_match.group(3) or ""

        m = 0
        if "نصف" in fraction or "نص" in fraction:
            m = 30
        elif "وربع" in fraction:
            m = 15
        elif "وثلث" in fraction:
            m = 20
        elif "الا ربع" in fraction or "إلا ربع" in fraction:
            h = (h - 1) % 12 or 12
            m = 45
        elif "الا ثلث" in fraction or "إلا ثلث" in fraction:
            h = (h - 1) % 12 or 12
            m = 40

        if any(p in period for p in ["مساء", "عصرا", "ليلا"]) and h < 12:
            h += 12
        elif "صباحا" in period and h == 12:
            h = 0

        return time(h, m), "arabic_colloquial"

    return None, None


def extract_duration_hours(text: str) -> Optional[float]:
    """
    Extracts permit or task duration in hours from text:
    e.g. 'duration 8 hours', 'لمدة 4 ساعات', '8h', '12 ساعة', 'نصف يوم', 'full day'
    """
    if not text:
        return None
    clean = normalize_text(text)

    # 1. Regex matching e.g. "8 hours", "8 hrs", "8h", "8 ساعات", "لمدة 8 ساعات"
    m = re.search(r"\b(?:for|duration|lasting|لمدة|فترة|مدة)?\s*(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h|ساعات|ساعة|ساعه)\b", clean)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass

    # 2. Words: full day, half day, shift, وردية
    if any(k in clean for k in ["full day", "يوم كامل", "24 hours", "24 ساعة"]):
        return 24.0
    if any(k in clean for k in ["half day", "نصف يوم", "12 hours", "12 ساعة"]):
        return 12.0
    if any(k in clean for k in ["shift", "وردية", "ورديه", "8 hours", "8 ساعات", "نوبتجية"]):
        return 8.0

    return None


def parse_shift_type(text: str) -> Optional[str]:
    """
    Extracts industrial shift from prompt:
    - MORNING / الوردية الصباحية / Shift A
    - EVENING / الوردية المسائية / Shift B
    - NIGHT / الوردية الليلية / Shift C
    """
    if not text:
        return None
    clean = normalize_text(text)
    if any(k in clean for k in ["morning shift", "shift a", "وردية اولى", "الوردية الصباحية", "وردية صباحية", "وردية أ", "وردية 1"]):
        return "MORNING"
    if any(k in clean for k in ["evening shift", "afternoon shift", "shift b", "وردية ثانية", "الوردية المسائية", "وردية مسائية", "وردية ب", "وردية 2"]):
        return "EVENING"
    if any(k in clean for k in ["night shift", "graveyard shift", "shift c", "وردية ثالثة", "الوردية الليلية", "وردية ليلية", "وردية ج", "وردية 3"]):
        return "NIGHT"
    return None
