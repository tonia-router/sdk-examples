"""Handle a policy block, then retry after a redact-mode profile in the portal.

    export TONIA_API_KEY=tonia_sk_…
    python 04_policy_block.py
"""

from __future__ import annotations

import os
import sys

from tonia import PolicyBlockError, Tonia

with Tonia(api_key=os.environ["TONIA_API_KEY"]) as client:
    listed = client.models.list()
    ids = [model["id"] for model in listed["data"]]
    if not ids:
        raise SystemExit("empty allowlist — do not guess a model id")
    try:
        client.chat.completions.create(
            model=ids[0],
            messages=[{"role": "user", "content": "…"}],
        )
    except PolicyBlockError as err:
        print("Request blocked by Workspace Policies.", file=sys.stderr)
        print(
            "Ask a Workspace admin to bind this key to a redact-mode profile "
            "(Policies → Profiles), then retry.",
            file=sys.stderr,
        )
        print(err.policy_block, file=sys.stderr)
        raise SystemExit(1) from err
