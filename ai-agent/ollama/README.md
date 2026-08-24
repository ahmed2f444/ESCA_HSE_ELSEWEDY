# Local LLM Fallback (Ollama)

Last-resort fallback tier for `app/llm_client.py`, used only after every Groq
model in the chain (`groq_model` + `_FALLBACK_MODELS`) is rate-limited or
erroring. Fully offline — no network calls leave the machine once the model
is pulled. Tuned for a 4GB RTX 3050.

## 1. Install Ollama and pull the model

```bash
# Linux/WSL2
curl -fsSL https://ollama.com/install.sh | sh
# Windows: download the installer from ollama.com

ollama pull qwen2.5:7b-instruct-q4_K_M
```

Sanity check before wiring anything up:

```bash
ollama run qwen2.5:7b-instruct-q4_K_M
```

## 2. Build the derived model (correct context size + GPU layers)

Ollama's default `num_ctx` (2048) is too small for this project's tool
schema. The `Modelfile` in this folder sets `num_ctx 8192` and
`num_gpu 20` (offloads ~20 of ~28 layers to the GPU, rest on CPU — safe
starting point for 4GB VRAM):

```bash
cd agent/ollama
ollama create esca-agent-local -f Modelfile
```

If `nvidia-smi` shows headroom during a call, raise `num_gpu` in increments
of 2 and re-run `ollama create`. If you see VRAM OOM errors, lower it.

## 3. Confirm it's wired up

The app already points at it via `.env`:

```
LOCAL_LLM_ENABLED=true
LOCAL_LLM_BASE_URL=http://localhost:11434/v1
LOCAL_LLM_MODEL=esca-agent-local
```

Set `LOCAL_LLM_ENABLED=false` to disable the local tier entirely (e.g. on a
machine without a GPU or without Ollama installed) — `chat_completion` will
skip straight to the old wait-and-retry-on-primary behavior.

## 4. Test checklist

- [ ] `ollama create esca-agent-local -f Modelfile` succeeds
- [ ] `python scripts/test_local_fallback.py` — hits the local model directly
      with real demo questions and flags malformed tool calls or tools picked
      outside the trimmed `LOCAL_TOOLS` set
- [ ] Temporarily blank/rename `GROQ_API_KEY` in `.env`, restart the app, hit
      `/api/ask`, confirm it falls through to the local model and still
      returns a coherent answer
- [ ] Watch `nvidia-smi` during one local-fallback call to confirm you're not
      pinned at 100% VRAM

## Why `run_read_only_query` and `get_db_schema` are excluded locally

`app/tools/definitions.py` exports `LOCAL_TOOLS`, a trimmed copy of `TOOLS`
without the two open-ended SQL tools. A 7B local model is more likely to
hallucinate a column name (`id` instead of `incident_id`, etc.) on free-form
SQL against this 60-table schema than to misuse a purpose-built tool with
fixed parameters. `app/llm_client.py` passes `LOCAL_TOOLS` to the local call
specifically (via `chat_completion(..., local_tools=LOCAL_TOOLS)` in
`app/agent.py`) while Groq keeps the full `TOOLS` list.
