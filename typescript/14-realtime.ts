/**
 * Cascaded Live text dry-run on tonia wss /v1/realtime.
 *
 *   export TONIA_API_KEY=tonia_sk_…
 *   # DEV (keep :8443):
 *   export TONIA_BASE_URL=https://pass-dev.tonia.ca:8443
 *   npx tsx 14-realtime.ts
 *
 * First hop is openai / gpt-live-1 only. Ask / clavarde has no microphone.
 * Reconnect is a new billed session.
 */
import { Tonia } from "@tonia-router/sdk";

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

const session = await client.realtime.connect({ model: "gpt-live-1" });
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
  session.sendText("Reply with the single word ok.");
  const event = await session.waitTurn(60_000);
  console.log(JSON.stringify(event, null, 2));
} finally {
  session.close();
}
