"""
ESCA HSE AI Agent - Multi-Layer Prompt Injection & Security Guardrail Subsystem.

Defends against:
1. Direct Prompt Injection (e.g. "ignore all instructions", "override system prompt", "jailbreak").
2. Persona Hijacking & Roleplay Bypasses (e.g. DAN, Developer Mode, evil twin).
3. Secret Harvesting Attacks (e.g. "print API keys", "show DB credentials", "reveal system prompt").
4. Delimiter and Control Token Injection (e.g. `<|im_start|>`, `<|system|>`, `[INST]`).
5. Base64 / Obfuscated Prompt Injection Payloads.
"""
import base64
import re
from typing import NamedTuple


class GuardCheckResult(NamedTuple):
    is_safe: bool
    reason: str | None
    sanitized_text: str
    rejection_response: str | None


# ── Known Jailbreak and System Override Patterns ─────────────────────────────
_PROMPT_INJECTION_PATTERNS = [
    # Direct instruction override
    re.compile(r"\b(ignore|disregard|forget|bypass|override)\s+(all\s+)?(previous|prior|above|system)\s+(instructions|rules|prompts|commands|guidelines)\b", re.IGNORECASE),
    re.compile(r"\b(system\s+override|admin\s+override|developer\s+mode|unrestricted\s+mode)\b", re.IGNORECASE),
    re.compile(r"\b(you\s+are\s+now|act\s+as)\s+(an?\s+)?(unrestricted|evil|dan|jailbroken|god\s+mode|unfiltered|ruleless)\b", re.IGNORECASE),
    re.compile(r"\b(do\s+anything\s+now|DAN\s+mode|jailbreak\s+prompt)\b", re.IGNORECASE),
    
    # Secret harvesting & system prompt extraction
    re.compile(r"\b(show|reveal|display|print|output|dump|tell|give)\s+(me\s+)?(your\s+)?(secret\s+)?(system\s+prompt|instructions|initial\s+prompt|raw\s+prompt|secret|api[_\s-]?key|database[_\s-]?password|db[_\s-]?password|credentials)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(is|are)\s+(your\s+)?(secret\s+)?(system\s+prompt|hidden\s+instructions|instructions|prompt)\b", re.IGNORECASE),
    re.compile(r"(ما\s*هي\s*(تعليماتك\s*(السرية|الأصلية)?|كلمة\s*السر\s*لقاعدة\s*البيانات|مفاتيح\s*API|بيانات\s*الاعتماد|تعليمات\s*النظام\s*الأصلية))", re.IGNORECASE),
    re.compile(r"(تجاهل\s*(جميع\s*)?(التعليمات\s*السابقة|القواعد|الأوامر|المحددات))", re.IGNORECASE),
    re.compile(r"(تصرف\s*كأنك\s*(غير\s*مقيد|مخترق|بدون\s*قواعد))", re.IGNORECASE),
    re.compile(r"(اكشف\s*(لي\s*)?(النظام\s*الداخلي|بيانات\s*الاتصال|كلمات\s*المرور))", re.IGNORECASE),
]

# Control Delimiters to neutralize
_CONTROL_TOKENS = [
    "<|im_start|>", "<|im_end|>", "<|system|>", "<|user|>", "<|assistant|>",
    "<|endoftext|>", "<s>", "</s>", "[INST]", "[/INST]", "<<SYS>>", "<</SYS>>"
]


def _detect_obfuscated_base64_injection(text: str) -> bool:
    """Detects base64 encoded strings in user input that decode to known injection patterns."""
    b64_matches = re.findall(r"\b[A-Za-z0-9+/]{24,}={0,2}\b", text)
    for b64_str in b64_matches:
        try:
            decoded = base64.b64decode(b64_str).decode("utf-8", errors="ignore").lower()
            if any(p.search(decoded) for p in _PROMPT_INJECTION_PATTERNS):
                return True
        except Exception:
            continue
    return False


def neutralize_control_tokens(text: str) -> str:
    """Strips or escapes special model control delimiters to prevent context escape."""
    if not text or not isinstance(text, str):
        return ""
    sanitized = text
    for token in _CONTROL_TOKENS:
        sanitized = sanitized.replace(token, f"[ESCAPED_TOKEN_{token.strip('<>|[]/')}]")
    return sanitized


def evaluate_prompt_safety(text: str) -> GuardCheckResult:
    """
    Evaluates incoming user questions for Prompt Injection, Jailbreak, and Secret Harvesting.
    Returns GuardCheckResult with safety status and appropriate refusal if unsafe.
    """
    if not text or not isinstance(text, str):
        return GuardCheckResult(is_safe=True, reason=None, sanitized_text="", rejection_response=None)

    clean_text = text.strip()
    
    # 1. Check for known injection patterns
    for pattern in _PROMPT_INJECTION_PATTERNS:
        if pattern.search(clean_text):
            return GuardCheckResult(
                is_safe=False,
                reason=f"Prompt injection or secret harvesting pattern matched: {pattern.pattern}",
                sanitized_text=neutralize_control_tokens(clean_text),
                rejection_response=(
                    "⚠️ **تنبيه أمني:** لا يمكن تنفيذ هذا الطلب لأنه يتعارض مع بروتوكولات الأمان وحماية البيانات "
                    "المعتمدة في شركة السويدي للكابلات (ESCA). النظام مصمم حصرياً لإدارة عمليات السلامة والصحة المهنية (HSE)."
                )
            )

    # 2. Check for base64 obfuscated injection
    if _detect_obfuscated_base64_injection(clean_text):
        return GuardCheckResult(
            is_safe=False,
            reason="Obfuscated base64 prompt injection detected.",
            sanitized_text=neutralize_control_tokens(clean_text),
            rejection_response=(
                "⚠️ **تنبيه أمني:** تم اكتشاف نص مشفر غير مصرح به يتعارض مع سياسات الأمان والحماية."
            )
        )

    # 3. Neutralize any control tokens
    sanitized = neutralize_control_tokens(clean_text)
    return GuardCheckResult(
        is_safe=True,
        reason=None,
        sanitized_text=sanitized,
        rejection_response=None
    )
