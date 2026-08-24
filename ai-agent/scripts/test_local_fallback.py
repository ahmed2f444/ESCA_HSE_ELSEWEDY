#!/usr/bin/env python3
"""
Exercises the local Ollama fallback tier directly, without touching Groq or
the running FastAPI app. Confirms:
  1. The local model (esca-agent-local) is reachable at LOCAL_LLM_BASE_URL.
  2. It reliably emits OpenAI-style tool_calls against the trimmed LOCAL_TOOLS set.
  3. Answers for a few real demo questions come back coherent.

Run with the FastAPI server stopped or running — this talks to Ollama directly,
not through /api/ask, so it isolates the local path from the Groq fallback chain.

Usage:
    python scripts/test_local_fallback.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openai import OpenAI
from app.config import settings
from app.tools.definitions import LOCAL_TOOLS
from app.agent import LOCAL_SYSTEM_PROMPT

local_client = OpenAI(api_key="ollama", base_url=settings.local_llm_base_url)

DEMO_QUESTIONS = [
    "Are there any overdue CAPAs right now?",
    "Show me the 5 most recent incidents.",
    "What are the latest critical AI detection events?",
]


def check_reachable() -> bool:
    print(f"Checking local model at {settings.local_llm_base_url} ...")
    try:
        local_client.models.list()
        print("  Ollama endpoint is reachable.\n")
        return True
    except Exception as exc:
        print(f"  Could not reach Ollama: {exc}")
        print("  Is `ollama serve` running, and did you run:")
        print(f"    ollama create {settings.local_llm_model} -f ollama/Modelfile")
        return False


def run_question(question: str):
    print("=" * 80)
    print(f"QUERY: {question}")
    print("=" * 80)
    messages = [
        {"role": "system", "content": LOCAL_SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    try:
        response = local_client.chat.completions.create(
            model=settings.local_llm_model,
            messages=messages,
            temperature=0.1,
            max_tokens=450,
            tools=LOCAL_TOOLS,
            tool_choice="auto",
        )
    except Exception as exc:
        print(f"  ERROR calling local model: {exc}\n")
        return

    message = response.choices[0].message
    if message.tool_calls:
        print(f"  Tool call(s) returned ({len(message.tool_calls)}):")
        for tc in message.tool_calls:
            args_raw = tc.function.arguments
            try:
                args = json.loads(args_raw)
                args_display = json.dumps(args)
            except Exception:
                args_display = f"MALFORMED JSON: {args_raw!r}"
            print(f"    - {tc.function.name}({args_display})")
            if tc.function.name not in {t["function"]["name"] for t in LOCAL_TOOLS}:
                print(f"      ⚠ picked a tool outside LOCAL_TOOLS — check the system prompt / model")
    else:
        preview = (message.content or "")[:300]
        print(f"  No tool call — direct text response:\n    {preview}")
    print()


def main():
    if not check_reachable():
        sys.exit(1)

    for q in DEMO_QUESTIONS:
        run_question(q)

    print("Done. Read each response above for:")
    print("  - malformed tool-call JSON")
    print("  - a tool name outside LOCAL_TOOLS")
    print("  - hallucinated column/argument names")
    print("If those look clean, the local fallback tier is working as expected.")


if __name__ == "__main__":
    main()
