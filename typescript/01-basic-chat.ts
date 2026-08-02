/**
 * Basic chat with the official @tonia/sdk client.
 *
 *   export TONIA_API_KEY=tonia_sk_…
 *   npx tsx 01-basic-chat.ts
 */
import { Tonia } from "@tonia/sdk";

const client = new Tonia({
  apiKey: process.env.TONIA_API_KEY,
  defaultHeaders: {
    "HTTP-Referer": "https://github.com/tonia-router/sdk-examples",
    "X-Tonia-Title": "sdk-examples",
  },
});

const completion = await client.chat.completions.create({
  model: "openai/gpt-4.1-mini",
  messages: [{ role: "user", content: "Bonjour — une phrase courte." }],
});

console.log(JSON.stringify(completion, null, 2));
