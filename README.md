# sdk-examples

Cookbook examples for the official tonia Pass SDKs.

Set `TONIA_API_KEY` in your environment. Use placeholder values in committed
files — never commit a live key. Examples call `models.list()` and pick an
id from that allowlist. That list is Bearer / OpenAI-shaped
(`anthropic/claude-…`); `x-api-key` listing returns Anthropic-shaped ids.

Runtime: Python 3.11+, Node.js 22+, and Rust 1.85+ (same floors as the
official SDKs). Rust examples use `tonia-sdk` **0.4.4** from
[`tonia-router/rust-sdk`](https://github.com/tonia-router/rust-sdk) (`tag = "v0.4.4"`,
not crates.io).

Copyright (c) 2026 tonia inc. Apache 2.0 — commercial use allowed. Keep `NOTICE`
if you copy these examples.

| Example | TypeScript | Python | Rust |
| --- | --- | --- |
| Basic chat | [`typescript/01-basic-chat.ts`](typescript/01-basic-chat.ts) | [`python/01_basic_chat.py`](python/01_basic_chat.py) | [`rust/src/bin/01_basic_chat.rs`](rust/src/bin/01_basic_chat.rs) |
| Streaming | [`typescript/02-streaming.ts`](typescript/02-streaming.ts) | [`python/02_streaming.py`](python/02_streaming.py) | [`rust/src/bin/02_streaming.rs`](rust/src/bin/02_streaming.rs) |
| Catalogue + models | [`typescript/03-catalogue-and-models.ts`](typescript/03-catalogue-and-models.ts) | [`python/03_catalogue_and_models.py`](python/03_catalogue_and_models.py) | [`rust/src/bin/03_catalogue_and_models.rs`](rust/src/bin/03_catalogue_and_models.rs) |
| Policy block → portal redact | [`typescript/04-policy-block.ts`](typescript/04-policy-block.ts) | [`python/04_policy_block.py`](python/04_policy_block.py) | [`rust/src/bin/04_policy_block.rs`](rust/src/bin/04_policy_block.rs) |
| Agent block → portal Agent controls | [`typescript/13-agent-block.ts`](typescript/13-agent-block.ts) | [`python/13_agent_block.py`](python/13_agent_block.py) | [`rust/src/bin/13_agent_block.rs`](rust/src/bin/13_agent_block.rs) |
| Images (`/v1/images`, tenant `size`; prefers Flare) | [`typescript/05-images.ts`](typescript/05-images.ts) | [`python/05_images.py`](python/05_images.py) | [`rust/src/bin/05_images.rs`](rust/src/bin/05_images.rs) |
| Gemini image gen/edit (`/v1/interactions`) | [`typescript/06-gemini-interactions-image.ts`](typescript/06-gemini-interactions-image.ts) | [`python/06_gemini_interactions_image.py`](python/06_gemini_interactions_image.py) | [`rust/src/bin/06_gemini_interactions_image.rs`](rust/src/bin/06_gemini_interactions_image.rs) |
| Rate limit → follow `Retry-After` | [`typescript/07-rate-limit-retry.ts`](typescript/07-rate-limit-retry.ts) | [`python/07_rate_limit_retry.py`](python/07_rate_limit_retry.py) | [`rust/src/bin/07_rate_limit_retry.rs`](rust/src/bin/07_rate_limit_retry.rs) |
| LLM tools passthrough | [`typescript/08-tools-passthrough.ts`](typescript/08-tools-passthrough.ts) | [`python/08_tools_passthrough.py`](python/08_tools_passthrough.py) | [`rust/src/bin/08_tools_passthrough.rs`](rust/src/bin/08_tools_passthrough.rs) |
| SaaS integrator (history, usage, limits) | [`typescript/09-saas-integrator.ts`](typescript/09-saas-integrator.ts) | [`python/09_saas_integrator.py`](python/09_saas_integrator.py) | [`rust/src/bin/09_saas_integrator.rs`](rust/src/bin/09_saas_integrator.rs) |
| Audio speech / transcriptions (+ Gemini Interactions) | [`typescript/10-audio.ts`](typescript/10-audio.ts) | [`python/10_audio.py`](python/10_audio.py) | [`rust/src/bin/10_audio.rs`](rust/src/bin/10_audio.rs) |
| Embeddings (`/v1/embeddings`, tenant `input`) | [`typescript/11-embeddings.ts`](typescript/11-embeddings.ts) | [`python/11_embeddings.py`](python/11_embeddings.py) | [`rust/src/bin/11_embeddings.rs`](rust/src/bin/11_embeddings.rs) |
| Rerank (`/v1/rerank`, tenant `query` + `documents`) | [`typescript/12-rerank.ts`](typescript/12-rerank.ts) | [`python/12_rerank.py`](python/12_rerank.py) | [`rust/src/bin/12_rerank.rs`](rust/src/bin/12_rerank.rs) |
| Live / realtime (`wss /v1/realtime`, `gpt-live-1`, native PCM) | [`typescript/15-live-native.ts`](typescript/15-live-native.ts) | [`python/15_live_native.py`](python/15_live_native.py) | [`rust/src/bin/15_live_native.rs`](rust/src/bin/15_live_native.rs) |
| Native Live **mic** (DEV full duplex) | [`live-mic/`](live-mic/) — `python live-mic/serve.py` then http://127.0.0.1:8765 | Latency HUD + `python live-mic/measure.py` (DEV; `--prod` when ready) |
| Live STT (`gemini-3.5-transcribe-live`, PCM 16 kHz) | [`typescript/16-gemini-transcribe-live.ts`](typescript/16-gemini-transcribe-live.ts) | [`python/16_gemini_transcribe_live.py`](python/16_gemini_transcribe_live.py) | [`rust/src/bin/16_gemini_transcribe_live.rs`](rust/src/bin/16_gemini_transcribe_live.rs) |
| System One (`/v1/systemone`, Jev noul / choice / score) | [`typescript/17-systemone.ts`](typescript/17-systemone.ts) | [`python/17_systemone.py`](python/17_systemone.py) | [`rust/src/bin/17_systemone.rs`](rust/src/bin/17_systemone.rs) |

## Run locally (before packages are published)

```bash
# TypeScript — link the local SDK
cd ../typescript-sdk && npm install && npm run build
cd ../sdk-examples/typescript
npm install ../../typescript-sdk
npx tsx 01-basic-chat.ts

# Python — editable install
cd ..
pip install -e ../python-sdk
python python/01_basic_chat.py

# Rust — tonia-sdk 0.4.4 from GitHub (not crates.io)
cd rust
cargo run --bin 01_basic_chat
```

## Coding tools

Install the portable skill:

```bash
gh skill install tonia-router/skills tonia-sdk
```

In Cursor, copy the `tonia-sdk` folder (the directory that contains
`SKILL.md`) to `.cursor/skills/tonia-sdk/` (project) or
`~/.cursor/skills/tonia-sdk/` (user).
