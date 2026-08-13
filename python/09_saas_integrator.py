"""SaaS integrator: you store history, meter usage, watch limits.

tonia Pass does not keep SDK chat threads. Billing, seats, and API keys
stay in the portal (https://portal.tonia.ca).

    export TONIA_API_KEY=tonia_sk_…
    python 09_saas_integrator.py
"""

from __future__ import annotations

import os
import sys

from tonia import EntitlementError, RateLimitError, Tonia


def assistant_text(body: object) -> str:
    if not isinstance(body, dict):
        return ""
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        return ""
    message = choices[0].get("message")
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    return content.strip() if isinstance(content, str) else ""


def usage_of(body: object) -> dict[str, int | None]:
    usage = body.get("usage") if isinstance(body, dict) else None
    if not isinstance(usage, dict):
        return {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}
    prompt = usage.get("prompt_tokens", usage.get("input_tokens"))
    completion = usage.get("completion_tokens", usage.get("output_tokens"))
    total = usage.get("total_tokens")
    return {
        "prompt_tokens": prompt if isinstance(prompt, int) else None,
        "completion_tokens": completion if isinstance(completion, int) else None,
        "total_tokens": total if isinstance(total, int) else None,
    }


with Tonia(
    api_key=os.environ["TONIA_API_KEY"],
    default_headers={
        "HTTP-Referer": "https://github.com/tonia-router/sdk-examples",
        "X-Tonia-Title": "sdk-examples",
    },
) as client:
    listed = client.models.list()
    ids = [model["id"] for model in listed["data"]]
    if not ids:
        raise SystemExit("empty allowlist — do not guess a model id")
    model = ids[0]

    # Stand-in for your database. Pass does not store this for the SDK.
    thread: list[dict[str, str]] = [
        {"role": "user", "content": "Remember this word: maple. Reply only: ok"},
    ]
    try:
        first = client.chat.completions.create(
            model=model, max_tokens=8, messages=thread
        )
        thread.append({"role": "assistant", "content": assistant_text(first) or "ok"})
        thread.append(
            {
                "role": "user",
                "content": "Reply with only the word I asked you to remember.",
            }
        )
        second = client.chat.completions.create(
            model=model, max_tokens=16, messages=thread
        )
    except RateLimitError as err:
        print(
            f"Admission limited ({err.reason or err.code}). "
            f"Wait {err.retry_after_seconds or 1}s, then retry once.",
            file=sys.stderr,
        )
        raise SystemExit(1) from err
    except EntitlementError as err:
        print(
            "Monthly quota reached. Wait Retry-After, or raise the plan in the portal."
            if err.retryable
            else "Budget exhausted. Do not retry until a Workspace admin adds credit.",
            file=sys.stderr,
        )
        raise SystemExit(1) from err

    # last_limits is set only when usage is ≥ 80% of quota/budget.
    print(
        {
            "turns": len(thread),
            "usage": usage_of(second),
            "last_limits": (
                None
                if client.last_limits is None
                else {
                    "warning": client.last_limits.warning,
                    "kind": client.last_limits.kind,
                    "remaining": client.last_limits.remaining,
                    "period_ends_at": client.last_limits.period_ends_at,
                }
            ),
        }
    )
