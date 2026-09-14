"""Native Live duplex on tonia wss /v1/realtime.

    export TONIA_API_KEY=tonia_sk_…
    # Hosted (keep :8443):
    export TONIA_BASE_URL=https://pass-dev.tonia.ca:8443
    python 15_live_native.py

PCM16 LE 24 kHz only. Recv output_audio.delta. Do not wait_turn,
input_text, or WAV. Example 14 stays cascaded text.
Reconnect is a new billed session. Ask / clavarde has no microphone.
"""

from __future__ import annotations

import json
import os
import struct

from tonia import Tonia

_RATE = 24_000
_MS = 100


def _pcm16_le_24k(ms: int = _MS) -> bytes:
    samples = _RATE * ms // 1000
    return struct.pack(f"<{samples}h", *([0] * samples))


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
    with client.realtime.connect(
        model="gpt-live-1",
        mode="native",
        transcripts=True,
    ) as session:
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
        session.send_audio_append(_pcm16_le_24k(), mime="audio/pcm")
        while True:
            event = session.recv(timeout=60.0)
            kind = str(event.get("type") or "")
            if kind == "output_audio.delta":
                print(
                    json.dumps(
                        {
                            "type": kind,
                            "session_id": event.get("session_id"),
                            "audio_b64_chars": len(str(event.get("audio") or "")),
                        },
                        indent=2,
                    )
                )
                break
            if kind in {"transcript.delta", "transcript.final", "delegation.created"}:
                continue
            raise SystemExit(f"unexpected native event: {kind}")
