//! `/v1/images/generations`. Skip Gemini (use 06).
//!
//! ```text
//! export TONIA_API_KEY=tonia_sk_…
//! cargo run --bin 05_images
//! ```

use serde_json::json;
use tonia_sdk_examples::{caps, example_client, model_rows, pick_id, surface};

fn is_gemini_image(id: &str) -> bool {
    id.starts_with("gemini/") || id.starts_with("gemini-")
}

fn is_path_a_image(item: &serde_json::Value) -> bool {
    let id = item.get("id").and_then(|v| v.as_str()).unwrap_or("");
    if id.to_ascii_lowercase().contains("turbo") || is_gemini_image(id) {
        return false;
    }
    if surface(item).get("path").and_then(|v| v.as_str()) == Some("/v1/images/generations") {
        return true;
    }
    caps(item).iter().any(|cap| cap == "image_generation")
}

#[tokio::main]
async fn main() -> Result<(), tonia_sdk::ToniaError> {
    let client = example_client();
    let listed = client.models.list().await?;
    let rows = model_rows(&listed);
    let model = pick_id(&rows, is_path_a_image).unwrap_or_else(|| {
        panic!("no image SKU for /v1/images on this key");
    });
    let mut body = json!({
        "model": model,
        "prompt": "Draw a red fox",
        "n": 1,
        "size": "2k",
    });
    if model.to_ascii_lowercase().contains("gpt-image-2.5") {
        body["quality"] = json!("auto");
    }
    let image = client.images.generate(body).await?;
    let count = image
        .get("data")
        .and_then(|value| value.as_array())
        .map(Vec::len)
        .unwrap_or(0);
    println!(
        "{}",
        json!({ "model": model, "size": "2k", "image_count": count })
    );
    Ok(())
}
