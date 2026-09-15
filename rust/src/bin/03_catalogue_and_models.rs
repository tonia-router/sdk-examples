//! Public catalogue vs keyed models.list; id styles.
//!
//! ```text
//! export TONIA_API_KEY=tonia_sk_…   # only needed for runtime models
//! cargo run --bin 03_catalogue_and_models
//! ```

use tonia_sdk::Tonia;
use tonia_sdk_examples::example_client;

#[tokio::main]
async fn main() -> Result<(), tonia_sdk::ToniaError> {
    let public_client = Tonia::new();
    let catalogue = public_client.catalogue.list().await?;
    let public_models = public_client.public_models.list().await?;
    println!(
        "catalogue products: {}",
        catalogue
            .get("products")
            .and_then(|value| value.as_array())
            .map(Vec::len)
            .unwrap_or(0)
    );
    println!(
        "public models: {}",
        public_models
            .get("data")
            .and_then(|value| value.as_array())
            .map(Vec::len)
            .unwrap_or(0)
    );

    if std::env::var("TONIA_API_KEY").is_ok() {
        let client = example_client();
        let runtime = client.models.list().await?;
        println!(
            "runtime models: {}",
            runtime
                .get("data")
                .and_then(|value| value.as_array())
                .map(Vec::len)
                .unwrap_or(0)
        );
        println!("last_limits: {:?}", client.last_limits());
    }
    Ok(())
}
