"""Embeddings on tenant `/v1/embeddings`.

Send `model` + `input`. Do not POST lab `/v2/embed` or chat completions.

    export TONIA_API_KEY=tonia_sk_…
    python 11_embeddings.py

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


def is_embeddings(item: dict[str, object]) -> bool:
    if _surface(item).get("family") == "embeddings":
        return True
    if "embeddings" in _caps(item):
        return True
    lowered = str(item["id"]).lower()
    return "embed" in lowered and "rerank" not in lowered


with Tonia(
    api_key=os.environ["TONIA_API_KEY"],
    default_headers={
        "HTTP-Referer": "https://github.com/tonia-router/sdk-examples",
        "X-Tonia-Title": "sdk-examples",
    },
) as client:
    listed = client.models.list()
    model = next((item["id"] for item in listed["data"] if is_embeddings(item)), None)
    if not model:
        raise SystemExit("no listed embeddings on this key")
    body = client.embeddings.create(model=model, input="Bonjour")
    vector = (body.get("data") or [{}])[0].get("embedding")
    print(
        json.dumps(
            {
                "model": model,
                "dimensions": len(vector) if isinstance(vector, list) else 0,
            },
            indent=2,
        )
    )
