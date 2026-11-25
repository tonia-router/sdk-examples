/**
 * System One on tenant `/v1/systemone`.
 *
 * Use the escape hatch. There is no typed `systemone.create` helper.
 * `stream` is not supported. Ask and clavarde do not list these ids. Use a portal API key.
 *
 *   export TONIA_API_KEY=tonia_sk_…
 *   npx tsx 17-systemone.ts
 */
import { Tonia } from "@tonia-router/sdk";

function isSystemone(item: {
  id: string;
  capabilities?: string[];
  surface?: { family?: string };
}): boolean {
  if (item.surface?.family === "systemone") return true;
  if (item.capabilities?.includes("systemone")) return true;
  return item.id.endsWith("jev-latest");
}

const client = new Tonia({
  apiKey: process.env.TONIA_API_KEY,
  defaultHeaders: {
    "HTTP-Referer": "https://github.com/tonia-router/sdk-examples",
    "X-Tonia-Title": "sdk-examples",
  },
});

const { data } = await client.models.list();
const model = data.find(isSystemone)?.id;
if (!model) {
  throw new Error("no listed systemone on this key");
}
const body = (await client.request("POST", "/v1/systemone", {
  model,
  state: "The sky is blue.",
  questions: {
    color: { type: "noul", instructions: "Is the sky blue?" },
    kind: {
      type: "choice",
      criteria: { sky: { description: "open air" }, sea: { description: "water" } },
    },
    confidence: {
      type: "score",
      instructions: "How sure is this public fixture?",
      criteria: ["Low", "Medium", "High"],
    },
  },
})) as { answers?: Record<string, unknown>; usage?: unknown };
const answers = body.answers ?? {};
console.log(
  JSON.stringify(
    {
      model,
      answer_count: Object.keys(answers).length,
      usage: body.usage,
    },
    null,
    2,
  ),
);
