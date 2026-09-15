# Live mic

Full-duplex voice page on tonia `wss /v1/realtime` (`mode=native`, PCM16 LE
24 kHz). Browser mic in, model audio out. Not lab WebRTC.

```bash
cd live-mic
pip install starlette uvicorn websockets
python serve.py
# open http://127.0.0.1:8765
```

Paste a Workspace `tonia_` key that can see `gpt-live-1` (portal → Live).
Default Pass is `https://pass.tonia.ca:8443`. Hosted DEV is
`https://pass-dev.tonia.ca:8443` if your key is on that fleet.

The page talks only to this local server. The server opens tonia `wss` with
`Authorization: Bearer` — the key is not put on the query string. Reconnect
is a new billed session.

Chrome or Safari on `http://127.0.0.1` (secure context). Stop downloads a
stereo mix (you left, model right), mic-only, model-only, and captions.
WAVs stay in the browser. Recordings under `takes/` are local only and are
gitignored.

## Latency + choke

The page shows four clocks:

- **Reply** — your speech onset → first `output_audio.delta`
- **Pass hop** — Pass copy time on each audio delta (`pass_hop_ms`)
- **Queue** — playback backlog. A queue that keeps growing is choke
- **Path** — handshake, then first audio after `session.created`

CLI check (bills a short Live session). Uses `TONIA_API_KEY`. Default is
production:

```bash
export TONIA_API_KEY=tonia_sk_…
python measure.py
# python measure.py --dev
```

`verdict` is `ok`, `choke` (audio arrives slower than it plays), `pass_slow`
(Pass copy p95 ≥ 25 ms), or `fail`.
