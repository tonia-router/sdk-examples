//! AgentBlockError when tool calls are off on the bound profile.
//!
//! ```text
//! export TONIA_API_KEY=tonia_sk_…
//! cargo run --bin 13_agent_block
//! ```

use serde_json::json;
use tonia_sdk::ErrorKind;
use tonia_sdk_examples::{example_client, require_first_id};

#[tokio::main]
async fn main() -> Result<(), tonia_sdk::ToniaError> {
    let client = example_client();
    let listed = client.models.list().await?;
    let model = require_first_id(&listed);
    match client
        .chat
        .completions
        .create(json!({
            "model": model,
            "messages": [{ "role": "user", "content": "Weather in Montréal?" }],
            "tools": [{
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Weather for a city",
                    "parameters": {
                        "type": "object",
                        "properties": { "city": { "type": "string" } },
                        "required": ["city"]
                    }
                }
            }]
        }))
        .await
    {
        Ok(_) => {
            println!("Tool calls are allowed on this key's profile.");
            Ok(())
        }
        Err(err) if err.kind == ErrorKind::AgentBlock => {
            eprintln!("Request blocked by Agent controls.");
            eprintln!(
                "Ask a Workspace admin to open Policies → the bound profile → \
                 Advanced — Agent controls."
            );
            eprintln!("{:?}", err.agent_block());
            std::process::exit(1);
        }
        Err(err) => Err(err),
    }
}
