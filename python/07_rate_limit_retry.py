"""Handle admission 429. The SDK does not auto-retry.

    export TONIA_API_KEY=tonia_sk_…
    python 07_rate_limit_retry.py
"""

from __future__ import annotations

import os
import sys
import time

from tonia import (
    ApiError,
    EntitlementError,
    ManagedCredentialUnavailableError,
    RateLimitError,
    Tonia,
)


def once(client: Tonia, model: str) -> object:
    return client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Bonjour"}],
    )


with Tonia(api_key=os.environ["TONIA_API_KEY"]) as client:
    listed = client.models.list()
    ids = [model["id"] for model in listed["data"]]
    if not ids:
        raise SystemExit("this key has no models; check the profile allowlist in the portal")
    model = ids[0]
    try:
        print(once(client, model))
    except RateLimitError as err:
        if not err.retryable:
            raise
        wait = err.retry_after_seconds or 1
        print(
            f"Admission limited ({err.reason or err.code}, "
            f"scope={err.scope or '?'}). Waiting {wait}s.",
            file=sys.stderr,
        )
        time.sleep(wait)
        print(once(client, model))
    except EntitlementError as err:
        print(
            "Monthly quota reached. Wait Retry-After, or ask a Workspace "
            "admin to raise the plan."
            if err.retryable
            else "Budget exhausted. Do not retry until a Workspace admin adds budget.",
            file=sys.stderr,
        )
        print(err.code, err.entitlement_block, file=sys.stderr)
        raise SystemExit(1) from err
    except (ManagedCredentialUnavailableError, ApiError) as err:
        if isinstance(err, ApiError) and err.code != "audit_tip_contention":
            raise
        wait = err.retry_after_seconds or 1
        print(f"{err.code}: retryable, wait {wait}s.", file=sys.stderr)
        raise SystemExit(1) from err
