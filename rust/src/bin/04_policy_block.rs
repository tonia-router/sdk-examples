//! PolicyBlockError on HTTP 200. No redact header — profile lives in the portal.
//!
//! ```text
//! export TONIA_API_KEY=tonia_sk_…
//! cargo run --bin 04_policy_block
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
            "messages": [{ "role": "user", "content": "…" }],
        }))
        .await
    {
        Ok(_) => Ok(()),
        Err(err) if err.kind == ErrorKind::PolicyBlock => {
            eprintln!("Request blocked by Workspace Policies.");
            eprintln!(
                "Ask a Workspace admin to bind this key to a redact-mode profile \
                 (Policies → Profiles), then retry."
            );
            eprintln!("{:?}", err.policy_block());
            std::process::exit(1);
        }
        Err(err) => Err(err),
    }
}
