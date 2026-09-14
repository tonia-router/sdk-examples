/**
 * Handle an agent-control refusal, then ask an admin to open the bound
 * profile in the tonia portal (https://portal.tonia.ca) under
 * Policies → profile → Advanced — Agent controls.
 *
 *   export TONIA_API_KEY=tonia_sk_…
 *   npx tsx 13-agent-block.ts
 */
import { AgentBlockError, Tonia } from "@tonia-router/sdk";

const client = new Tonia({ apiKey: process.env.TONIA_API_KEY });

const { data } = await client.models.list();
if (!data[0]) {
  throw new Error("this key has no models; check the profile allowlist in the portal");
}

try {
  await client.chat.completions.create({
    model: data[0].id,
    messages: [{ role: "user", content: "Weather in Montréal?" }],
    tools: [
      {
        type: "function",
        function: {
          name: "get_weather",
          description: "Weather for a city",
          parameters: {
            type: "object",
            properties: { city: { type: "string" } },
            required: ["city"],
          },
        },
      },
    ],
  });
  console.log("Tool calls are allowed on this key's profile.");
} catch (err) {
  if (err instanceof AgentBlockError) {
    console.error("Request blocked by Agent controls.");
    console.error(
      "Ask a Workspace admin to open Policies → the bound profile → Advanced — Agent controls.",
    );
    console.error(err.agentBlock);
    process.exitCode = 1;
  } else {
    throw err;
  }
}
