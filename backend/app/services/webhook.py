import httpx
from app.config import settings
from app.security.webhook import sign_payload

async def deliver_webhook(agent, payload):
    if not agent.webhook_url:
        return "SKIPPED_NO_WEBHOOK"
    # MVP demo secret. In production, store a unique encrypted secret per registered agent.
    timestamp, signature = sign_payload(payload, agent.api_key_hash or "development-webhook-secret")
    headers = {"Content-Type":"application/json", "X-AgentConnect-Timestamp":timestamp, "X-AgentConnect-Signature":signature}
    try:
        async with httpx.AsyncClient(timeout=settings.webhook_timeout_seconds) as client:
            response = await client.post(str(agent.webhook_url), json=payload, headers=headers)
            response.raise_for_status()
        return "DELIVERED"
    except Exception:
        return "FAILED"
