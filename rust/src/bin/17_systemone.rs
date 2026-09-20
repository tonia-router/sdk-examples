//! `/v1/systemone` escape hatch — no typed helper.
//!
//! ```text
//! export TONIA_API_KEY=tonia_sk_…
//! cargo run --bin 17_systemone
//! ```

use serde_json::{json, Value};
use tonia_sdk::RequestOptions;
use tonia_sdk_examples::{caps, example_client, model_rows, pick_id, surface};

#[tokio::main]
async fn main() -> Result<(), tonia_sdk::ToniaError> {
    let client = example_client();
    let listed = client.models.list().await?;
    let rows = model_rows(&listed);
    let model = pick_id(&rows, |item| {
        surface(item).get("family").and_then(Value::as_str) == Some("systemone")
            || caps(item).iter().any(|cap| cap == "systemone")
            || item
                .get("id")
                .and_then(Value::as_str)
                .is_some_and(|id| id.ends_with("jev-latest"))
    })
    .expect("no listed systemone on this key");
    let body = client
        .request(
            "POST",
            "/v1/systemone",
            Some(json!({
                "model": model,
                "state": "The sky is blue.",
                "questions": {
                    "color": {"type": "noul", "instructions": "Is the sky blue?"},
                    "kind": {
                        "type": "choice",
                        "criteria": {
                            "sky": {"description": "open air"},
                            "sea": {"description": "water"}
                        }
                    },
                    "confidence": {
                        "type": "score",
                        "instructions": "How sure is this public fixture?",
                        "criteria": ["Low", "Medium", "High"]
                    }
                }
            })),
            RequestOptions::default(),
        )
        .await?;
    let answers = body.get("answers").and_then(Value::as_object);
    println!(
        "{}",
        json!({
            "model": model,
            "answer_count": answers.map(serde_json::Map::len).unwrap_or(0),
            "usage": body.get("usage")
        })
    );
    Ok(())
}
