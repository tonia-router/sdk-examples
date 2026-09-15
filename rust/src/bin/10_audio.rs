//! Speech bytes + multipart transcriptions. Gemini token audio uses interactions.
//!
//! ```text
//! export TONIA_API_KEY=tonia_sk_…
//! cargo run --bin 10_audio
//! ```

use serde_json::json;
use tonia_sdk_examples::{caps, example_client, model_rows, pick_id, surface};

fn skip_id(id: &str) -> bool {
    let lowered = id.to_ascii_lowercase();
    matches!(lowered.as_str(), "s2.1-pro" | "s2.1-pro-free")
        || lowered.contains("-latest")
        || lowered.contains("vd-")
        || lowered.contains("realtime")
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let client = example_client();
    let listed = client.models.list().await?;
    let rows: Vec<_> = model_rows(&listed)
        .into_iter()
        .filter(|item| !skip_id(item.get("id").and_then(|v| v.as_str()).unwrap_or("")))
        .collect();
    let tts = pick_id(&rows, |item| {
        let id = item.get("id").and_then(|v| v.as_str()).unwrap_or("");
        (surface(item).get("path").and_then(|v| v.as_str()) == Some("/v1/audio/speech")
            || caps(item).iter().any(|cap| cap == "audio_speech"))
            && !id.starts_with("gemini/")
    });
    let stt = pick_id(&rows, |item| {
        let id = item.get("id").and_then(|v| v.as_str()).unwrap_or("");
        (surface(item).get("path").and_then(|v| v.as_str()) == Some("/v1/audio/transcriptions")
            || caps(item).iter().any(|cap| cap == "audio_transcription"))
            && !id.starts_with("gemini/")
    });
    let gemini_audio = pick_id(&rows, |item| {
        let id = item.get("id").and_then(|v| v.as_str()).unwrap_or("");
        id.starts_with("gemini/")
            && matches!(
                surface(item).get("family").and_then(|v| v.as_str()),
                Some("speech" | "transcription")
            )
    });
    if tts.is_none() && stt.is_none() && gemini_audio.is_none() {
        panic!("no listed audio on this key");
    }

    let mut spent = json!({});
    if let Some(tts) = tts {
        let voice = if tts.starts_with("fish_") || tts.contains("s2.1-pro") {
            ""
        } else {
            "alloy"
        };
        let speech = client
            .audio
            .speech
            .create(json!({ "model": tts, "input": "Bonjour Tonia", "voice": voice }))
            .await?;
        spent["speech"] = json!({ "model": tts, "bytes": speech.len() });
    }
    if let Some(stt) = stt {
        let wav = tiny_wav();
        let transcript = client
            .audio
            .transcriptions
            .create(&stt, wav.as_slice(), Some("clip.wav"), &[])
            .await?;
        spent["transcription"] = json!({ "model": stt, "has_text": transcript.is_object() });
    }
    if let Some(gemini_audio) = gemini_audio {
        client
            .interactions
            .create(json!({ "model": gemini_audio, "input": "Bonjour", "stream": false }))
            .await?;
        spent["gemini_interactions"] = json!({ "model": gemini_audio });
    }
    println!("{}", serde_json::to_string_pretty(&spent).unwrap());
    Ok(())
}

fn tiny_wav() -> Vec<u8> {
    let mut out = Vec::from(*b"RIFF");
    out.extend_from_slice(&36u32.to_le_bytes());
    out.extend_from_slice(b"WAVEfmt ");
    out.extend_from_slice(&16u32.to_le_bytes());
    out.extend_from_slice(&1u16.to_le_bytes());
    out.extend_from_slice(&1u16.to_le_bytes());
    out.extend_from_slice(&8000u32.to_le_bytes());
    out.extend_from_slice(&16000u32.to_le_bytes());
    out.extend_from_slice(&2u16.to_le_bytes());
    out.extend_from_slice(&16u16.to_le_bytes());
    out.extend_from_slice(b"data");
    out.extend_from_slice(&0u32.to_le_bytes());
    out
}
