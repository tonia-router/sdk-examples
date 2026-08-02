"""Public catalogue + public models (no key) and runtime models (with key).

    export TONIA_API_KEY=tonia_sk_…   # only needed for runtime models
    python 03_catalogue_and_models.py
"""

from __future__ import annotations

import os

from tonia import Tonia

with Tonia() as public_client:
    catalogue = public_client.catalogue.list()
    public_models = public_client.public_models.list()
    print("catalogue products:", len(catalogue.get("products", [])))
    print("public models:", len(public_models.get("data", [])))

with Tonia(api_key=os.environ.get("TONIA_API_KEY")) as client:
    runtime = client.models.list()
    print("runtime models:", len(runtime.get("data", [])))
    print("last_limits:", client.last_limits)
