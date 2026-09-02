/**
 * A1 speech + transcription, and Gemini token audio on Interactions.
 *
 *   export TONIA_API_KEY=tonia_sk_…
 *   npx tsx 10-audio.ts
 *
 * Sold A1 examples: mistral/voxtral-mini-tts-2603, openai/gpt-transcribe.
 * Never gpt-4o-mini-tts. Gemini token TTS/STT uses interactions.create.
 * Workspace audio must be on (portal /dlp).
 */
import { Tonia } from "@tonia-router/sdk";

function skip(id: string): boolean {
  return /latest|vd-|realtime|mini-tts/i.test(id);
}

function tinyWav(): Uint8Array {
  return Uint8Array.from([
    0x52, 0x49, 0x46, 0x46, 0x24, 0x00, 0x00, 0x00, 0x57, 0x41, 0x56, 0x45,
    0x66, 0x6d, 0x74, 0x20, 0x10, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00,
    0x40, 0x1f, 0x00, 0x00, 0x80, 0x3e, 0x00, 0x00, 0x02, 0x00, 0x10, 0x00,
    0x64, 0x61, 0x74, 0x61, 0x00, 0x00, 0x00, 0x00,
  ]);
}

const client = new Tonia({
  apiKey: process.env.TONIA_API_KEY,
  defaultHeaders: {
    "HTTP-Referer": "https://github.com/tonia-router/sdk-examples",
    "X-Tonia-Title": "sdk-examples",
  },
});

const { data } = await client.models.list();
const rows = data.filter((item) => !skip(item.id));
const ids = rows.map((item) => item.id);
const caps = (item: (typeof rows)[number]) => item.capabilities ?? [];

const tts =
  rows.find((item) => caps(item).includes("audio_speech") && !item.id.startsWith("gemini/"))
    ?.id ??
  ids.find((id) => /tts/i.test(id) && !/gemini/i.test(id));
const stt =
  rows.find(
    (item) => caps(item).includes("audio_transcription") && !item.id.startsWith("gemini/"),
  )?.id ??
  ids.find(
    (id) =>
      (/transcribe|whisper|asr/i.test(id) && !/tts/i.test(id) && !/gemini/i.test(id)),
  );
const geminiAudio = ids.find(
  (id) => id.startsWith("gemini/") && (/tts/i.test(id) || /transcribe/i.test(id)),
);

if (!tts && !stt && !geminiAudio) {
  throw new Error("no listed audio on this key");
}

const spent: Record<string, unknown> = {};
if (tts) {
  const speech = await client.audio.speech.create({
    model: tts,
    input: "Bonjour Tonia",
    voice: "alloy",
  });
  spent.speech = {
    model: tts,
    kind: speech instanceof Uint8Array ? "bytes" : "json",
  };
}
if (stt) {
  const transcript = await client.audio.transcriptions.create({
    model: stt,
    file: tinyWav(),
    filename: "clip.wav",
  });
  spent.transcription = { model: stt, has_text: Boolean(transcript && typeof transcript === "object") };
}
if (geminiAudio) {
  await client.interactions.create({
    model: geminiAudio,
    input: "Bonjour",
    stream: false,
  });
  spent.gemini_interactions = { model: geminiAudio };
}
console.log(JSON.stringify(spent, null, 2));
