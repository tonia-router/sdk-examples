/**
 * Rerank on tenant `/v1/rerank`.
 *
 * Send `model`, `query`, and `documents`. Do not POST lab `/v2/rerank`.
 * A rerank search is not a web search.
 *
 *   export TONIA_API_KEY=tonia_sk_…
 *   npx tsx 12-rerank.ts
 *
 * The chat app never lists these ids. Use a portal API key.
 */
import { Tonia } from "@tonia-router/sdk";

function isRerank(item: { id: string; capabilities?: string[]; surface?: { family?: string } }): boolean {
  if (item.surface?.family === "rerank") return true;
  if (item.capabilities?.includes("rerank")) return true;
  return item.id.toLowerCase().includes("rerank");
}

const client = new Tonia({
  apiKey: process.env.TONIA_API_KEY,
  defaultHeaders: {
    "HTTP-Referer": "https://github.com/tonia-router/sdk-examples",
    "X-Tonia-Title": "sdk-examples",
  },
});

const { data } = await client.models.list();
const model = data.find(isRerank)?.id;
if (!model) {
  throw new Error("no listed rerank on this key");
}
const body = await client.rerank.create({
  model,
  query: "bonjour",
  documents: ["bonjour", "au revoir"],
});
const ranked =
  (body as { results?: unknown[]; data?: unknown[] }).results ??
  (body as { data?: unknown[] }).data ??
  [];
console.log(
  JSON.stringify(
    { model, result_count: Array.isArray(ranked) ? ranked.length : 0 },
    null,
    2,
  ),
);
