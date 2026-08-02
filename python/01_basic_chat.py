"""Basic chat with the official tonia client.

    export TONIA_API_KEY=tonia_sk_…
    python 01_basic_chat.py
"""

from __future__ import annotations

import json
import os

from tonia import Tonia

with Tonia(
    api_key=os.environ["TONIA_API_KEY"],
    default_headers={
        "HTTP-Referer": "https://github.com/tonia-router/sdk-examples",
        "X-Tonia-Title": "sdk-examples",
    },
) as client:
    completion = client.chat.completions.create(
        model="openai/gpt-4.1-mini",
        messages=[{"role": "user", "content": "Bonjour — une phrase courte."}],
    )
    print(json.dumps(completion, indent=2, ensure_ascii=False))
