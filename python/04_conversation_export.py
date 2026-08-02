"""Export conversation history (member app_session key + chat_history plan).

    export TONIA_API_KEY=tonia_sk_…
    python 04_conversation_export.py
"""

from __future__ import annotations

import json
import os

from tonia import Tonia

with Tonia(api_key=os.environ["TONIA_API_KEY"]) as client:
    exported = client.conversations.export()
    print(json.dumps(exported, indent=2, ensure_ascii=False))
