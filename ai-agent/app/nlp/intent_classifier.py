"""
ESCA HSE AI Agent - Multi-Module Intent Classifier & Scoring Engine

Classifies user queries across 60+ HSE intents across all 15 modules with
multi-intent ranking, contextual disambiguation, and confidence scoring.
"""

from typing import Optional, Tuple, List, Dict, Any
from .normalization import normalize_text, extract_word_tokens
from .module_keywords import HSE_INTENTS_KEYWORDS, INTENT_TO_MODULE_MAP, MODULE_METADATA


def score_all_intents(text: str) -> List[Dict[str, Any]]:
    """
    Scores all registered HSE intents against the input prompt.
    Returns a sorted list of matches with intent name, score, module_id, and matched keywords.
    """
    if not text:
        return []

    clean = normalize_text(text)
    clean_padded = f" {clean} "
    tokens = set(extract_word_tokens(text))
    scored_results = []

    for intent, keywords in HSE_INTENTS_KEYWORDS.items():
        score = 0
        matched_kws = []

        for kw in keywords:
            norm_kw = normalize_text(kw)
            if " " in norm_kw:
                # Multi-word phrase match
                if f" {norm_kw} " in clean_padded or norm_kw == clean:
                    weight = len(norm_kw.split()) * 6
                    score += weight
                    matched_kws.append((kw, weight))
                elif norm_kw in clean:
                    weight = len(norm_kw.split()) * 4
                    score += weight
                    matched_kws.append((kw, weight))
                else:
                    # Check if all words of the multi-word phrase are in the token set
                    kw_words = norm_kw.split()
                    if len(kw_words) >= 2 and all(w in tokens for w in kw_words):
                        weight = len(kw_words) * 3
                        score += weight
                        matched_kws.append((kw, weight))
            else:
                # Single word token match
                if norm_kw in tokens:
                    weight = 2
                    score += weight
                    matched_kws.append((kw, weight))
                elif f" {norm_kw} " in clean_padded:
                    weight = 1
                    score += weight
                    matched_kws.append((kw, weight))

        if score > 0:
            mod_id = INTENT_TO_MODULE_MAP.get(intent, 0)
            scored_results.append({
                "intent": intent,
                "score": score,
                "module_id": mod_id,
                "module_name": MODULE_METADATA.get(mod_id, {}).get("name_en", "General"),
                "matched_keywords": [m[0] for m in matched_kws]
            })

    # Sort primarily by score descending, then by matched phrase specificity
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    return scored_results


def classify_hse_intent(text: str) -> Tuple[Optional[str], List[str]]:
    """
    Classifies user prompt into primary intent and a ranked list of all matching secondary intents.
    Returns: (primary_intent, all_matching_intents)
    """
    scored = score_all_intents(text)
    if not scored:
        return None, []

    primary = scored[0]["intent"]
    all_intents = [item["intent"] for item in scored]
    return primary, all_intents


def classify_module_affinity(text: str) -> List[Dict[str, Any]]:
    """
    Calculates aggregated affinity scores for each of the 15 HSE modules based on user prompt.
    Returns a ranked list of relevant modules.
    """
    scored_intents = score_all_intents(text)
    module_scores: Dict[int, int] = {}

    for item in scored_intents:
        mod_id = item["module_id"]
        module_scores[mod_id] = module_scores.get(mod_id, 0) + item["score"]

    ranked_modules = []
    for mod_id, score in sorted(module_scores.items(), key=lambda x: x[1], reverse=True):
        ranked_modules.append({
            "module_id": mod_id,
            "score": score,
            "module_info": MODULE_METADATA.get(mod_id, {})
        })

    return ranked_modules
