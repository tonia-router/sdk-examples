"""Live STT on tonia wss /v1/realtime (gemini-3.5-transcribe-live).

    export TONIA_API_KEY=tonia_sk_…
    # Hosted (keep :8443):
    export TONIA_BASE_URL=https://pass-dev.tonia.ca:8443
    python 16_gemini_transcribe_live.py

PCM16 LE 16 kHz only. Recv transcript.delta / transcript.final.
No output_audio, input_text, or WAV. Example 15 stays gpt-live-1 duplex.
Reconnect is a new billed session. Ask / clavarde has no microphone.
"""

from __future__ import annotations

import json
import os
import struct
import time

from tonia import Tonia

_RATE = 16_000
_MS = 80
_LIVE = "gemini-3.5-transcribe-live"


def _pcm16_le_16k(ms: int = _MS) -> bytes:
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
            if item["id"] in {_LIVE, f"gemini/{_LIVE}"}
        ),
        None,
    )
    if live is None:
        raise SystemExit(
            "this key cannot see gemini-3.5-transcribe-live; add it on the "
            "profile Temps réel / Live tab, then retry"
        )
    pcm = _pcm16_le_16k()
    with client.realtime.connect(
        provider="gemini",
        model=_LIVE,
        mode="native",
        transcripts=True,
    ) as session:
        print(
            json.dumps(
                {
                    "session_id": session.session_id,
                    "mode": session.mode,
                    "model": session.model,
                },
                indent=2,
            )
        )
        for _ in range(8):
            session.send_audio_append(pcm, mime="audio/pcm;rate=16000")
            time.sleep(0.03)
        time.sleep(0.4)
        session.send_audio_commit(mime="audio/pcm;rate=16000")
        event = session.recv(timeout=60.0)
        print(json.dumps(event, indent=2, ensure_ascii=False))
