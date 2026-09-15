//! Manual retry from `retryable` + `retry_after_seconds`. The SDK never auto-retries.
//!
//! ```text
//! export TONIA_API_KEY=tonia_sk_…
//! cargo run --bin 07_rate_limit_retry
//! ```

use std::time::Duration;

use serde_json::json;
use tonia_sdk::ErrorKind;
use tonia_sdk_examples::{example_client, require_first_id};

#[tokio::main]
async fn main() -> Result<(), tonia_sdk::ToniaError> {
    let client = example_client();
    let listed = client.models.list().await?;
    let model = require_first_id(&listed);
    let body = json!({
        "model": model,
        "messages": [{ "role": "user", "content": "Bonjour" }],
    });
    match client.chat.completions.create(body.clone()).await {
        Ok(value) => {
            println!("{value}");
            Ok(())
        }
        Err(err) if err.kind == ErrorKind::RateLimit && err.retryable == Some(true) => {
            let wait = err.retry_after_seconds().unwrap_or(1);
            eprintln!(
                "Admission limited ({}, scope={:?}). Waiting {wait}s.",
                err.reason().or(err.code.as_deref()).unwrap_or("rate_limit"),
                err.scope()
            );
            tokio::time::sleep(Duration::from_secs(wait)).await;
            println!("{}", client.chat.completions.create(body).await?);
            Ok(())
        }
        Err(err) if err.kind == ErrorKind::Entitlement => {
            eprintln!(
                "{}",
                if err.retryable == Some(true) {
                    "Monthly quota reached. Wait Retry-After, or ask a Workspace admin to raise the plan."
                } else {
                    "Budget exhausted. Do not retry until a Workspace admin adds budget."
                }
            );
            eprintln!("{:?} {:?}", err.code, err.entitlement_block());
            std::process::exit(1);
        }
        Err(err)
            if matches!(
                err.kind,
                ErrorKind::ManagedCredentialUnavailable | ErrorKind::Api
            ) && (err.kind != ErrorKind::Api
                || err.code.as_deref() == Some("audit_tip_contention")) =>
        {
            let wait = err.retry_after_seconds().unwrap_or(1);
            eprintln!("{:?}: retryable, wait {wait}s.", err.code);
            std::process::exit(1);
        }
        Err(err) => Err(err),
    }
}
