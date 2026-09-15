//! Shared helpers for the Rust cookbook bins.

use serde_json::Value;
use tonia_sdk::Tonia;

pub fn example_client() -> Tonia {
    let mut builder = Tonia::builder()
        .api_key(std::env::var("TONIA_API_KEY").expect("TONIA_API_KEY"))
        .header(
            "HTTP-Referer",
            "https://github.com/tonia-router/sdk-examples",
        )
        .header("X-Tonia-Title", "sdk-examples");
    if let Some(url) = std::env::var("TONIA_BASE_URL")
        .ok()
        .or_else(|| std::env::var("PASS_BASE_URL").ok())
        .filter(|value| !value.is_empty())
    {
        builder = builder.base_url(url);
    }
    builder.build()
}

pub fn model_rows(listed: &Value) -> Vec<Value> {
    listed
        .get("data")
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default()
}

pub fn model_ids(listed: &Value) -> Vec<String> {
    model_rows(listed)
        .into_iter()
        .filter_map(|item| item.get("id").and_then(Value::as_str).map(str::to_string))
        .collect()
}

pub fn require_first_id(listed: &Value) -> String {
    model_ids(listed).into_iter().next().unwrap_or_else(|| {
        panic!("this key has no models; check the profile allowlist in the portal")
    })
}

pub fn caps(item: &Value) -> Vec<String> {
    item.get("capabilities")
        .and_then(Value::as_array)
        .map(|caps| {
            caps.iter()
                .filter_map(Value::as_str)
                .map(str::to_string)
                .collect()
        })
        .unwrap_or_default()
}

pub fn surface(item: &Value) -> &Value {
    item.get("surface").unwrap_or(&Value::Null)
}

pub fn pick_id(rows: &[Value], test: impl Fn(&Value) -> bool) -> Option<String> {
    rows.iter()
        .find(|item| test(item))
        .and_then(|item| item.get("id").and_then(Value::as_str))
        .map(str::to_string)
}
