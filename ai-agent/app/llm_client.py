import re
import time
import logging
from openai import OpenAI, RateLimitError
from app.config import settings

logger = logging.getLogger(__name__)
client = OpenAI(api_key=settings.groq_api_key, base_url=settings.groq_base_url, timeout=12.0)

# Local Ollama instance — OpenAI-compatible endpoint, no real API key needed.
# Only ever reached once every Groq model below has failed or is rate-limited.
local_client = OpenAI(api_key="ollama", base_url=settings.local_llm_base_url, timeout=60.0)

_FALLBACK_MODELS = [
    "qwen/qwen3.6-27b",
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
]


def _extract_retry_seconds(error_message: str) -> float:
    """Parse 'Please try again in Xs' from Groq error message."""
    match = re.search(r"try again in ([\d.]+)s", str(error_message))
    if match:
        return min(float(match.group(1)), 3.0)
    return 2.0   # fast default


def _call_local(messages: list[dict], kwargs: dict, local_tools: list[dict] | None):
    """Call Ollama with lean token limits optimized for RTX 3050 (4GB VRAM)."""
    local_kwargs = dict(kwargs)
    if local_tools:
        local_kwargs["tools"] = local_tools
        local_kwargs.setdefault("tool_choice", "auto")
    else:
        local_kwargs.pop("tools", None)
        local_kwargs.pop("tool_choice", None)

    return local_client.chat.completions.create(
        model=settings.local_llm_model,
        messages=messages,
        temperature=0.1,
        max_tokens=512,
        extra_body={
            "options": {
                "num_ctx": 2048,       # Small context to fit in 4GB VRAM
                "num_predict": 512,    # Bounded generation — prevents runaway compute
                "num_gpu": 99,         # Offload ALL layers to GPU for speed
                "num_thread": 4,       # CPU threads for any CPU-side work
            }
        },
        **local_kwargs,
    )


def chat_completion(
    messages: list[dict],
    tools: list[dict] | None = None,
    tool_choice: str = "auto",
    local_tools: list[dict] | None = None,
    model_mode: str = "auto",
) -> tuple[any, str]:
    """
    Executes a chat completion based on the requested `model_mode`:
      - "groq": Runs strictly through Groq cloud models.
      - "local": Runs strictly through local Ollama model (esca-agent-local).
      - "auto": Tries primary Groq -> fallback Groq -> local Ollama fallback -> Groq retry.

    Returns a tuple of `(response, model_used_name)`.
    """
    kwargs = {}
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = tool_choice

    # 1. Mode: Local Only
    if model_mode == "local":
        if not settings.local_llm_enabled:
            raise RuntimeError("النموذج المحلي غير مفعّل في الإعدادات.")
        logger.info(f"[LLM] Using local model '{settings.local_llm_model}' (User selected Local)...")
        try:
            res = _call_local(messages, kwargs, local_tools)
            return res, f"Local Ollama ({settings.local_llm_model})"
        except Exception as exc:
            logger.warning(f"[LLM] Local Ollama failed or not running: {exc}")
            raise RuntimeError(
                f"تعذّر الاتصال بخادم Ollama المحلي على المنفذ 11434. "
                f"يرجى التأكد من تشغيل تطبيق Ollama محلياً (`ollama run {settings.local_llm_model}`) أو اختيار وضع 'Groq Online' السحابي."
            )

    # 2. Mode: Groq Only or Auto Fallback
    models_to_try = [settings.groq_model] + [m for m in _FALLBACK_MODELS if m != settings.groq_model]
    last_rate_limit_wait = None

    for i, model in enumerate(models_to_try):
        try:
            res = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,
                **kwargs,
            )
            return res, f"Groq ({model})"
        except RateLimitError as exc:
            last_rate_limit_wait = _extract_retry_seconds(str(exc))
            if i < len(models_to_try) - 1:
                logger.warning(f"[Groq] Rate limit on '{model}', trying next model...")
                continue
            else:
                logger.warning(f"[Groq] All cloud models rate-limited.")
        except Exception as exc:
            if i < len(models_to_try) - 1:
                logger.warning(f"[Groq] Error on '{model}': {exc}. Trying next model...")
                continue
            else:
                logger.warning(f"[Groq] All cloud models failed ({exc}).")

    # If Auto mode and all cloud models failed, try local fallback
    if model_mode == "auto" and settings.local_llm_enabled:
        try:
            logger.warning(f"[LLM] Falling back to local model '{settings.local_llm_model}'...")
            res = _call_local(messages, kwargs, local_tools)
            return res, f"Local Ollama ({settings.local_llm_model}) [Fallback]"
        except Exception as exc:
            logger.warning(f"[LLM] Local fallback failed ({exc}).")

    # Last resort: wait out rate limit if available
    if last_rate_limit_wait is not None:
        logger.warning(f"[Groq] Waiting {last_rate_limit_wait:.1f}s then retrying primary model...")
        time.sleep(last_rate_limit_wait + 0.5)
        res = client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            temperature=0.2,
            **kwargs,
        )
        return res, f"Groq ({settings.groq_model})"

    raise RuntimeError("All LLM providers and fallbacks failed to respond.")
