//! App-owned `messages[]` + `last_limits`. Pass does not store SDK threads.
//!
//! ```text
//! export TONIA_API_KEY=tonia_sk_…
//! cargo run --bin 09_saas_integrator
//! ```

use serde_json::{json, Value};
use tonia_sdk::ErrorKind;
use tonia_sdk_examples::{example_client, require_first_id};

fn assistant_text(body: &Value) -> String {
    body.get("choices")
        .and_then(Value::as_array)
        .and_then(|choices| choices.first())
        .and_then(|choice| choice.get("message"))
        .and_then(|message| message.get("content"))
        .and_then(Value::as_str)
        .unwrap_or("")
        .trim()
        .to_string()
}

#[tokio::main]
async fn main() -> Result<(), tonia_sdk::ToniaError> {
    let client = example_client();
    let listed = client.models.list().await?;
    let model = require_first_id(&listed);
    let mut thread = vec![json!({
        "role": "user",
        "content": "Remember this word: maple. Reply only: ok"
    })];
    let first = match client
        .chat
        .completions
        .create(json!({ "model": model, "max_tokens": 8, "messages": thread }))
        .await
    {
        Ok(value) => value,
        Err(err) if err.kind == ErrorKind::RateLimit => {
            eprintln!(
                "Admission limited ({:?}). Wait {}s, then retry once.",
                err.reason().or(err.code.as_deref()),
                err.retry_after_seconds().unwrap_or(1)
            );
            std::process::exit(1);
        }
        Err(err) if err.kind == ErrorKind::Entitlement => {
            eprintln!("quota or budget: see portal billing");
            std::process::exit(1);
        }
        Err(err) => return Err(err),
    };
    let reply = assistant_text(&first);
    thread.push(json!({
        "role": "assistant",
        "content": if reply.is_empty() { "ok".into() } else { reply }
    }));
    thread.push(json!({
        "role": "user",
        "content": "Reply with only the word I asked you to remember."
    }));
    let second = client
        .chat
        .completions
        .create(json!({ "model": model, "max_tokens": 16, "messages": thread }))
        .await?;
    let limits = client.last_limits().map(|info| {
        json!({
            "warning": info.warning,
            "kind": info.kind,
            "remaining": info.remaining,
            "period_ends_at": info.period_ends_at
        })
    });
    println!(
        "{}",
        json!({
            "turns": thread.len(),
            "usage": second.get("usage"),
            "last_limits": limits
        })
    );
    Ok(())
}
