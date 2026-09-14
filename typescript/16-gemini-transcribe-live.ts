/**
 * Live STT on tonia wss /v1/realtime (gemini-3.5-transcribe-live).
 *
 *   export TONIA_API_KEY=tonia_sk_…
 *   # DEV (keep :8443):
 *   export TONIA_BASE_URL=https://pass-dev.tonia.ca:8443
 *   npx tsx 16-gemini-transcribe-live.ts
 *
 * PCM16 LE 16 kHz only. Recv transcript.delta / transcript.final.
 * No output_audio, sendText, or WAV. Example 15 stays gpt-live-1 duplex.
 * Reconnect is a new billed session. Ask / clavarde has no microphone.
 */
import { Tonia } from "@tonia-router/sdk";

const RATE = 16_000;
const MS = 80;
const LIVE = "gemini-3.5-transcribe-live";

function pcm16Le16k(ms = MS): Uint8Array {
  const samples = (RATE * ms) / 1000;
  return new Uint8Array(samples * 2);
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
  (item) => item.id === LIVE || item.id === `gemini/${LIVE}`,
);
if (!live) {
  throw new Error(
    "this key cannot see gemini-3.5-transcribe-live; add it on the profile Temps réel / Live tab, then retry",
  );
}

const pcm = pcm16Le16k();
const session = await client.realtime.connect({
  provider: "gemini",
  model: LIVE,
  mode: "native",
  transcripts: true,
});
console.log(
  JSON.stringify(
    {
      session_id: session.sessionId,
      mode: session.mode,
      model: session.model,
    },
    null,
    2,
  ),
);
for (let i = 0; i < 8; i += 1) {
  session.sendAudioAppend(pcm, "audio/pcm;rate=16000");
  await new Promise((resolve) => setTimeout(resolve, 30));
}
await new Promise((resolve) => setTimeout(resolve, 400));
session.sendAudioCommit(undefined, "audio/pcm;rate=16000");
const event = await session.recv(60_000);
console.log(JSON.stringify(event, null, 2));
session.close();
