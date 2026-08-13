"""Streaming chat (SSE). Reads events as they arrive.

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
        raise SystemExit("this key has no models; check the profile allowlist in the portal")
    for event in client.chat.completions.stream(
        model=ids[0],
        messages=[{"role": "user", "content": "Compte jusqu’à 5."}],
    ):
        if event.data == "[DONE]":
            break
        if event.json is not None:
            print(json.dumps(event.json, ensure_ascii=False))
