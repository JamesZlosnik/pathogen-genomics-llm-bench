# Setup Guide — Providers, Models, and Harnesses

This document covers how to get local LLM inference servers and agentic coding harnesses
running on **macOS (Apple Silicon)**. Linux notes are included where the setup differs
meaningfully. Windows is not covered — if you need it, the LM Studio and llama.cpp
sections are the best starting points as both have Windows installers.

> **Last reviewed:** June 2026. This space moves fast — check linked docs if something
> has changed.

---

## Contents

1. [Hardware and memory guide](#1-hardware-and-memory-guide)
2. [Model formats and where to get them](#2-model-formats-and-where-to-get-them)
3. [Inference providers](#3-inference-providers)
   - [LM Studio](#lm-studio) — easiest; GUI + OpenAI-compatible server
   - [llama.cpp (llama-server)](#llamacpp--llama-server) — most control; CLI
   - [mlx-lm](#mlx-lm) — best raw throughput on Apple Silicon; Python
4. [Agentic harnesses](#4-agentic-harnesses)
   - [Claude Code](#claude-code)
   - [OpenCode](#opencode)
   - [OpenAI Codex CLI](#openai-codex-cli)
5. [Wiring harnesses to providers](#5-wiring-harnesses-to-providers)
6. [Recommended models for this benchmark](#6-recommended-models-for-this-benchmark)
7. [Verifying your setup](#7-verifying-your-setup)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Hardware and Memory Guide

Apple Silicon Macs use **unified memory** — the same pool is shared by CPU and GPU,
so the full RAM is available for model weights. This is the key advantage over
discrete GPU setups.

| Unified RAM | What fits comfortably |
|-------------|----------------------|
| 8 GB | 3–4B models at Q4 quantization |
| 16 GB | 7–8B models at Q4; 14B models at Q2 |
| 24 GB | 14B models at Q4; 32B at Q2–Q3 |
| 32 GB | 14B at full Q8; 32B at Q4 |
| 64 GB | 70B at Q4; 32B at Q8 |
| 96–128 GB | 70B+ at Q8; some 405B models quantized |

**Rule of thumb:** model weights + KV cache must fit in RAM. For a 7B Q4_K_M model,
weights are ~4.5 GB; at 32K context with 4-bit KV cache, add ~2 GB. At f16 KV cache,
add ~8 GB. Always leave ~4 GB for macOS and other processes.

For this benchmark, **14B or larger at Q4_K_M or better** is the minimum recommended
to get meaningful results on the Tier 3–4 projects. Smaller models will pass Tier 1–2
but struggle with complex DSL2 and multi-step integration tasks.

---

## 2. Model Formats and Where to Get Them

### Formats

| Format | Used by | Notes |
|--------|---------|-------|
| **GGUF** | llama.cpp, LM Studio | Most widely supported; get `Q4_K_M` as a starting point |
| **MLX** | mlx-lm | Apple-native; better throughput on M-series; from `mlx-community` on HF |
| **Safetensors / HF** | conversion source | Not run directly; convert to GGUF or MLX |

### Where to download

- **Hugging Face** — `huggingface.co`. Use `huggingface-cli`:
  ```bash
  pip install huggingface_hub
  huggingface-cli download \
    bartowski/gemma-4-27b-it-GGUF \
    --include "gemma-4-27b-it-Q4_K_M.gguf" \
    --local-dir ~/models/
  ```
- **mlx-community** — pre-converted MLX models at `huggingface.co/mlx-community`.
  Good source for Apple-optimized quantizations.

### Recommended quantizations

For benchmarking, use the same quantization across all model comparisons.
`Q4_K_M` (GGUF) or `4bit` (MLX) is the standard. Record the exact quant in your run
metadata.

---

## 3. Inference Providers

All three providers below expose an **OpenAI-compatible API**. Harnesses connect to
whichever one is running by pointing at its base URL. You only need one running at a time.

| Provider | Default port | Best for |
|----------|-------------|---------|
| LM Studio | `1234` | Getting started; GUI model management |
| llama.cpp | `8080` | Maximum control; scripted launches; non-Apple hardware |
| mlx-lm | `8080` | Best tokens/sec on Apple Silicon |

---

### LM Studio

**macOS install:**
1. Download from [lmstudio.ai](https://lmstudio.ai) — grab the Apple Silicon `.dmg`
2. Drag to `/Applications`, open; allow through Gatekeeper if prompted
3. Requires macOS 14 (Sonoma) or later; Apple Silicon only for the MLX backend
   (Intel Macs fall back to llama.cpp backend automatically)

**Download a model:**
- Open LM Studio → Discover tab → search for your model → Download
- Or use the `lms` CLI (run `lms bootstrap` once after first launch to register it):
  ```bash
  lms get gemma4-27b-it
  lms ls  # list installed models
  ```

**Start the API server:**
- GUI: Developer tab → toggle Status to Running
- CLI:
  ```bash
  lms load gemma4-27b-it
  lms server start --port 1234
  ```
- Verify: `curl http://localhost:1234/v1/models`

**Linux:** LM Studio ships an AppImage for Linux. Download from lmstudio.ai,
`chmod +x` it and run. GPU acceleration via CUDA (NVIDIA) or ROCm (AMD).

---

### llama.cpp / llama-server

**macOS install (Homebrew — simplest):**
```bash
brew install llama.cpp
```

**macOS install (build from source — recommended for benchmarking so you can pin a commit):**
```bash
# Prerequisites
xcode-select --install  # installs clang and build tools

# Clone and build with Metal acceleration
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp

cmake -B build \
  -DBUILD_SHARED_LIBS=OFF \
  -DGGML_METAL=ON \
  -DGGML_CUDA=OFF
cmake --build build --config Release -j$(sysctl -n hw.ncpu)

# Binaries are in build/bin/
ls build/bin/
```

> **Benchmarking note:** record the git commit hash when you build.
> Bleeding-edge builds may have regressions for specific models;
> pinning a known-good commit and documenting it in your run notes avoids
> confounding model quality with inference bugs.

**Start the server:**
```bash
./build/bin/llama-server \
  -m ~/models/gemma-4-27b-it-Q4_K_M.gguf \
  --host 127.0.0.1 \
  --port 8080 \
  -c 32768 \
  -ngl 99            # offload all layers to Metal GPU
```

Key flags:
- `-c` — context window in tokens; use at least 16384 for these projects; 32768 is safer
- `-ngl` — number of GPU layers; set to 99 to offload everything to Metal (adjust down if
  you run out of memory)
- `--threads` — CPU threads for non-GPU layers; defaults to hardware threads

**Linux (CUDA):**
```bash
cmake -B build -DGGML_CUDA=ON
cmake --build build --config Release -j$(nproc)
# Then launch with -ngl 99 to offload to CUDA GPU
```

**Verify:**
```bash
curl http://localhost:8080/v1/models
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"local","messages":[{"role":"user","content":"Say hi"}],"max_tokens":20}'
```

---

### mlx-lm

Apple Silicon only. Provides the best tokens/sec on M-series chips for supported model
architectures. Models must be in MLX format (from `mlx-community` on Hugging Face).

**Install:**
```bash
# Requires Python 3.11+ and macOS with Apple Silicon
pip install mlx-lm

# Or with uv (faster):
uv pip install mlx-lm
```

**Download an MLX model:**
```bash
huggingface-cli download mlx-community/gemma-4-27b-it-4bit \
  --local-dir ~/models/mlx/gemma4-27b-4bit
```

**Start the server:**
```bash
python -m mlx_lm.server \
  --model mlx-community/gemma-4-27b-it-4bit \
  --host 127.0.0.1 \
  --port 8080 \
  --max-tokens 32768   # IMPORTANT: default is 512, too short for coding tasks
```

The server downloads the model on first run if not already cached in
`~/.cache/huggingface/hub/`.

**Verify:**
```bash
curl http://localhost:8080/v1/models
```

> **Note:** mlx-lm is Apple Silicon only. For Linux or Intel Mac, use llama.cpp instead.

---

## 4. Agentic Harnesses

### Claude Code

Claude Code is Anthropic's official CLI coding agent. It is primarily designed for
Anthropic's API, but can be redirected to a local OpenAI-compatible endpoint.

**Install:**
```bash
npm install -g @anthropic-ai/claude-code
# or
brew install claude-code
```

**Point at a local provider** (see [Section 5](#5-wiring-harnesses-to-providers) for
full wiring instructions):
```bash
export ANTHROPIC_BASE_URL="http://localhost:8080"
export ANTHROPIC_AUTH_TOKEN="not-needed"
unset ANTHROPIC_API_KEY
claude --model <model-name>
```

---

### OpenCode

OpenCode is an open-source agentic coding harness that natively supports any
OpenAI-compatible endpoint via its config file.

**Install:**
```bash
npm install -g opencode-ai
# or
brew install opencode
```

**Config file** (`~/.config/opencode/config.json`):
```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "local": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Local LLM",
      "options": {
        "baseURL": "http://127.0.0.1:8080/v1"
      },
      "models": {
        "gemma4-27b": {
          "name": "Gemma4-27B"
        }
      }
    }
  }
}
```

Change `baseURL` to match your provider's port (1234 for LM Studio, 8080 for
llama.cpp / mlx-lm). The model ID must match the `id` returned by
`GET /v1/models` on your running server.

**Launch:**
```bash
opencode --provider local --model gemma4-27b
```

---

### OpenAI Codex CLI

OpenAI's Codex CLI supports custom OpenAI-compatible endpoints via a config profile.

**Install:**
```bash
npm install -g @openai/codex
# or
brew install codex
```

**Config** (`~/.codex/config.toml`):
```toml
[profile.local]
provider = "openai"
base_url = "http://127.0.0.1:8080/v1"
api_key = "not-needed"
model = "gemma4-27b"
requires_openai_auth = false
model_context_window = 32768
```

**Launch:**
```bash
codex --oss --profile local
```

> **Note:** Always launch with `--oss` and `--profile <name>` when using a local model;
> launching without these flags opens the ChatGPT sign-in flow with no escape.

---

## 5. Wiring Harnesses to Providers

The key insight: **all three providers expose an OpenAI-compatible API**. The harness
just needs the base URL and a placeholder API key (local servers don't validate it).

| Provider | Base URL | Notes |
|----------|---------|-------|
| LM Studio | `http://localhost:1234/v1` | Default; configurable in Developer tab |
| llama.cpp | `http://127.0.0.1:8080/v1` | Port set via `--port` flag |
| mlx-lm | `http://127.0.0.1:8080/v1` | Port set via `--port` flag |

**Getting the model ID** (important — harnesses must use the exact string the server returns):
```bash
curl http://localhost:8080/v1/models | python3 -m json.tool
```

The `id` field in the response is what you pass as the model name to the harness.

**Environment variable approach (works for all harnesses):**
```bash
export OPENAI_BASE_URL="http://127.0.0.1:8080/v1"
export OPENAI_API_KEY="not-needed"
```

**Claude Code specifically** — uses Anthropic-format environment variables:
```bash
export ANTHROPIC_BASE_URL="http://127.0.0.1:8080"   # no /v1 suffix
export ANTHROPIC_AUTH_TOKEN="not-needed"
unset ANTHROPIC_API_KEY
```

---

## 6. Recommended Models for This Benchmark

These models have strong instruction-following and tool-calling, which are required for
agentic harness use. All available in both GGUF and MLX format.

| Model | Params | Min RAM | Strengths | HF ID (GGUF) |
|-------|--------|---------|-----------|--------------|
| Gemma4-27B-Instruct | 27B | 24 GB | Strong general coding and instruction following | `bartowski/gemma-4-27b-it-GGUF` |
| Llama-3.3-70B-Instruct | 70B | 64 GB | Best overall quality at high RAM | `bartowski/Llama-3.3-70B-Instruct-GGUF` |
| Mistral-Small-3.2-24B | 24B | 24 GB | Strong coding, efficient at 24B | `bartowski/Mistral-Small-3.2-24B-Instruct-GGUF` |
| Phi-4-reasoning | 14B | 16 GB | Strong reasoning at smaller size | `bartowski/phi-4-reasoning-GGUF` |

Use `Q4_K_M` quantization as the standard for comparability.

For MLX (Apple Silicon), use the `mlx-community` equivalents with `4bit` quantization.

---

## 7. Verifying Your Setup

Before running a benchmark project, confirm the full stack with this checklist:

```bash
# 1. Server is running and responding
curl -s http://localhost:8080/v1/models | python3 -m json.tool

# 2. Chat completions work (replace model name with yours)
curl -s http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma4-27b",
    "messages": [{"role": "user", "content": "What is the MLST scheme for E. coli?"}],
    "max_tokens": 200
  }' | python3 -m json.tool

# 3. Harness connects (Claude Code example)
ANTHROPIC_BASE_URL=http://localhost:8080 \
ANTHROPIC_AUTH_TOKEN=not-needed \
claude --model gemma4-27b --print "What is samtools depth -a?"

# 4. Record model identity — ask the model what it is
# A model that misidentifies itself is a config problem, not a model quality issue
```

Also run the identity probe before every benchmark session:
> "What model are you and what is your context window?"

If the response names the wrong model or says it's Claude/GPT when it shouldn't,
your routing is misconfigured.

---

## 8. Troubleshooting

**GateKeeper blocking llama.cpp binaries (macOS)**
If you downloaded pre-built binaries rather than building from source:
```bash
xattr -dr com.apple.quarantine ~/llama.cpp/
```
Or build from source to avoid it entirely.

**Model fits in RAM but inference is very slow**
macOS is swapping to disk — the model plus KV cache exceeds available RAM.
Check Activity Monitor → Memory → Memory Pressure. If yellow or red:
- Reduce context window (`-c 8192` instead of `-c 32768`)
- Use a smaller quantization (Q3_K_M instead of Q4_K_M)
- Use a smaller model

**Claude Code loops or produces garbled output**
The local model is not keeping up with the agentic format. Common causes:
- Context window too small (increase to at least 16K)
- Model too small for the harness's structured output requirements
- Try a larger or more capable model

**mlx-lm: max tokens too short**
The default `max_tokens` in mlx-lm is 512, which truncates most coding responses.
Always set `--max-tokens 32768` or higher when starting the server.

**OpenCode can't find the model**
The model ID in `config.json` must exactly match the `id` returned by
`GET /v1/models`. Run `curl localhost:8080/v1/models` to check.

**Codex drops into OpenAI login screen**
Always use `codex --oss --profile <your-local-profile>`. Without `--oss`, it defaults
to the OpenAI auth flow.
