//! `/v1/embeddings` only — not lab `/v2/embed`.
//!
//! ```text
//! export TONIA_API_KEY=tonia_sk_…
//! cargo run --bin 11_embeddings
//! ```

use serde_json::{json, Value};
use tonia_sdk_examples::{caps, example_client, model_rows, pick_id, surface};

#[tokio::main]
async fn main() -> Result<(), tonia_sdk::ToniaError> {
    let client = example_client();
    let listed = client.models.list().await?;
    let rows = model_rows(&listed);
    let model = pick_id(&rows, |item| {
        if surface(item).get("family").and_then(Value::as_str) == Some("embeddings") {
            return true;
        }
        if caps(item).iter().any(|cap| cap == "embeddings") {
            return true;
        }
        let id = item.get("id").and_then(Value::as_str).unwrap_or("");
        id.to_ascii_lowercase().contains("embed") && !id.to_ascii_lowercase().contains("rerank")
    })
    .expect("no listed embeddings on this key");
    let body = client
        .embeddings
        .create(json!({ "model": model, "input": "Bonjour" }))
        .await?;
    let dims = body
        .get("data")
        .and_then(Value::as_array)
        .and_then(|data| data.first())
        .and_then(|row| row.get("embedding"))
        .and_then(Value::as_array)
        .map(Vec::len)
        .unwrap_or(0);
    println!("{}", json!({ "model": model, "dimensions": dims }));
    Ok(())
}
