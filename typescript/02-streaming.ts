/**
 * Streaming chat (SSE). Reads events as they arrive.
 *
 *   export TONIA_API_KEY=tonia_sk_…
 *   npx tsx 02-streaming.ts
 */
import { Tonia } from "@tonia-router/sdk";

const client = new Tonia({ apiKey: process.env.TONIA_API_KEY });

const { data } = await client.models.list();
if (!data[0]) {
  throw new Error("this key has no models; check the profile allowlist in the portal");
}

for await (const event of client.chat.completions.stream({
  model: data[0].id,
  messages: [{ role: "user", content: "Compte jusqu’à 5." }],
})) {
  if (event.data === "[DONE]") break;
  if (event.json) {
    process.stdout.write(JSON.stringify(event.json) + "\n");
  }
}
