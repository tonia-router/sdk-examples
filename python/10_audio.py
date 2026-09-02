"""A1 speech + transcription, and Gemini token audio on Interactions.

    export TONIA_API_KEY=tonia_sk_…
    python 10_audio.py

Sold A1 examples: mistral/voxtral-mini-tts-2603, openai/gpt-transcribe.
Never gpt-4o-mini-tts. Gemini token TTS/STT uses interactions.create.
Workspace audio must be on (portal /dlp).
"""

from __future__ import annotations

import json
import os
import struct
import wave
from io import BytesIO

from tonia import Tonia


def _skip(model_id: str) -> bool:
    lowered = model_id.lower()
    return any(part in lowered for part in ("latest", "vd-", "realtime", "mini-tts"))


def _tiny_wav() -> bytes:
    buf = BytesIO()
    with wave.open(buf, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(8000)
        out.writeframes(struct.pack("<64h", *([0] * 64)))
    return buf.getvalue()


with Tonia(
    api_key=os.environ["TONIA_API_KEY"],
    default_headers={
        "HTTP-Referer": "https://github.com/tonia-router/sdk-examples",
        "X-Tonia-Title": "sdk-examples",
    },
) as client:
    listed = client.models.list()
    rows = [item for item in listed["data"] if not _skip(item["id"])]
    ids = [item["id"] for item in rows]

    def caps(item: dict[str, object]) -> list[str]:
        raw = item.get("capabilities")
        return [str(cap) for cap in raw] if isinstance(raw, list) else []

    tts = next(
        (
            item["id"]
            for item in rows
            if "audio_speech" in caps(item)
            and not item["id"].startswith("gemini/")
        ),
        next(
            (
                model_id
                for model_id in ids
                if "tts" in model_id.lower() and "gemini" not in model_id.lower()
            ),
            None,
        ),
    )
    stt = next(
        (
            item["id"]
            for item in rows
            if "audio_transcription" in caps(item)
            and not item["id"].startswith("gemini/")
        ),
        next(
            (
                model_id
                for model_id in ids
                if any(part in model_id.lower() for part in ("transcribe", "whisper", "asr"))
                and "tts" not in model_id.lower()
                and "gemini" not in model_id.lower()
            ),
            None,
        ),
    )
    gemini_audio = next(
        (
            model_id
            for model_id in ids
            if model_id.startswith("gemini/")
            and ("tts" in model_id.lower() or "transcribe" in model_id.lower())
        ),
        None,
    )
    if not tts and not stt and not gemini_audio:
        raise SystemExit("no listed audio on this key")

    spent: dict[str, object] = {}
    if tts:
        speech = client.audio.speech.create(model=tts, input="Bonjour Tonia", voice="alloy")
        spent["speech"] = {
            "model": tts,
            "kind": "bytes" if isinstance(speech, (bytes, bytearray)) else "json",
        }
    if stt:
        transcript = client.audio.transcriptions.create(
            model=stt,
            file=_tiny_wav(),
            filename="clip.wav",
        )
        spent["transcription"] = {"model": stt, "has_text": isinstance(transcript, dict)}
    if gemini_audio:
        client.interactions.create(model=gemini_audio, input="Bonjour", stream=False)
        spent["gemini_interactions"] = {"model": gemini_audio}
    print(json.dumps(spent, indent=2))
