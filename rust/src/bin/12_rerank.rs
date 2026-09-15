//! `/v1/rerank` only — not lab `/v2/rerank`.
//!
//! ```text
//! export TONIA_API_KEY=tonia_sk_…
//! cargo run --bin 12_rerank
//! ```

use serde_json::{json, Value};
use tonia_sdk_examples::{caps, example_client, model_rows, pick_id, surface};

#[tokio::main]
async fn main() -> Result<(), tonia_sdk::ToniaError> {
    let client = example_client();
    let listed = client.models.list().await?;
    let rows = model_rows(&listed);
    let model = pick_id(&rows, |item| {
        surface(item).get("family").and_then(Value::as_str) == Some("rerank")
            || caps(item).iter().any(|cap| cap == "rerank")
            || item
                .get("id")
                .and_then(Value::as_str)
                .is_some_and(|id| id.to_ascii_lowercase().contains("rerank"))
    })
    .expect("no listed rerank on this key");
    let body = client
        .rerank
        .create(json!({
            "model": model,
            "query": "bonjour",
            "documents": ["bonjour", "au revoir"]
        }))
        .await?;
    let ranked = body
        .get("results")
        .or_else(|| body.get("data"))
        .and_then(Value::as_array)
        .map(Vec::len)
        .unwrap_or(0);
    println!("{}", json!({ "model": model, "result_count": ranked }));
    Ok(())
}
