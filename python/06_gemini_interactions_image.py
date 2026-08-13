"""Gemini image generate + edit on `/v1/interactions`.

    export TONIA_API_KEY=tonia_sk_…
    python 06_gemini_interactions_image.py
"""

from __future__ import annotations

import json
import os
from typing import Any

from tonia import InvalidRequestError, Tonia


def output_images(body: Any) -> list[dict[str, Any]]:
    if not isinstance(body, dict):
        return []
    root = body["interaction"] if isinstance(body.get("interaction"), dict) else body
    steps = root.get("steps") if isinstance(root, dict) else None
    if not isinstance(steps, list):
        return []
    out: list[dict[str, Any]] = []
    for step in steps:
        if not isinstance(step, dict) or step.get("type") != "model_output":
            continue
        content = step.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict):
                continue
            data = part.get("data")
            if not isinstance(data, str) or not data:
                continue
            mime = part.get("mime_type") if isinstance(part.get("mime_type"), str) else ""
            if part.get("type") == "image" or mime.startswith("image/"):
                out.append(part)
    return out


with Tonia(
    api_key=os.environ["TONIA_API_KEY"],
    timeout=300,
    default_headers={
        "HTTP-Referer": "https://github.com/tonia-router/sdk-examples",
        "X-Tonia-Title": "sdk-examples",
    },
) as client:
    listed = client.models.list()
    gemini_image = next(
        (
            item["id"]
            for item in listed["data"]
            if item["id"].startswith("gemini/") and "image" in item["id"].lower()
        ),
        None,
    )
    if not gemini_image:
        raise SystemExit("no Gemini image SKU on this key")
    try:
        client.images.generate(model=gemini_image, prompt="Draw a red fox")
        raise SystemExit("expected provider_requires_surface on /v1/images")
    except InvalidRequestError as err:
        if err.code != "provider_requires_surface":
            raise

    generated = client.interactions.create(
        model=gemini_image,
        input="Draw a red fox",
        stream=False,
    )
    images = output_images(generated)
    if not images:
        raise SystemExit("generate_image_missing")
    first = images[0]
    mime = first.get("mime_type") if isinstance(first.get("mime_type"), str) else "image/png"
    raw_b64 = first["data"]

    edited = client.interactions.create(
        model=gemini_image,
        stream=False,
        input=[
            {"type": "text", "text": "Make the fox sit"},
            {"type": "image", "mime_type": mime, "data": raw_b64},
        ],
    )
    print(
        json.dumps(
            {
                "generate_count": len(images),
                "edit_count": len(output_images(edited)),
            }
        )
    )
