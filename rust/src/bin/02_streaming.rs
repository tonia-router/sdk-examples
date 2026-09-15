//! Incremental `.stream()` — do not buffer the body.
//!
//! ```text
//! export TONIA_API_KEY=tonia_sk_…
//! cargo run --bin 02_streaming
//! ```

use futures_util::StreamExt;
use serde_json::json;
use tonia_sdk_examples::{example_client, require_first_id};

#[tokio::main]
async fn main() -> Result<(), tonia_sdk::ToniaError> {
    let client = example_client();
    let listed = client.models.list().await?;
    let model = require_first_id(&listed);
    let mut stream = client.chat.completions.stream(json!({
        "model": model,
        "messages": [{ "role": "user", "content": "Compte jusqu’à 5." }],
    }));
    while let Some(event) = stream.next().await {
        let event = event?;
        if event.data == "[DONE]" {
            break;
        }
        if let Some(json) = event.json {
            println!("{}", json);
        }
    }
    Ok(())
}
