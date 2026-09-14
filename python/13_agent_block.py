"""Handle an agent-control refusal, then ask an admin to open the profile.

    export TONIA_API_KEY=tonia_sk_…
    python 13_agent_block.py
"""

from __future__ import annotations

import os
import sys

from tonia import AgentBlockError, Tonia

with Tonia(api_key=os.environ["TONIA_API_KEY"]) as client:
    listed = client.models.list()
    ids = [model["id"] for model in listed["data"]]
    if not ids:
        raise SystemExit("this key has no models; check the profile allowlist in the portal")
    try:
        client.chat.completions.create(
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
        print("Tool calls are allowed on this key's profile.")
    except AgentBlockError as err:
        print("Request blocked by Agent controls.", file=sys.stderr)
        print(
            "Ask a Workspace admin to open Policies → the bound profile → "
            "Advanced — Agent controls.",
            file=sys.stderr,
        )
        print(err.agent_block, file=sys.stderr)
        raise SystemExit(1) from err
