"""Path A image generate (openai / xAI / StepFun).

Gemini image SKUs must use 06_gemini_interactions_image.py instead.

    export TONIA_API_KEY=tonia_sk_…
    python 05_images_path_a.py
"""

from __future__ import annotations

import json
import os

from tonia import Tonia

with Tonia(
    api_key=os.environ["TONIA_API_KEY"],
    timeout=300,
    default_headers={
        "HTTP-Referer": "https://github.com/tonia-router/sdk-examples",
        "X-Tonia-Title": "sdk-examples",
    },
) as client:
    listed = client.models.list()
    model = next(
        (
            item["id"]
            for item in listed["data"]
            if item["id"].startswith(("openai/", "xai/", "stepfun/"))
            and "image" in item["id"].lower()
        ),
        None,
    )
    if not model:
        raise SystemExit("no Path A image SKU on this key")
    image = client.images.generate(
        model=model,
        prompt="Draw a red fox",
        n=1,
    )
    data = image.get("data") if isinstance(image, dict) else None
    print(json.dumps({"image_count": len(data) if isinstance(data, list) else 0}))
