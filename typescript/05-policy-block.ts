/**
 * Handle a policy block, then retry after a redact-mode profile is configured
 * in the tonia portal (https://portal.tonia.ca).
 *
 *   export TONIA_API_KEY=tonia_sk_…
 *   npx tsx 05-policy-block.ts
 */
import { PolicyBlockError, Tonia } from "@tonia/sdk";

const client = new Tonia({ apiKey: process.env.TONIA_API_KEY });

try {
  await client.chat.completions.create({
    model: "openai/gpt-4.1-mini",
    messages: [{ role: "user", content: "…" }],
  });
} catch (err) {
  if (err instanceof PolicyBlockError) {
    console.error("Blocked by policy.");
    console.error("Configure a redact-mode profile in the portal, bind this key, then retry.");
    console.error(err.policyBlock);
    process.exitCode = 1;
  } else {
    throw err;
  }
}
