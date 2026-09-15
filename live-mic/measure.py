"""Native Live latency + choke check. tonia wss only.

    export TONIA_API_KEY=tonia_sk_…
    python measure.py
    python measure.py --dev

Needs TONIA_API_KEY. Do not print the key.
Reconnect is a new billed session.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from serve import DEFAULT_BASE, realtime_connect_url  # noqa: E402

RATE = 24_000
CHUNK_MS = 100
PROD_BASE = "https://pass.tonia.ca:8443"
DEV_BASE = "https://pass-dev.tonia.ca:8443"
# Pass copy should stay a couple of milliseconds. 25ms p95 is already fat.
PASS_HOP_P95_LIMIT_MS = 25
# Audio arriving more than this behind its own duration is a choke.
BEHIND_LIMIT_S = 1.25
MIN_AUDIO_S = 0.3


def _pcm16_le_24k(ms: int = CHUNK_MS) -> str:
    samples = RATE * ms // 1000
    return base64.b64encode(b"\x00\x00" * samples).decode("ascii")


def _pcm_s(audio_b64: str) -> float:
    raw = base64.b64decode(audio_b64)
    even = len(raw) - (len(raw) % 2)
    return (even / 2) / float(RATE)


def _pct(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = (p / 100.0) * (len(ordered) - 1)
    lo = int(rank)
    hi = min(len(ordered) - 1, lo + 1)
    frac = rank - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def verdict(report: dict[str, Any]) -> str:
    if report.get("error"):
        return "fail"
    if report.get("first_output_ms") is None:
        return "fail"
    audio_s = float(report.get("audio_s") or 0)
    behind_s = float(report.get("behind_s") or 0)
    if audio_s >= MIN_AUDIO_S and behind_s > BEHIND_LIMIT_S:
        return "choke"
    hops = [float(v) for v in (report.get("pass_hop_ms") or [])]
    hop_p95 = _pct(hops, 95) if hops else None
    if hop_p95 is not None and hop_p95 >= PASS_HOP_P95_LIMIT_MS:
        return "pass_slow"
    return "ok"


def _bearer() -> str:
    return (os.environ.get("TONIA_API_KEY") or "").strip()


def _error_code(payload: dict[str, Any]) -> str | None:
    error = payload.get("error")
    if isinstance(error, dict):
        code = str(error.get("code") or "").strip()
        if code:
            return code
    if payload.get("type") == "error":
        return str(payload.get("code") or "realtime_error")
    return None


async def _run(*, base_url: str, seconds: float, timeout: float) -> dict[str, Any]:
    import websockets

    bearer = _bearer()
    url = realtime_connect_url(base_url)
    fleet = "prod" if "pass.tonia.ca" in url and "pass-dev" not in url else "dev"
    if "127.0.0.1" in url or "localhost" in url:
        fleet = "local"
    report: dict[str, Any] = {
        "fleet": fleet,
        "base": urlsplit(base_url).netloc,
        "seconds": seconds,
        "handshake_ms": None,
        "first_output_ms": None,
        "first_transcript_ms": None,
        "deltas": 0,
        "audio_s": 0.0,
        "wall_after_first_s": None,
        "behind_s": None,
        "interarrival_p50_ms": None,
        "interarrival_p95_ms": None,
        "pass_hop_ms": [],
        "pass_hop_p50_ms": None,
        "pass_hop_p95_ms": None,
        "error": None,
    }
    if not bearer:
        report["error"] = "missing_bearer"
        return report
    headers = {"Authorization": f"Bearer {bearer}"}
    connect_kwargs: dict[str, Any] = {"open_timeout": 15}
    t_open = time.perf_counter()
    try:
        try:
            connect = websockets.connect(
                url, additional_headers=headers, **connect_kwargs
            )
        except TypeError:
            connect = websockets.connect(url, extra_headers=headers, **connect_kwargs)
    except Exception as exc:  # noqa: BLE001 — typed report, no traceback to stdout
        report["error"] = f"realtime_plane_unreachable:{type(exc).__name__}"
        return report
    arrivals: list[float] = []
    hops: list[float] = []
    audio_s = 0.0
    t_created = None
    t_first_audio = None
    t_last_audio = None
    try:
        async with connect as ws:
            raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
            created = json.loads(raw)
            t_created = time.perf_counter()
            report["handshake_ms"] = int((t_created - t_open) * 1000)
            if not isinstance(created, dict) or created.get("type") != "session.created":
                report["error"] = _error_code(created) or "realtime_handshake_invalid"
                return report
            deadline = t_created + seconds
            chunk = json.dumps(
                {
                    "type": "input_audio.append",
                    "audio": _pcm16_le_24k(),
                    "mime": "audio/pcm",
                }
            )
            next_send = t_created

            async def pump_in() -> None:
                nonlocal next_send
                while time.perf_counter() < deadline:
                    now = time.perf_counter()
                    if now >= next_send:
                        await ws.send(chunk)
                        next_send += CHUNK_MS / 1000.0
                    await asyncio.sleep(0.02)

            async def pump_out() -> None:
                nonlocal audio_s, t_first_audio, t_last_audio
                while time.perf_counter() < deadline:
                    remaining = deadline - time.perf_counter()
                    if remaining <= 0:
                        return
                    raw_event = await asyncio.wait_for(ws.recv(), timeout=remaining)
                    event = json.loads(raw_event)
                    if not isinstance(event, dict):
                        continue
                    err = _error_code(event)
                    if err:
                        report["error"] = err
                        return
                    kind = str(event.get("type") or "")
                    now = time.perf_counter()
                    if kind == "output_audio.delta" and event.get("audio"):
                        if t_first_audio is None and t_created is not None:
                            t_first_audio = now
                            report["first_output_ms"] = int((now - t_created) * 1000)
                        arrivals.append(now)
                        t_last_audio = now
                        audio_s += _pcm_s(str(event.get("audio") or ""))
                        hop = event.get("pass_hop_ms")
                        if hop is not None:
                            hops.append(float(hop))
                        report["deltas"] += 1
                    elif (
                        kind in {"transcript.delta", "transcript.final"}
                        and event.get("text")
                        and report["first_transcript_ms"] is None
                        and t_created is not None
                    ):
                        report["first_transcript_ms"] = int((now - t_created) * 1000)

            await asyncio.gather(pump_in(), pump_out())
    except TimeoutError:
        if report["error"] is None and report["first_output_ms"] is None:
            report["error"] = "realtime_probe_timeout"
    except Exception as exc:  # noqa: BLE001
        if report["error"] is None:
            report["error"] = f"realtime_plane_unreachable:{type(exc).__name__}"
    report["audio_s"] = round(audio_s, 3)
    if t_first_audio is not None and t_last_audio is not None:
        wall = max(0.0, t_last_audio - t_first_audio)
        report["wall_after_first_s"] = round(wall, 3)
        report["behind_s"] = round(wall - audio_s, 3)
    gaps = [
        (arrivals[i] - arrivals[i - 1]) * 1000
        for i in range(1, len(arrivals))
        if arrivals[i] >= arrivals[i - 1]
    ]
    report["interarrival_p50_ms"] = _round( _pct(gaps, 50) )
    report["interarrival_p95_ms"] = _round( _pct(gaps, 95) )
    report["pass_hop_ms"] = [int(v) for v in hops]
    report["pass_hop_p50_ms"] = _round(_pct(hops, 50))
    report["pass_hop_p95_ms"] = _round(_pct(hops, 95))
    report["verdict"] = verdict(report)
    return report


def _round(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 1)


def _self_check() -> int:
    ok = verdict(
        {
            "first_output_ms": 420,
            "audio_s": 2.0,
            "behind_s": 0.1,
            "pass_hop_ms": [0, 1, 1],
        }
    )
    choke = verdict(
        {
            "first_output_ms": 400,
            "audio_s": 2.0,
            "behind_s": 2.4,
            "pass_hop_ms": [1],
        }
    )
    slow = verdict(
        {
            "first_output_ms": 400,
            "audio_s": 2.0,
            "behind_s": 0.1,
            "pass_hop_ms": [40, 40, 40],
        }
    )
    failed = verdict({"error": "missing_bearer"})
    assert ok == "ok", ok
    assert choke == "choke", choke
    assert slow == "pass_slow", slow
    assert failed == "fail", failed
    print("SELF_CHECK_OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Native Live latency + choke check")
    parser.add_argument("--dev", action="store_true", help="pass-dev.tonia.ca")
    parser.add_argument("--prod", action="store_true", help="pass.tonia.ca (default)")
    parser.add_argument("--base-url", default="", help="Override Pass HTTPS base")
    parser.add_argument("--seconds", type=float, default=12.0)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        return _self_check()
    if args.dev and args.prod:
        print("refuse: --dev and --prod together", file=sys.stderr)
        return 1
    base = args.base_url.strip() or (DEV_BASE if args.dev else PROD_BASE)
    if args.prod and "pass-dev" in base:
        print("refuse: --prod with a DEV base", file=sys.stderr)
        return 1
    report = asyncio.run(_run(base_url=base, seconds=args.seconds, timeout=args.timeout))
    print(json.dumps(report, indent=2))
    kind = report.get("verdict") or verdict(report)
    if kind == "ok":
        return 0
    if kind in {"choke", "pass_slow"}:
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
