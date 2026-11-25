"""Rerank on tenant `/v1/rerank`.

Send `model`, `query`, and `documents`. Do not POST lab `/v2/rerank`.
A rerank search is not a web search.

    export TONIA_API_KEY=tonia_sk_…
    python 12_rerank.py

Ask and clavarde do not list these ids. Use a portal API key.
"""

from __future__ import annotations

import json
import os

from tonia import Tonia


def _caps(item: dict[str, object]) -> list[str]:
    raw = item.get("capabilities")
    return [str(cap) for cap in raw] if isinstance(raw, list) else []


def _surface(item: dict[str, object]) -> dict[str, object]:
    raw = item.get("surface")
    return raw if isinstance(raw, dict) else {}


def is_rerank(item: dict[str, object]) -> bool:
    if _surface(item).get("family") == "rerank":
        return True
    if "rerank" in _caps(item):
        return True
    return "rerank" in str(item["id"]).lower()


with Tonia(
    api_key=os.environ["TONIA_API_KEY"],
    default_headers={
        "HTTP-Referer": "https://github.com/tonia-router/sdk-examples",
        "X-Tonia-Title": "sdk-examples",
    },
) as client:
    listed = client.models.list()
    model = next((item["id"] for item in listed["data"] if is_rerank(item)), None)
    if not model:
        raise SystemExit("no listed rerank on this key")
    body = client.rerank.create(
        model=model,
        query="bonjour",
        documents=["bonjour", "au revoir"],
    )
    ranked = body.get("results") or body.get("data") or []
    print(
        json.dumps(
            {"model": model, "result_count": len(ranked) if isinstance(ranked, list) else 0},
            indent=2,
        )
    )
