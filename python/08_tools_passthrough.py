"""Pass LLM tools through chat.completions. The SDK does not run a tool loop.

    export TONIA_API_KEY=tonia_sk_…
    python 08_tools_passthrough.py
"""

from __future__ import annotations

import json
import os

from tonia import Tonia

with Tonia(api_key=os.environ["TONIA_API_KEY"]) as client:
    listed = client.models.list()
    ids = [model["id"] for model in listed["data"]]
    if not ids:
        raise SystemExit("empty allowlist — do not guess a model id")
    completion = client.chat.completions.create(
        model=ids[0],
        messages=[{"role": "user", "content": "Weather in Montréal?"}],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Weather for a city",
                    "parameters": {
                        "type": "object",
                        "properties": {"city": {"type": "string"}},
                        "required": ["city"],
                    },
                },
            }
        ],
    )
    print(json.dumps(completion, indent=2))
