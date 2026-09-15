//! Cascaded Live + wait_turn. Opt-in live (`TONIA_API_KEY` + DEV/local Pass).
//!
//! ```text
//! export TONIA_API_KEY=tonia_sk_…
//! export TONIA_BASE_URL=https://pass.tonia.ca:8443
//! cargo run --bin 14_realtime
//! ```

use std::time::Duration;

use serde_json::json;
use tonia_sdk::RealtimeConnect;
use tonia_sdk_examples::{caps, example_client, model_rows, pick_id};

#[tokio::main]
async fn main() -> Result<(), tonia_sdk::ToniaError> {
    let client = example_client();
    let listed = client.models.list().await?;
    let rows = model_rows(&listed);
    let live = pick_id(&rows, |item| {
        let id = item.get("id").and_then(|v| v.as_str()).unwrap_or("");
        matches!(id, "gpt-live-1" | "openai/gpt-live-1")
            || caps(item).iter().any(|cap| cap == "realtime")
    });
    if live.is_none() {
        panic!(
            "this key cannot see gpt-live-1; add it on the profile Temps réel / Live tab, then retry"
        );
    }
    let mut session = client
        .realtime
        .connect(RealtimeConnect {
            model: Some("gpt-live-1".into()),
            ..RealtimeConnect::default()
        })
        .await?;
    println!(
        "{}",
        json!({
            "session_id": session.session_id,
            "mode": session.mode,
            "model": session.model,
            "reconnect": session.reconnect
        })
    );
    session.send_text("Reply with the single word ok.").await?;
    let event = session.wait_turn(Duration::from_secs(60)).await?;
    println!("{}", serde_json::to_string_pretty(&event).unwrap());
    session.close().await?;
    Ok(())
}
