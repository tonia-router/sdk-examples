/**
 * Gemini image generate + edit on `/v1/interactions`.
 *
 *   export TONIA_API_KEY=tonia_sk_…
 *   npx tsx 06-gemini-interactions-image.ts
 */
import { InvalidRequestError, Tonia } from "@tonia-router/sdk";

type ImagePart = { type?: unknown; mime_type?: unknown; data?: unknown };

function outputImages(body: unknown): ImagePart[] {
  if (!body || typeof body !== "object") return [];
  const root = body as { interaction?: unknown; steps?: unknown };
  const interaction =
    root.interaction && typeof root.interaction === "object"
      ? (root.interaction as { steps?: unknown })
      : root;
  const steps = Array.isArray(interaction.steps) ? interaction.steps : [];
  const out: ImagePart[] = [];
  for (const step of steps) {
    if (!step || typeof step !== "object") continue;
    const rec = step as { type?: unknown; content?: unknown };
    if (rec.type !== "model_output" || !Array.isArray(rec.content)) continue;
    for (const part of rec.content) {
      if (!part || typeof part !== "object") continue;
      const p = part as ImagePart;
      if (typeof p.data !== "string" || !p.data) continue;
      const mime = typeof p.mime_type === "string" ? p.mime_type : "";
      if (p.type === "image" || mime.startsWith("image/")) out.push(p);
    }
  }
  return out;
}

const client = new Tonia({
  apiKey: process.env.TONIA_API_KEY,
  defaultHeaders: {
    "HTTP-Referer": "https://github.com/tonia-router/sdk-examples",
    "X-Tonia-Title": "sdk-examples",
  },
});

const { data: listed } = await client.models.list();
const GEMINI_IMAGE = listed.find(
  (item) => item.id.startsWith("gemini/") && /image/i.test(item.id),
)?.id;
if (!GEMINI_IMAGE) {
  throw new Error("no Gemini image SKU on this key");
}

try {
  await client.images.generate({ model: GEMINI_IMAGE, prompt: "Draw a red fox" });
  throw new Error("expected provider_requires_surface on /v1/images");
} catch (err) {
  if (!(err instanceof InvalidRequestError) || err.code !== "provider_requires_surface") {
    throw err;
  }
}

const generated = await client.interactions.create({
  model: GEMINI_IMAGE,
  input: "Draw a red fox",
  stream: false,
});
const images = outputImages(generated);
const first = images[0];
if (!first || typeof first.data !== "string") {
  throw new Error("generate_image_missing");
}
const mime = typeof first.mime_type === "string" ? first.mime_type : "image/png";

const edited = await client.interactions.create({
  model: GEMINI_IMAGE,
  stream: false,
  input: [
    { type: "text", text: "Make the fox sit" },
    { type: "image", mime_type: mime, data: first.data },
  ],
});

console.log(
  JSON.stringify({
    generate_count: images.length,
    edit_count: outputImages(edited).length,
  }),
);
