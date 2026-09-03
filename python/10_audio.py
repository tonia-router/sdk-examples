"""A1 speech + transcription, and Gemini token audio on Interactions.

    export TONIA_API_KEY=tonia_sk_…
    python 10_audio.py

Sold A1 examples: mistral/voxtral-mini-tts-2603, openai/gpt-transcribe.
Gemini token TTS/STT uses interactions.create.
Workspace audio must be on (portal /dlp).
"""

from __future__ import annotations

import json
import os
import struct
import wave
from io import BytesIO

from tonia import Tonia

_BARE_FISH = frozenset({"s2.1-pro", "s2.1-pro-free"})


def _skip(model_id: str) -> bool:
    lowered = model_id.lower()
    if lowered in _BARE_FISH:
        return True
    return any(part in lowered for part in ("-latest", "vd-", "realtime"))


def _caps(item: dict[str, object]) -> list[str]:
    raw = item.get("capabilities")
    return [str(cap) for cap in raw] if isinstance(raw, list) else []


def _surface(item: dict[str, object]) -> dict[str, object]:
    raw = item.get("surface")
    return raw if isinstance(raw, dict) else {}


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

    tts = next(
        (
            item["id"]
            for item in rows
            if (
                _surface(item).get("path") == "/v1/audio/speech"
                or "audio_speech" in _caps(item)
            )
            and not item["id"].startswith("gemini/")
        ),
        None,
    )
    stt = next(
        (
            item["id"]
            for item in rows
            if (
                _surface(item).get("path") == "/v1/audio/transcriptions"
                or "audio_transcription" in _caps(item)
            )
            and not item["id"].startswith("gemini/")
        ),
        None,
    )
    gemini_audio = next(
        (
            item["id"]
            for item in rows
            if item["id"].startswith("gemini/")
            and _surface(item).get("family") in ("speech", "transcription")
        ),
        None,
    )
    if not tts and not stt and not gemini_audio:
        raise SystemExit("no listed audio on this key")

    spent: dict[str, object] = {}
    if tts:
        speech_voice = "" if tts.startswith("fish_") or "s2.1-pro" in tts else "alloy"
        speech = client.audio.speech.create(model=tts, input="Bonjour Tonia", voice=speech_voice)
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
