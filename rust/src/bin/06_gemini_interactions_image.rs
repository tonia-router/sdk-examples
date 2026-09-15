//! Gemini `/v1/interactions` generate + edit (raw base64, not a data URL).
//!
//! ```text
//! export TONIA_API_KEY=tonia_sk_…
//! cargo run --bin 06_gemini_interactions_image
//! ```

use serde_json::{json, Value};
use tonia_sdk::ErrorKind;
use tonia_sdk_examples::{example_client, model_rows, pick_id};

fn output_images(body: &Value) -> Vec<Value> {
    let root = body.get("interaction").unwrap_or(body);
    let Some(steps) = root.get("steps").and_then(Value::as_array) else {
        return Vec::new();
    };
    let mut out = Vec::new();
    for step in steps {
        if step.get("type").and_then(Value::as_str) != Some("model_output") {
            continue;
        }
        let Some(content) = step.get("content").and_then(Value::as_array) else {
            continue;
        };
        for part in content {
            let data = part.get("data").and_then(Value::as_str).unwrap_or("");
            if data.is_empty() {
                continue;
            }
            let mime = part.get("mime_type").and_then(Value::as_str).unwrap_or("");
            if part.get("type").and_then(Value::as_str) == Some("image")
                || mime.starts_with("image/")
            {
                out.push(part.clone());
            }
        }
    }
    out
}

#[tokio::main]
async fn main() -> Result<(), tonia_sdk::ToniaError> {
    let client = example_client();
    let listed = client.models.list().await?;
    let rows = model_rows(&listed);
    let gemini_image = pick_id(&rows, |item| {
        let id = item.get("id").and_then(Value::as_str).unwrap_or("");
        id.starts_with("gemini/") && id.to_ascii_lowercase().contains("image")
    })
    .expect("no Gemini image SKU on this key");

    match client
        .images
        .generate(json!({ "model": gemini_image, "prompt": "Draw a red fox" }))
        .await
    {
        Err(err)
            if err.kind == ErrorKind::InvalidRequest
                && err.code.as_deref() == Some("provider_requires_surface") => {}
        Ok(_) => panic!("expected provider_requires_surface on /v1/images"),
        Err(err) => return Err(err),
    }

    let generated = client
        .interactions
        .create(json!({
            "model": gemini_image,
            "input": "Draw a red fox",
            "stream": false
        }))
        .await?;
    let images = output_images(&generated);
    if images.is_empty() {
        panic!("generate_image_missing");
    }
    let first = &images[0];
    let mime = first
        .get("mime_type")
        .and_then(Value::as_str)
        .unwrap_or("image/png");
    let raw_b64 = first.get("data").and_then(Value::as_str).unwrap();
    let edited = client
        .interactions
        .create(json!({
            "model": gemini_image,
            "stream": false,
            "input": [
                { "type": "text", "text": "Make the fox sit" },
                { "type": "image", "mime_type": mime, "data": raw_b64 }
            ]
        }))
        .await?;
    println!(
        "{}",
        json!({
            "generate_count": images.len(),
            "edit_count": output_images(&edited).len()
        })
    );
    Ok(())
}
