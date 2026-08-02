# sdk-examples

Cookbook examples for the official tonia Pass SDKs.

Set `TONIA_API_KEY` in your environment. Use placeholder values in committed
files — never commit a live key.

| Example | TypeScript | Python |
| --- | --- | --- |
| Basic chat | [`typescript/01-basic-chat.ts`](typescript/01-basic-chat.ts) | [`python/01_basic_chat.py`](python/01_basic_chat.py) |
| Streaming | [`typescript/02-streaming.ts`](typescript/02-streaming.ts) | [`python/02_streaming.py`](python/02_streaming.py) |
| Catalogue + models | [`typescript/03-catalogue-and-models.ts`](typescript/03-catalogue-and-models.ts) | [`python/03_catalogue_and_models.py`](python/03_catalogue_and_models.py) |
| Conversation export | [`typescript/04-conversation-export.ts`](typescript/04-conversation-export.ts) | [`python/04_conversation_export.py`](python/04_conversation_export.py) |
| Policy block → portal redact | [`typescript/05-policy-block.ts`](typescript/05-policy-block.ts) | [`python/05_policy_block.py`](python/05_policy_block.py) |

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

Or in Cursor: **Settings → Rules → Add Rule → Remote Rule (GitHub)** with
`tonia-router/skills`.
