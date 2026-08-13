/**
 * Handle admission 429. The SDK does not auto-retry.
 *
 *   export TONIA_API_KEY=tonia_sk_…
 *   npx tsx 07-rate-limit-retry.ts
 */
import {
  ApiError,
  EntitlementError,
  ManagedCredentialUnavailableError,
  RateLimitError,
  Tonia,
} from "@tonia-router/sdk";

const client = new Tonia({ apiKey: process.env.TONIA_API_KEY });
const { data } = await client.models.list();
if (!data[0]) {
  throw new Error("this key has no models; check the profile allowlist in the portal");
}

async function once() {
  return client.chat.completions.create({
    model: data[0].id,
    messages: [{ role: "user", content: "Bonjour" }],
  });
}

function sleep(seconds: number) {
  return new Promise((resolve) => setTimeout(resolve, seconds * 1000));
}

try {
  console.log(JSON.stringify(await once(), null, 2));
} catch (err) {
  if (err instanceof RateLimitError && err.retryable) {
    const wait = err.retryAfterSeconds ?? 1;
    console.error(
      `Admission limited (${err.reason ?? err.code}, scope=${err.scope ?? "?"}). Waiting ${wait}s.`,
    );
    await sleep(wait);
    console.log(JSON.stringify(await once(), null, 2));
  } else if (err instanceof EntitlementError) {
    console.error(
      err.retryable
        ? "Monthly quota reached. Wait Retry-After, or ask a Workspace admin to raise the plan."
        : "Budget exhausted. Do not retry until a Workspace admin adds budget.",
    );
    console.error(err.code, err.entitlementBlock);
    process.exitCode = 1;
  } else if (
    err instanceof ManagedCredentialUnavailableError ||
    (err instanceof ApiError && err.code === "audit_tip_contention")
  ) {
    const wait = err.retryAfterSeconds ?? 1;
    console.error(`${err.code}: retryable, wait ${wait}s.`);
    process.exitCode = 1;
  } else {
    throw err;
  }
}
