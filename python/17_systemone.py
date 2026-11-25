"""System One on tenant ``/v1/systemone``.

Use the escape hatch. There is no typed ``systemone.create`` helper.
``stream`` is not supported. Ask and clavarde do not list these ids. Use a portal API key.

    export TONIA_API_KEY=tonia_sk_…
    python 17_systemone.py
"""

from __future__ import annotations

import json
import os

from tonia import Tonia


def _caps(item: dict[str, object]) -> list[str]:
    raw = item.get("capabilities")
    return [str(cap) for cap in raw] if isinstance(raw, list) else []


def _surface(item: dict[str, object]) -> dict[str, object]:
    raw = item.get("surface")
    return raw if isinstance(raw, dict) else {}


def is_systemone(item: dict[str, object]) -> bool:
    if _surface(item).get("family") == "systemone":
        return True
    if "systemone" in _caps(item):
        return True
    return str(item["id"]).endswith("jev-latest")


with Tonia(
    api_key=os.environ["TONIA_API_KEY"],
    default_headers={
        "HTTP-Referer": "https://github.com/tonia-router/sdk-examples",
        "X-Tonia-Title": "sdk-examples",
    },
) as client:
    listed = client.models.list()
    model = next((item["id"] for item in listed["data"] if is_systemone(item)), None)
    if not model:
        raise SystemExit("no listed systemone on this key")
    body = client.request(
        "POST",
        "/v1/systemone",
        {
            "model": model,
            "state": "The sky is blue.",
            "questions": {
                "color": {"type": "noul", "instructions": "Is the sky blue?"},
                "kind": {
                    "type": "choice",
                    "criteria": {"sky": {"description": "open air"}, "sea": {"description": "water"}},
                },
                "confidence": {
                    "type": "score",
                    "instructions": "How sure is this public fixture?",
                    "criteria": ["Low", "Medium", "High"],
                },
            },
        },
    )
    answers = body.get("answers") or {}
    print(
        json.dumps(
            {
                "model": model,
                "answer_count": len(answers) if isinstance(answers, dict) else 0,
                "usage": body.get("usage"),
            },
            indent=2,
        )
    )
