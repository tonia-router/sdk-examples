"""Handle a policy block, then retry after a redact-mode profile in the portal.

    export TONIA_API_KEY=tonia_sk_…
    python 05_policy_block.py
"""

from __future__ import annotations

import os
import sys

from tonia import PolicyBlockError, Tonia

with Tonia(api_key=os.environ["TONIA_API_KEY"]) as client:
    try:
        client.chat.completions.create(
            model="openai/gpt-4.1-mini",
            messages=[{"role": "user", "content": "…"}],
        )
    except PolicyBlockError as err:
        print("Blocked by policy.", file=sys.stderr)
        print(
            "Configure a redact-mode profile in the portal, bind this key, then retry.",
            file=sys.stderr,
        )
        print(err.policy_block, file=sys.stderr)
        raise SystemExit(1) from err
