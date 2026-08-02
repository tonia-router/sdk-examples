/**
 * Streaming chat (SSE). Do not buffer the full response.
 *
 *   export TONIA_API_KEY=tonia_sk_…
 *   npx tsx 02-streaming.ts
 */
import { Tonia } from "@tonia/sdk";

const client = new Tonia({ apiKey: process.env.TONIA_API_KEY });

for await (const event of client.chat.completions.stream({
  model: "openai/gpt-4.1-mini",
  messages: [{ role: "user", content: "Compte jusqu’à 5." }],
})) {
  if (event.data === "[DONE]") break;
  if (event.json) {
    process.stdout.write(JSON.stringify(event.json) + "\n");
  }
}
