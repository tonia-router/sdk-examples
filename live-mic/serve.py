"""Full-duplex Live mic. Serves the UI and proxies tonia wss.

    python serve.py
    open http://127.0.0.1:8765

Paste a Workspace tonia_ key. Default Pass is pass.tonia.ca:8443.
The browser never talks to api.openai.com.
Reconnect is a new billed session.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path
from urllib.parse import urlencode, urlsplit, urlunsplit

from starlette.responses import FileResponse

log = logging.getLogger("live-mic")

from starlette.applications import Starlette
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 8765
DEFAULT_BASE = "https://pass.tonia.ca:8443"
REALTIME_PATH = "/v1/realtime"
LOCAL_DATA_PORT = "8444"
LOCAL_REALTIME_PORT = "8448"


def realtime_connect_url(base_url: str) -> str:
    parsed = urlsplit((base_url or DEFAULT_BASE).rstrip("/"))
    scheme = "wss" if parsed.scheme == "https" else "ws"
    hostname = parsed.hostname or ""
    port = parsed.port
    if hostname in {"127.0.0.1", "localhost"} and (
        port is None or str(port) == LOCAL_DATA_PORT
    ):
        netloc = f"{hostname}:{LOCAL_REALTIME_PORT}"
    elif port:
        netloc = f"{hostname}:{port}"
    else:
        netloc = hostname
    query = urlencode(
        {
            "provider": "openai",
            "model": "gpt-live-1",
            "mode": "native",
            "transcripts": "1",
        }
    )
    return f"{urlunsplit((scheme, netloc, REALTIME_PATH, '', ''))}?{query}"


def _upstream_error(exc: Exception) -> dict[str, object]:
    response = getattr(exc, "response", None)
    status = getattr(response, "status_code", None)
    raw = getattr(response, "body", None) or b""
    if isinstance(raw, bytes):
        text = raw.decode("utf-8", "replace")
    else:
        text = str(raw or "")
    code = ""
    try:
        parsed = json.loads(text) if text else {}
    except json.JSONDecodeError:
        parsed = {}
    if isinstance(parsed, dict):
        error = parsed.get("error")
        if isinstance(error, dict):
            code = str(error.get("code") or "").strip()
        code = code or str(parsed.get("code") or "").strip()
    if not code and status == 401:
        code = "missing_bearer"
    elif not code and status == 403:
        code = "realtime_edge_forbidden"
    elif not code and status == 429:
        code = "admission_rate_limited"
    elif not code:
        code = "realtime_plane_unreachable"
    message = {
        401: "key refused — check the tonia_ key and Live tab",
        400: code.replace("_", " "),
        403: "Pass refused this network or key",
        429: "rate limited — wait and retry",
    }.get(int(status or 0), str(exc)[:180])
    return {
        "status": status,
        "error": {
            "type": "invalid_request_error",
            "code": code,
            "message": message,
            "retryable": False,
        },
    }


def _static(name: str):
    async def _send(_request):
        path = ROOT / name
        media = "text/html" if path.suffix == ".html" else None
        return FileResponse(
            path,
            media_type=media,
            headers={"Cache-Control": "no-store"},
        )

    return _send


async def session_proxy(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        hello = json.loads(await websocket.receive_text())
    except Exception:
        await websocket.close(code=4400)
        return
    if not isinstance(hello, dict) or hello.get("type") != "hello":
        await websocket.close(code=4400)
        return
    api_key = str(hello.get("api_key") or "").strip()
    base_url = str(hello.get("base_url") or DEFAULT_BASE).strip() or DEFAULT_BASE
    if not api_key:
        await websocket.send_json(
            {"error": {"code": "missing_bearer", "type": "invalid_request_error"}}
        )
        await websocket.close(code=4401)
        return
    url = realtime_connect_url(base_url)
    try:
        import websockets
    except ImportError:
        await websocket.send_json(
            {"error": {"code": "realtime_plane_unreachable", "type": "invalid_request_error"}}
        )
        await websocket.close(code=1011)
        return
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        try:
            upstream = await websockets.connect(
                url, additional_headers=headers, open_timeout=15
            )
        except TypeError:
            upstream = await websockets.connect(
                url, extra_headers=headers, open_timeout=15
            )
    except Exception as exc:
        payload = _upstream_error(exc)
        log.warning(
            "upstream open failed status=%s code=%s",
            payload.get("status"),
            payload["error"]["code"],
        )
        await websocket.send_json({"error": payload["error"]})
        await websocket.close(code=1011)
        return

    t_connected = time.perf_counter()
    t_created: float | None = None
    first_audio_sent = False

    async def to_pass() -> None:
        try:
            while True:
                message = await websocket.receive_text()
                await upstream.send(message)
        except (WebSocketDisconnect, Exception):
            return

    async def from_pass() -> None:
        nonlocal first_audio_sent, t_created
        try:
            async for message in upstream:
                t_recv = time.perf_counter()
                if isinstance(message, bytes):
                    message = message.decode("utf-8")
                try:
                    event = json.loads(message)
                except json.JSONDecodeError:
                    await websocket.send_text(message)
                    continue
                if not isinstance(event, dict):
                    await websocket.send_text(message)
                    continue
                hop = max(0, int((time.perf_counter() - t_recv) * 1000))
                event["proxy_hop_ms"] = hop
                if event.get("type") == "session.created":
                    t_created = t_recv
                    event["handshake_ms"] = int((t_recv - t_connected) * 1000)
                if event.get("type") == "output_audio.delta" and event.get("audio"):
                    if not first_audio_sent:
                        first_audio_sent = True
                        origin = t_created if t_created is not None else t_connected
                        await websocket.send_json(
                            {
                                "type": "live.timing",
                                "handshake_ms": int(((t_created or t_recv) - t_connected) * 1000),
                                "path_first_audio_ms": int((t_recv - origin) * 1000),
                            }
                        )
                await websocket.send_json(event)
        except Exception:
            return

    try:
        await asyncio.wait(
            [
                asyncio.create_task(to_pass()),
                asyncio.create_task(from_pass()),
            ],
            return_when=asyncio.FIRST_COMPLETED,
        )
    finally:
        try:
            await upstream.close()
        except Exception:
            pass
        try:
            await websocket.close()
        except Exception:
            pass


app = Starlette(
    routes=[
        Route("/", _static("index.html")),
        Route("/index.html", _static("index.html")),
        Route("/app.js", _static("app.js")),
        Route("/styles.css", _static("styles.css")),
        Route("/pcm-capture-worklet.js", _static("pcm-capture-worklet.js")),
        WebSocketRoute("/session", session_proxy),
    ]
)


def main() -> None:
    import uvicorn

    print(f"open http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()
