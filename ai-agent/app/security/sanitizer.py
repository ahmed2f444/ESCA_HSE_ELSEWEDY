"""
ESCA HSE AI Agent - Sensitive Credential & Data Sanitization Subsystem.

Responsible for:
1. Scrubbing secrets (API keys, database URLs, passwords, Bearer tokens, private keys)
   from user inputs, assistant outputs, tool traces, error messages, and logs.
2. Neutralizing XSS vectors and unsafe HTML tags in generated content.
3. Safe recursive masking of structured dictionaries and lists.
4. Error message sanitization to prevent stack traces and internal leakage.
"""
import re
from typing import Any


# ── Secret Pattern Definitions ───────────────────────────────────────────────
_SECRET_PATTERNS = [
    # OpenAI / Groq API Keys (gsk_..., sk-...)
    (re.compile(r"\b(gsk_[a-zA-Z0-9]{20,})\b", re.IGNORECASE), "[REDACTED_API_KEY]"),
    (re.compile(r"\b(sk-[a-zA-Z0-9]{20,})\b", re.IGNORECASE), "[REDACTED_API_KEY]"),
    # Bearer tokens
    (re.compile(r"Bearer\s+[a-zA-Z0-9\-_.~+/]+=*", re.IGNORECASE), "Bearer [REDACTED_TOKEN]"),
    # Database URIs with credentials (e.g., mysql+pymysql://user:password@host:port/db)
    (
        re.compile(
            r"(mysql(\+pymysql)?|postgresql(\+psycopg2)?|sqlite|redis|mongodb)://(?P<user>[^:]+):(?P<pass>[^@]+)@(?P<host>[^:/]+)(?::(?P<port>\d+))?/(?P<db>[^\s\?\"']+)",
            re.IGNORECASE,
        ),
        r"\1://\g<user>:[REDACTED_PASSWORD]@\g<host>:\g<port>/\g<db>",
    ),
    # Generic password assignments in connection strings or logs
    (re.compile(r"(password|passwd|pwd|db_password|mysqlpassword)\s*[:=]\s*['\"]?([^\s'\",&]+)['\"]?", re.IGNORECASE), r"\1=[REDACTED_PASSWORD]"),
    # Secret keys / JWT secret keys
    (re.compile(r"(client_secret|jwt_secret|api_secret|secret_key)\s*[:=]\s*['\"]?([^\s'\",&]+)['\"]?", re.IGNORECASE), r"\1=[REDACTED_SECRET]"),
    # PEM / Private Keys
    (re.compile(r"-----BEGIN\s+(RSA\s+|EC\s+)?PRIVATE\s+KEY-----[\s\S]*?-----END\s+(RSA\s+|EC\s+)?PRIVATE\s+KEY-----", re.IGNORECASE), "[REDACTED_PRIVATE_KEY]"),
]

# Sensitive dictionary keys to mask
_SENSITIVE_DICT_KEYS = {
    "password", "password_hash", "hashed_password", "passwd", "pwd",
    "secret", "client_secret", "jwt_secret", "api_secret", "secret_key",
    "token", "access_token", "refresh_token", "auth_token", "api_key",
    "groq_api_key", "mysql_password", "db_password", "private_key",
    "salt", "ssn", "national_id"
}

# ── XSS & Unsafe HTML Patterns ──────────────────────────────────────────────
_XSS_PATTERNS = [
    re.compile(r"<\s*script[^>]*>[\s\S]*?<\s*/\s*script\s*>", re.IGNORECASE),
    re.compile(r"<\s*iframe[^>]*>[\s\S]*?<\s*/\s*iframe\s*>", re.IGNORECASE),
    re.compile(r"<\s*object[^>]*>[\s\S]*?<\s*/\s*object\s*>", re.IGNORECASE),
    re.compile(r"<\s*embed[^>]*>[\s\S]*?<\s*/\s*embed\s*>", re.IGNORECASE),
    re.compile(r"<\s*style[^>]*>[\s\S]*?<\s*/\s*style\s*>", re.IGNORECASE),
    re.compile(r"<\s*link[^>]*>", re.IGNORECASE),
    re.compile(r"<\s*meta[^>]*>", re.IGNORECASE),
    re.compile(r"<\s*base[^>]*>", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"data\s*:\s*text/html", re.IGNORECASE),
    re.compile(r"vbscript\s*:", re.IGNORECASE),
    re.compile(r"\bon[a-zA-Z]+\s*=\s*(['\"][^'\"]*['\"]|[^\s>]+)", re.IGNORECASE),  # onload=, onerror=, etc.
]


def scrub_secrets_from_text(text: str) -> str:
    """Removes all known secret keys, passwords, connection strings, and tokens from a string."""
    if not text or not isinstance(text, str):
        return ""
    sanitized = text
    for pattern, replacement in _SECRET_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def sanitize_xss(text: str) -> str:
    """Neutralizes dangerous HTML/script injection tags while preserving safe markdown."""
    if not text or not isinstance(text, str):
        return ""
    sanitized = text
    for pattern in _XSS_PATTERNS:
        sanitized = pattern.sub("", sanitized)
    return sanitized


def sanitize_data_payload(data: Any) -> Any:
    """
    Recursively scrubs secrets and sensitive dictionary keys from structured
    data (dicts, lists, primitives).
    """
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            if any(sens in k_lower for sens in _SENSITIVE_DICT_KEYS):
                cleaned[k] = "[REDACTED_SENSITIVE_FIELD]"
            else:
                cleaned[k] = sanitize_data_payload(v)
        return cleaned
    elif isinstance(data, list):
        return [sanitize_data_payload(item) for item in data]
    elif isinstance(data, str):
        return scrub_secrets_from_text(sanitize_xss(data))
    return data


def mask_safe_error(exc: Exception | str) -> str:
    """
    Converts raw internal exceptions or database error traces into safe,
    non-disclosing messages for clients.
    """
    err_str = str(exc)
    # Check if this error contains connection strings or passwords
    scrubbed = scrub_secrets_from_text(err_str)
    
    # Check for internal database syntax or driver errors
    if any(k in scrubbed.lower() for k in ("operationalerror", "programmingerror", "pymysql", "access denied", "sqlalchemy")):
        return "⚠️ حدث خطأ أثناء تنفيذ عملية قاعدة البيانات. تم تسجيل الخطأ داخلياً بأمان."
    
    return scrubbed
