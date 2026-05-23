"""Push Workflow Auth Business config (persona, first message) into the Vapi assistant.

When the dashboard owner edits `voice_persona` or `name`, the Vapi-side
`firstMessage` should follow. This module performs that sync via Vapi REST API.

Vapi assistant ID is stored on Business (added in this change). If unset, sync
is a no-op — useful for dev/test where a Vapi assistant hasn't been provisioned.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

VAPI_API = "https://api.vapi.ai"


def first_message(persona: str, business_name: str) -> str:
    """Compose the assistant's opening line."""
    persona = (persona or "Mary").strip() or "Mary"
    business_name = (business_name or "").strip()
    if business_name:
        return f"Hi, this is {persona} with {business_name}. Thanks for calling, how can I help you today?"
    return f"Hi, this is {persona}. Thanks for calling, how can I help you today?"


def sync_assistant(business) -> dict[str, Any]:
    """PATCH the Vapi assistant linked to this Business.

    Returns {success: bool, stubbed?: bool, status?: int, error?: str}.

    Stubs out (no error) when:
    - business.vapi_assistant_id is empty (nothing to sync).
    - business.resolved_vapi_key is empty (not configured).
    """
    assistant_id = (getattr(business, "vapi_assistant_id", "") or "").strip()
    api_key = (getattr(business, "resolved_vapi_key", "") or "").strip()
    if not assistant_id or not api_key:
        logger.info(
            "[VAPI SYNC STUB] biz=%s assistant=%s key_set=%s",
            getattr(business, "id", None), bool(assistant_id), bool(api_key),
        )
        return {"success": True, "stubbed": True}

    try:
        import requests  # noqa: WPS433
    except ImportError:
        logger.warning("requests not installed — cannot sync Vapi assistant")
        return {"success": False, "error": "requests not installed"}

    persona = (getattr(business, "voice_persona", "") or "Mary").strip() or "Mary"
    body = {
        "name": f"{business.name} · {persona}",
        "firstMessage": first_message(persona, business.name),
    }
    try:
        resp = requests.patch(
            f"{VAPI_API}/assistant/{assistant_id}",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=10,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("[VAPI SYNC ERROR] biz=%s err=%s", business.id, exc)
        return {"success": False, "error": str(exc)}

    if resp.status_code >= 400:
        logger.error("[VAPI SYNC HTTP %d] biz=%s body=%s", resp.status_code, business.id, resp.text[:300])
        return {"success": False, "status": resp.status_code, "error": resp.text[:300]}

    logger.info("[VAPI SYNC OK] biz=%s assistant=%s", business.id, assistant_id)
    return {"success": True, "status": resp.status_code}
