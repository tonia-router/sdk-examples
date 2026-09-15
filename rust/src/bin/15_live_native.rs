//! Native 24 kHz PCM + recv. No wait_turn / input_text. Opt-in live.
//!
//! ```text
//! export TONIA_API_KEY=tonia_sk_…
//! export TONIA_BASE_URL=https://pass-dev.tonia.ca:8443
//! cargo run --bin 15_live_native
//! ```

use std::time::Duration;

use serde_json::json;
use tonia_sdk::RealtimeConnect;
use tonia_sdk_examples::{caps, example_client, model_rows, pick_id};

const RATE: usize = 24_000;
const MS: usize = 100;

fn pcm16_le_24k() -> Vec<u8> {
    let samples = RATE * MS / 1000;
    vec![0u8; samples * 2]
}

#[tokio::main]
async fn main() -> Result<(), tonia_sdk::ToniaError> {
    let client = example_client();
    let listed = client.models.list().await?;
    let rows = model_rows(&listed);
    if pick_id(&rows, |item| {
        let id = item.get("id").and_then(|v| v.as_str()).unwrap_or("");
        matches!(id, "gpt-live-1" | "openai/gpt-live-1")
            || caps(item).iter().any(|cap| cap == "realtime")
    })
    .is_none()
    {
        panic!(
            "this key cannot see gpt-live-1; add it on the profile Temps réel / Live tab, then retry"
        );
    }
    let mut session = client
        .realtime
        .connect(RealtimeConnect {
            model: Some("gpt-live-1".into()),
            mode: Some("native".into()),
            transcripts: true,
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
    session
        .send_audio_append(&pcm16_le_24k(), Some("audio/pcm"))
        .await?;
    loop {
        let event = session.recv(Some(Duration::from_secs(60))).await?;
        let kind = event.get("type").and_then(|v| v.as_str()).unwrap_or("");
        if kind == "output_audio.delta" {
            println!(
                "{}",
                json!({
                    "type": kind,
                    "session_id": event.get("session_id"),
                    "audio_b64_chars": event.get("audio").and_then(|v| v.as_str()).unwrap_or("").len()
                })
            );
            break;
        }
        if matches!(
            kind,
            "transcript.delta" | "transcript.final" | "delegation.created"
        ) {
            continue;
        }
        panic!("unexpected native event: {kind}");
    }
    session.close().await?;
    Ok(())
}
