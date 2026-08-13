/**
 * Path A image generate (openai / xAI / StepFun).
 *
 * Gemini image SKUs must use 06-gemini-interactions-image.ts instead.
 *
 *   export TONIA_API_KEY=tonia_sk_…
 *   npx tsx 05-images-path-a.ts
 */
import { Tonia } from "@tonia/sdk";

const client = new Tonia({
  apiKey: process.env.TONIA_API_KEY,
  defaultHeaders: {
    "HTTP-Referer": "https://github.com/tonia-router/sdk-examples",
    "X-Tonia-Title": "sdk-examples",
  },
});

const { data: models } = await client.models.list();
const model = models.find(
  (item) => /^(openai|xai|stepfun)\//.test(item.id) && /image/i.test(item.id),
)?.id;
if (!model) {
  throw new Error("no Path A image SKU on this key");
}

const image = (await client.images.generate({
  model,
  prompt: "Draw a red fox",
  n: 1,
})) as { data?: unknown[] };

console.log(JSON.stringify({ image_count: Array.isArray(image.data) ? image.data.length : 0 }));
