/**
 * Native Live duplex on tonia wss /v1/realtime.
 *
 *   export TONIA_API_KEY=tonia_sk_…
 *   # DEV (keep :8443):
 *   export TONIA_BASE_URL=https://pass-dev.tonia.ca:8443
 *   npx tsx 15-live-native.ts
 *
 * PCM16 LE 24 kHz only. Recv output_audio.delta. Do not waitTurn,
 * sendText, or WAV.
 * Reconnect is a new billed session. Ask / clavarde has no microphone.
 */
import { Tonia } from "@tonia-router/sdk";

const RATE = 24_000;
const MS = 100;

function pcm16Le24k(ms = MS): Uint8Array {
  const samples = (RATE * ms) / 1000;
  const out = new Uint8Array(samples * 2);
  return out;
}

const client = new Tonia({
  apiKey: process.env.TONIA_API_KEY,
  baseURL: process.env.TONIA_BASE_URL || process.env.PASS_BASE_URL,
  defaultHeaders: {
    "HTTP-Referer": "https://github.com/tonia-router/sdk-examples",
    "X-Tonia-Title": "sdk-examples",
  },
});

const { data } = await client.models.list();
const live = data.find(
  (item) =>
    item.id === "gpt-live-1" ||
    item.id === "openai/gpt-live-1" ||
    (Array.isArray(item.capabilities) && item.capabilities.includes("realtime")),
);
if (!live) {
  throw new Error(
    "this key cannot see gpt-live-1; add it on the profile Temps réel / Live tab, then retry",
  );
}

const session = await client.realtime.connect({
  model: "gpt-live-1",
  mode: "native",
  transcripts: true,
});
try {
  console.log(
    JSON.stringify(
      {
        session_id: session.sessionId,
        mode: session.mode,
        model: session.model,
        reconnect: session.reconnect,
      },
      null,
      2,
    ),
  );
  session.sendAudioAppend(pcm16Le24k(), "audio/pcm");
  while (true) {
    const event = await session.recv(60_000);
    const kind = typeof event.type === "string" ? event.type : "";
    if (kind === "output_audio.delta") {
      console.log(
        JSON.stringify(
          {
            type: kind,
            session_id: event.session_id,
            audio_b64_chars: String(event.audio ?? "").length,
          },
          null,
          2,
        ),
      );
      break;
    }
    if (
      kind === "transcript.delta" ||
      kind === "transcript.final" ||
      kind === "delegation.created"
    ) {
      continue;
    }
    throw new Error(`unexpected native event: ${kind}`);
  }
} finally {
  session.close();
}
