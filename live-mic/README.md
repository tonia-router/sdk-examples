# Live mic (DEV)

Small full-duplex voice page for **DEV**. Browser mic in, model audio out, on
tonia `wss /v1/realtime` (`mode=native`, PCM16 LE 24 kHz). Not Ask. Not lab
WebRTC.

```bash
cd /Users/flxpro/Desktop/Tonia
.venv/bin/python tonia-router/sdk-examples/live-mic/serve.py
# open http://127.0.0.1:8765
```

Paste a Workspace `tonia_` key that can see `gpt-live-1` (portal Temps réel /
Live). Leave the base URL as `https://pass-dev.tonia.ca:8443`.

The page talks only to this local server. The server opens tonia `wss` with
`Authorization: Bearer` — the key is not put on the public query string.
Reconnect is a new billed session.

Need: operator CIDR to reach `pass-dev.tonia.ca:8443`, and audio on for that
tenant. Chrome / Safari on `http://127.0.0.1` (secure context).

The page records the call locally while you talk. Stop downloads four files:
stereo mix (you left, model right), mic-only, model-only, and captions.
WAVs stay in the browser. Refresh the tab after pulling this change.

## Latency + choke

The page shows four clocks:

- **Reply** — your speech onset → first `output_audio.delta` (lab + WAN + Pass).
- **Pass hop** — Pass copy time on each audio delta (`pass_hop_ms`). Expect a
  few milliseconds. Hosted DEV/PROD only show this after that Pass build is
  promoted.
- **Queue** — playback backlog. A queue that keeps growing is choke.
- **Path** — handshake, then first audio after `session.created`.

Hosted check (bills a short Live session). Default is DEV. Use `--prod` only
after native is on PROD:

```bash
set -a && source PLANS/02-architecture/e2e/.env.dev && set +a
.venv/bin/python tonia-router/sdk-examples/live-mic/measure.py
# .venv/bin/python tonia-router/sdk-examples/live-mic/measure.py --prod
```

`verdict` is `ok`, `choke` (audio arrives slower than it plays), `pass_slow`
(Pass copy p95 ≥ 25 ms), or `fail`.
