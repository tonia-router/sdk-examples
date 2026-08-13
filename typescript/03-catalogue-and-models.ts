/**
 * Public catalogue + public models (no key) and runtime models (with key).
 *
 *   export TONIA_API_KEY=tonia_sk_…   # only needed for runtime models
 *   npx tsx 03-catalogue-and-models.ts
 */
import { Tonia } from "@tonia-router/sdk";

const publicClient = new Tonia(); // no key for public routes
const catalogue = await publicClient.catalogue.list();
const publicModels = await publicClient.publicModels.list();
console.log("catalogue products:", (catalogue as { products?: unknown[] }).products?.length);
console.log("public models:", (publicModels as { data?: unknown[] }).data?.length);

const client = new Tonia({ apiKey: process.env.TONIA_API_KEY });
const runtime = await client.models.list();
console.log("runtime models:", (runtime as { data?: unknown[] }).data?.length);
// Bearer / OpenAI-shaped ids. x-api-key listing looks different.
console.log("lastLimits:", client.lastLimits);
