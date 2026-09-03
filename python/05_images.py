"""Image generate on `/v1/images/generations`.

Send the tenant dial (`1k` / `2k` / `4k`) or OpenAI `size`.
Pass maps each lab. Do not send `resolution` or `image_size`.

Gemini image SKUs must use 06_gemini_interactions_image.py instead.

    export TONIA_API_KEY=tonia_sk_…
    python 05_images.py
"""

from __future__ import annotations

import json
import os

from tonia import Tonia


def is_gemini_image(model_id: str) -> bool:
    return model_id.startswith("gemini/") or model_id.startswith("gemini-")


def is_openai_image(model_id: str) -> bool:
    return model_id.startswith("openai/") or model_id.lower().startswith("gpt-image")


def is_xai_image(model_id: str) -> bool:
    return model_id.startswith("xai/") or model_id.lower().startswith("grok-imagine-image")


def is_meta_image(model_id: str) -> bool:
    return model_id.lower().startswith("muse-image")


def is_alibaba_image(model_id: str) -> bool:
    lowered = model_id.lower()
    return lowered.startswith("qwen-image") or model_id.startswith("alibaba_qwen/")


def _caps(item: dict[str, object]) -> list[str]:
    raw = item.get("capabilities")
    return [str(cap) for cap in raw] if isinstance(raw, list) else []


def _surface(item: dict[str, object]) -> dict[str, object]:
    raw = item.get("surface")
    return raw if isinstance(raw, dict) else {}


def is_path_a_image(item: dict[str, object]) -> bool:
    model_id = str(item["id"])
    if "turbo" in model_id.lower() or is_gemini_image(model_id):
        return False
    if _surface(item).get("path") == "/v1/images/generations":
        return True
    if "image_generation" in _caps(item):
        return True
    return (
        is_openai_image(model_id)
        or is_xai_image(model_id)
        or is_meta_image(model_id)
        or is_alibaba_image(model_id)
    )


with Tonia(
    api_key=os.environ["TONIA_API_KEY"],
    base_url=os.environ.get("TONIA_BASE_URL"),
    timeout=300,
    default_headers={
        "HTTP-Referer": "https://github.com/tonia-router/sdk-examples",
        "X-Tonia-Title": "sdk-examples",
    },
) as client:
    listed = client.models.list()
    path_a = [item["id"] for item in listed["data"] if is_path_a_image(item)]
    model = next((item_id for item_id in path_a if is_meta_image(item_id)), None)
    if model is None:
        model = next(
            (
                item_id
                for item_id in path_a
                if is_xai_image(item_id) and "quality" not in item_id.lower()
            ),
            None,
        )
    if model is None:
        model = next((item_id for item_id in path_a if is_xai_image(item_id)), None)
    if model is None:
        model = path_a[0] if path_a else None
    if not model:
        raise SystemExit("no image SKU for /v1/images on this key")
    # Tenant dial. Pass maps OpenAI 2k to billed WxH.
    size = "2k"
    image = client.images.generate(
        model=model,
        prompt="Draw a red fox",
        n=1,
        size=size,
    )
    data = image.get("data") if isinstance(image, dict) else None
    print(
        json.dumps(
            {
                "model": model,
                "size": size,
                "image_count": len(data) if isinstance(data, list) else 0,
            }
        )
    )
