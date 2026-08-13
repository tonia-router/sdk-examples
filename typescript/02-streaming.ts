/**
 * Streaming chat (SSE). Do not buffer the full response.
 *
 *   export TONIA_API_KEY=tonia_sk_…
 *   npx tsx 02-streaming.ts
 */
import { Tonia } from "@tonia/sdk";

const client = new Tonia({ apiKey: process.env.TONIA_API_KEY });

const { data } = await client.models.list();
if (!data[0]) {
  throw new Error("empty allowlist — do not guess a model id");
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
