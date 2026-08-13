"""Streaming chat (SSE). Do not buffer the full response.

    export TONIA_API_KEY=tonia_sk_…
    python 02_streaming.py
"""

from __future__ import annotations

import json
import os

from tonia import Tonia

with Tonia(api_key=os.environ["TONIA_API_KEY"]) as client:
    listed = client.models.list()
    ids = [model["id"] for model in listed["data"]]
    if not ids:
        raise SystemExit("empty allowlist — do not guess a model id")
    for event in client.chat.completions.stream(
        model=ids[0],
        messages=[{"role": "user", "content": "Compte jusqu’à 5."}],
    ):
        if event.data == "[DONE]":
            break
        if event.json is not None:
            print(json.dumps(event.json, ensure_ascii=False))
