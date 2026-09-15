//! Gemini live STT 16 kHz + commit. Opt-in live.
//!
//! ```text
//! export TONIA_API_KEY=tonia_sk_…
//! export TONIA_BASE_URL=https://pass-dev.tonia.ca:8443
//! cargo run --bin 16_gemini_transcribe_live
//! ```

use std::time::Duration;

use serde_json::json;
use tonia_sdk::RealtimeConnect;
use tonia_sdk_examples::{example_client, model_rows, pick_id};

const LIVE: &str = "gemini-3.5-transcribe-live";
const RATE: usize = 16_000;
const MS: usize = 80;

fn pcm16_le_16k() -> Vec<u8> {
    vec![0u8; RATE * MS / 1000 * 2]
}

#[tokio::main]
async fn main() -> Result<(), tonia_sdk::ToniaError> {
    let client = example_client();
    let listed = client.models.list().await?;
    let rows = model_rows(&listed);
    if pick_id(&rows, |item| {
        matches!(
            item.get("id").and_then(|v| v.as_str()),
            Some(LIVE) | Some("gemini/gemini-3.5-transcribe-live")
        )
    })
    .is_none()
    {
        panic!(
            "this key cannot see gemini-3.5-transcribe-live; add it on the \
             profile Temps réel / Live tab, then retry"
        );
    }
    let pcm = pcm16_le_16k();
    let mut session = client
        .realtime
        .connect(RealtimeConnect {
            provider: Some("gemini".into()),
            model: Some(LIVE.into()),
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
            "model": session.model
        })
    );
    for _ in 0..8 {
        session
            .send_audio_append(&pcm, Some("audio/pcm;rate=16000"))
            .await?;
        tokio::time::sleep(Duration::from_millis(30)).await;
    }
    tokio::time::sleep(Duration::from_millis(400)).await;
    session
        .send_audio_commit(None, Some("audio/pcm;rate=16000"))
        .await?;
    let event = session.recv(Some(Duration::from_secs(60))).await?;
    println!("{}", serde_json::to_string_pretty(&event).unwrap());
    session.close().await?;
    Ok(())
}
