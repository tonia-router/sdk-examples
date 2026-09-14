/**
 * Embeddings on tenant `/v1/embeddings`.
 *
 * Send `model` + `input`. Do not POST lab `/v2/embed` or chat completions.
 *
 *   export TONIA_API_KEY=tonia_sk_…
 *   npx tsx 11-embeddings.ts
 *
 * The chat app never lists these ids. Use a portal API key.
 */
import { Tonia } from "@tonia-router/sdk";

function isEmbeddings(item: { id: string; capabilities?: string[]; surface?: { family?: string } }): boolean {
  if (item.surface?.family === "embeddings") return true;
  if (item.capabilities?.includes("embeddings")) return true;
  const lowered = item.id.toLowerCase();
  return lowered.includes("embed") && !lowered.includes("rerank");
}

const client = new Tonia({
  apiKey: process.env.TONIA_API_KEY,
  defaultHeaders: {
    "HTTP-Referer": "https://github.com/tonia-router/sdk-examples",
    "X-Tonia-Title": "sdk-examples",
  },
});

const { data } = await client.models.list();
const model = data.find(isEmbeddings)?.id;
if (!model) {
  throw new Error("no listed embeddings on this key");
}
const body = await client.embeddings.create({ model, input: "Bonjour" });
const vector = (body as { data?: Array<{ embedding?: unknown[] }> }).data?.[0]?.embedding;
console.log(
  JSON.stringify(
    {
      model,
      dimensions: Array.isArray(vector) ? vector.length : 0,
    },
    null,
    2,
  ),
);
