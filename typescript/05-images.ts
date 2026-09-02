/**
 * Image generate on `/v1/images/generations`.
 *
 * Send the tenant dial (`1k` / `2k` / `4k`) or OpenAI `size`.
 * Pass maps each lab. Do not send `resolution` or `image_size`.
 *
 * Gemini image SKUs must use 06-gemini-interactions-image.ts instead.
 *
 *   export TONIA_API_KEY=tonia_sk_…
 *   npx tsx 05-images.ts
 */
import { Tonia } from "@tonia-router/sdk";

function isGeminiImage(id: string): boolean {
  return id.startsWith("gemini/") || id.startsWith("gemini-");
}

function isOpenAIImage(id: string): boolean {
  return id.startsWith("openai/") || /^gpt-image/i.test(id);
}

function isXaiImage(id: string): boolean {
  return id.startsWith("xai/") || /^grok-imagine-image/i.test(id);
}

function isMetaImage(id: string): boolean {
  return /^muse-image/i.test(id);
}

function isPathAImage(id: string): boolean {
  if (/turbo/i.test(id) || isGeminiImage(id)) return false;
  return isOpenAIImage(id) || isXaiImage(id) || isMetaImage(id);
}

const client = new Tonia({
  apiKey: process.env.TONIA_API_KEY,
  baseURL: process.env.TONIA_BASE_URL,
  defaultHeaders: {
    "HTTP-Referer": "https://github.com/tonia-router/sdk-examples",
    "X-Tonia-Title": "sdk-examples",
  },
});

const { data: models } = await client.models.list();
const pathA = models.map((item) => item.id).filter(isPathAImage);
const model =
  pathA.find(isMetaImage) ??
  pathA.find((id) => isXaiImage(id) && !/quality/i.test(id)) ??
  pathA.find(isXaiImage) ??
  pathA[0];
if (!model) {
  throw new Error("no image SKU for /v1/images on this key");
}

/** Tenant dial. Pass maps OpenAI `2k` to billed WxH. */
const size = "2k";

const image = (await client.images.generate({
  model,
  prompt: "Draw a red fox",
  n: 1,
  size,
})) as { data?: unknown[] };

console.log(
  JSON.stringify({
    model,
    size,
    image_count: Array.isArray(image.data) ? image.data.length : 0,
  }),
);
