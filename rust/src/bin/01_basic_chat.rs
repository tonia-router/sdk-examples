//! Ctor + attribution headers + models.list + chat.completions.create
//!
//! ```text
//! export TONIA_API_KEY=tonia_sk_…
//! cargo run --bin 01_basic_chat
//! ```

use serde_json::json;
use tonia_sdk_examples::{example_client, require_first_id};

#[tokio::main]
async fn main() -> Result<(), tonia_sdk::ToniaError> {
    let client = example_client();
    let listed = client.models.list().await?;
    let model = require_first_id(&listed);
    let completion = client
        .chat
        .completions
        .create(json!({
            "model": model,
            "messages": [{ "role": "user", "content": "Bonjour — une phrase courte." }],
        }))
        .await?;
    println!("{}", serde_json::to_string_pretty(&completion).unwrap());
    Ok(())
}
