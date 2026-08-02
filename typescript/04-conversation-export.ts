/**
 * Export conversation history (needs a member app_session key + chat_history plan).
 *
 *   export TONIA_API_KEY=tonia_sk_…
 *   npx tsx 04-conversation-export.ts
 */
import { Tonia } from "@tonia/sdk";

const client = new Tonia({ apiKey: process.env.TONIA_API_KEY });
const exported = await client.conversations.export();
console.log(JSON.stringify(exported, null, 2));
