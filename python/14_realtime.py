"""Cascaded Live text dry-run on tonia wss /v1/realtime.

    export TONIA_API_KEY=tonia_sk_…
    # Hosted (keep :8443):
    export TONIA_BASE_URL=https://pass.tonia.ca:8443
    python 14_realtime.py

First hop is openai / gpt-live-1 only. Ask / clavarde has no microphone.
Reconnect is a new billed session.
"""

from __future__ import annotations

import json
import os

from tonia import Tonia

base_url = os.environ.get("TONIA_BASE_URL") or os.environ.get("PASS_BASE_URL")

with Tonia(
    api_key=os.environ["TONIA_API_KEY"],
    base_url=base_url,
    default_headers={
        "HTTP-Referer": "https://github.com/tonia-router/sdk-examples",
        "X-Tonia-Title": "sdk-examples",
    },
) as client:
    listed = client.models.list()
    live = next(
        (
            item
            for item in listed["data"]
            if item["id"] in {"gpt-live-1", "openai/gpt-live-1"}
            or "realtime" in (item.get("capabilities") or [])
        ),
        None,
    )
    if live is None:
        raise SystemExit(
            "this key cannot see gpt-live-1; add it on the profile "
            "Temps réel / Live tab, then retry"
        )
    with client.realtime.connect(model="gpt-live-1") as session:
        print(
            json.dumps(
                {
                    "session_id": session.session_id,
                    "mode": session.mode,
                    "model": session.model,
                    "reconnect": session.reconnect,
                },
                indent=2,
            )
        )
        session.send_text("Reply with the single word ok.")
        event = session.wait_turn(timeout=60.0)
        print(json.dumps(event, indent=2, ensure_ascii=False))
