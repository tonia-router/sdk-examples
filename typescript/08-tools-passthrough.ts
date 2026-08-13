/**
 * Pass LLM tools through chat.completions. The SDK does not run a tool loop.
 *
 *   export TONIA_API_KEY=tonia_sk_…
 *   npx tsx 08-tools-passthrough.ts
 */
import { Tonia } from "@tonia/sdk";

const client = new Tonia({ apiKey: process.env.TONIA_API_KEY });

const { data } = await client.models.list();
if (!data[0]) {
  throw new Error("empty allowlist — do not guess a model id");
}
const completion = await client.chat.completions.create({
  model: data[0].id,
  messages: [{ role: "user", content: "Weather in Montréal?" }],
  tools: [
    {
      type: "function",
      function: {
        name: "get_weather",
        description: "Weather for a city",
        parameters: {
          type: "object",
          properties: { city: { type: "string" } },
          required: ["city"],
        },
      },
    },
  ],
});

console.log(JSON.stringify(completion, null, 2));
