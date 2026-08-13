/**
 * Handle a policy block, then retry after a redact-mode profile is configured
 * in the tonia portal (https://portal.tonia.ca) under Policies → Profiles.
 *
 *   export TONIA_API_KEY=tonia_sk_…
 *   npx tsx 04-policy-block.ts
 */
import { PolicyBlockError, Tonia } from "@tonia/sdk";

const client = new Tonia({ apiKey: process.env.TONIA_API_KEY });

const { data } = await client.models.list();
if (!data[0]) {
  throw new Error("empty allowlist — do not guess a model id");
}

try {
  await client.chat.completions.create({
    model: data[0].id,
    messages: [{ role: "user", content: "…" }],
  });
} catch (err) {
  if (err instanceof PolicyBlockError) {
    console.error("Request blocked by Workspace Policies.");
    console.error(
      "Ask a Workspace admin to bind this key to a redact-mode profile (Policies → Profiles), then retry.",
    );
    console.error(err.policyBlock);
    process.exitCode = 1;
  } else {
    throw err;
  }
}
