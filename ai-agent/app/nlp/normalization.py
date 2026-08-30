"""
ESCA HSE AI Agent - Text Normalization, Tokenization & Morphological Analysis

Provides deep text normalization for Arabic (MSA, Egyptian colloquial, Gulf dialects)
and English technical HSE terminology.
"""

import re
import unicodedata
from typing import Set, List
from .constants import ARABIC_DIACRITICS, ARABIC_TATWEEL, ARABIC_CHAR_MAP, ARABIC_ATTACHED_PREFIXES


def normalize_arabic(text: str) -> str:
    """
    Strips diacritics, tatweel, and normalizes Arabic letter variations:
    - Normalizes [إأآٱ] -> ا
    - Normalizes ة -> ه
    - Normalizes [ىي] -> ي
    - Normalizes ئ / ؤ
    """
    if not text:
        return ""
    text = ARABIC_DIACRITICS.sub("", text)
    text = ARABIC_TATWEEL.sub("", text)
    for src, dst in ARABIC_CHAR_MAP.items():
        text = text.replace(src, dst)
    return text


def normalize_english(text: str) -> str:
    """
    Normalizes English text: lowercase, NFKD decomposition, trim whitespace.
    Preserves alphanumeric characters, dashes (for codes like PTW-001), and spaces.
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", str(text))
    return text.lower().strip()


def normalize_text(text: str) -> str:
    """
    Unified normalization pipeline for both Arabic and English.
    Handles Unicode normalization, Arabic orthography, and trims extra spaces.
    """
    if not text:
        return ""
    norm = unicodedata.normalize("NFKD", str(text))
    norm = normalize_arabic(norm)
    norm = norm.lower()
    # Collapse multiple whitespace characters
    norm = re.sub(r"\s+", " ", norm).strip()
    return norm


def extract_word_tokens(text: str) -> List[str]:
    """
    Extracts normalized word tokens and generates root tokens by stripping
    common Arabic attached prepositions (لـ, بـ, كـ, فـ, وـ, الـ, للـ, فالـ, وبالـ).
    Also preserves domain hyphenated IDs (e.g. PTW-001, PPE-EY-01, FE-CO2).
    """
    if not text:
        return []
    norm = normalize_text(text)
    raw_tokens = re.findall(r"[\w-]+", norm)
    token_set: Set[str] = set(raw_tokens)

    for t in raw_tokens:
        # Strip prefixes
        for prefix in ARABIC_ATTACHED_PREFIXES:
            if t.startswith(prefix) and len(t) > len(prefix) + 2:
                stripped = t[len(prefix):]
                token_set.add(stripped)
                # Check for secondary prefix (e.g. والـ + كلمة -> كلمة)
                if stripped.startswith("ال") and len(stripped) > 4:
                    token_set.add(stripped[2:])

    return list(token_set)


def contains_keyword_phrase(text: str, phrase: str) -> bool:
    """
    Checks if a given phrase (single or multi-word) is present in normalized text,
    matching either exact word boundaries or substring padded boundaries.
    """
    if not text or not phrase:
        return False
    norm_text = normalize_text(text)
    norm_phrase = normalize_text(phrase)

    if norm_phrase == norm_text:
        return True

    padded_text = f" {norm_text} "
    padded_phrase = f" {norm_phrase} "

    if padded_phrase in padded_text:
        return True

    # If single word, check token set
    if " " not in norm_phrase:
        tokens = set(extract_word_tokens(text))
        if norm_phrase in tokens:
            return True

    return norm_phrase in norm_text
