# sdk-examples

Cookbook examples for the official tonia Pass SDKs.

Set `TONIA_API_KEY` in your environment. Use placeholder values in committed
files — never commit a live key. Examples call `models.list()` and pick an
id from that allowlist — they do not hardcode a SKU.

Runtime: Python 3.11+ and Node.js 22+ (same floors as the official SDKs).

Copyright (c) 2026 tonia inc.. Apache 2.0 — commercial use allowed. Keep `NOTICE`
if you copy these examples.

| Example | TypeScript | Python |
| --- | --- | --- |
| Basic chat | [`typescript/01-basic-chat.ts`](typescript/01-basic-chat.ts) | [`python/01_basic_chat.py`](python/01_basic_chat.py) |
| Streaming | [`typescript/02-streaming.ts`](typescript/02-streaming.ts) | [`python/02_streaming.py`](python/02_streaming.py) |
| Catalogue + models | [`typescript/03-catalogue-and-models.ts`](typescript/03-catalogue-and-models.ts) | [`python/03_catalogue_and_models.py`](python/03_catalogue_and_models.py) |
| Policy block → portal redact | [`typescript/04-policy-block.ts`](typescript/04-policy-block.ts) | [`python/04_policy_block.py`](python/04_policy_block.py) |
| Images (`/v1/images`) | [`typescript/05-images.ts`](typescript/05-images.ts) | [`python/05_images.py`](python/05_images.py) |
| Gemini image gen/edit (`/v1/interactions`) | [`typescript/06-gemini-interactions-image.ts`](typescript/06-gemini-interactions-image.ts) | [`python/06_gemini_interactions_image.py`](python/06_gemini_interactions_image.py) |
| Rate limit → honor `Retry-After` | [`typescript/07-rate-limit-retry.ts`](typescript/07-rate-limit-retry.ts) | [`python/07_rate_limit_retry.py`](python/07_rate_limit_retry.py) |
| LLM tools passthrough | [`typescript/08-tools-passthrough.ts`](typescript/08-tools-passthrough.ts) | [`python/08_tools_passthrough.py`](python/08_tools_passthrough.py) |
| SaaS integrator (history, usage, limits) | [`typescript/09-saas-integrator.ts`](typescript/09-saas-integrator.ts) | [`python/09_saas_integrator.py`](python/09_saas_integrator.py) |

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
```

## Coding agents

Install the portable skill:

```bash
gh skill install tonia-router/skills tonia-sdk
```

Or in Cursor: copy the `tonia-sdk` folder (the directory that contains
`SKILL.md`) to `.cursor/skills/tonia-sdk/` (project) or
`~/.cursor/skills/tonia-sdk/` (user). That is an Agent Skill, not a
Cursor Rule.
