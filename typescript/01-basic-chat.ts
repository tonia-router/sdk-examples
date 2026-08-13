/**
 * Basic chat with the official @tonia-router/sdk client.
 *
 *   export TONIA_API_KEY=tonia_sk_…
 *   npx tsx 01-basic-chat.ts
 */
import { Tonia } from "@tonia-router/sdk";

const client = new Tonia({
  apiKey: process.env.TONIA_API_KEY,
  defaultHeaders: {
    "HTTP-Referer": "https://github.com/tonia-router/sdk-examples",
    "X-Tonia-Title": "sdk-examples",
  },
});

const { data } = await client.models.list();
if (!data[0]) {
  throw new Error("this key has no models; check the profile allowlist in the portal");
}

const completion = await client.chat.completions.create({
  model: data[0].id,
  messages: [{ role: "user", content: "Bonjour — une phrase courte." }],
});

console.log(JSON.stringify(completion, null, 2));
