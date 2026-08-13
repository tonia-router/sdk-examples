/**
 * SaaS integrator: you store history, meter usage, watch limits.
 *
 * tonia Pass does not keep SDK chat threads. Billing, seats, and API keys
 * stay in the portal (https://portal.tonia.ca).
 *
 *   export TONIA_API_KEY=tonia_sk_…
 *   npx tsx 09-saas-integrator.ts
 */
import { EntitlementError, RateLimitError, Tonia } from "@tonia-router/sdk";

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
const model = data[0].id;

type ChatMessage = { role: "user" | "assistant"; content: string };

function assistantText(body: unknown): string {
  const choice = (body as { choices?: { message?: { content?: unknown } }[] })
    ?.choices?.[0];
  const content = choice?.message?.content;
  return typeof content === "string" ? content.trim() : "";
}

function usageOf(body: unknown): {
  prompt_tokens: number | null;
  completion_tokens: number | null;
  total_tokens: number | null;
} {
  const usage = (body as { usage?: Record<string, unknown> })?.usage;
  const prompt = usage?.prompt_tokens ?? usage?.input_tokens;
  const completion = usage?.completion_tokens ?? usage?.output_tokens;
  const total = usage?.total_tokens;
  return {
    prompt_tokens: typeof prompt === "number" ? prompt : null,
    completion_tokens: typeof completion === "number" ? completion : null,
    total_tokens: typeof total === "number" ? total : null,
  };
}

// Stand-in for your database. Pass does not store this for the SDK.
const thread: ChatMessage[] = [
  { role: "user", content: "Remember this word: maple. Reply only: ok" },
];

try {
  const first = await client.chat.completions.create({
    model,
    max_tokens: 8,
    messages: thread,
  });
  thread.push({ role: "assistant", content: assistantText(first) || "ok" });
  thread.push({
    role: "user",
    content: "Reply with only the word I asked you to remember.",
  });
  const second = await client.chat.completions.create({
    model,
    max_tokens: 16,
    messages: thread,
  });
  // lastLimits is set only when usage is ≥ 80% of quota/budget.
  console.log(
    JSON.stringify(
      {
        turns: thread.length,
        usage: usageOf(second),
        lastLimits: client.lastLimits
          ? {
              warning: client.lastLimits.warning,
              kind: client.lastLimits.kind,
              remaining: client.lastLimits.remaining,
              periodEndsAt: client.lastLimits.periodEndsAt,
            }
          : null,
      },
      null,
      2,
    ),
  );
} catch (err) {
  if (err instanceof RateLimitError) {
    console.error(
      `Admission limited (${err.reason ?? err.code}). Wait ${err.retryAfterSeconds ?? 1}s, then retry once.`,
    );
    process.exitCode = 1;
  } else if (err instanceof EntitlementError) {
    console.error(
      err.retryable
        ? "Monthly quota reached. Wait Retry-After, or raise the plan in the portal."
        : "Budget exhausted. Do not retry until a Workspace admin adds credit.",
    );
    process.exitCode = 1;
  } else {
    throw err;
  }
}
