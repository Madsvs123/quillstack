"""Webhook signing, retry policy, and delivery inspection."""
from __future__ import annotations

import hashlib
import hmac
import json
from datetime import timedelta

from django.utils import timezone

from apps.webhooks.models import WebhookDelivery, WebhookEndpoint


SUPPORTED_EVENTS = [
    "content.created",
    "content.updated",
    "content.published",
    "content.unpublished",
    "content.archived",
    "content.expired",
    "media.uploaded",
    "schedule.processed",
    "translation.completed",
    "*",
]


def sign_body(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def verify_signature(secret: str, body: bytes, signature: str) -> bool:
    expected = sign_body(secret, body)
    return hmac.compare_digest(expected, signature or "")


def build_payload(event: str, data: dict, organization_id: str) -> dict:
    return {
        "event": event,
        "data": data,
        "organization_id": organization_id,
        "sent_at": timezone.now().isoformat(),
        "version": "2024-08-01",
    }


def endpoint_matches(endpoint: WebhookEndpoint, event: str) -> bool:
    events = endpoint.events or []
    return bool(endpoint.is_active) and (event in events or "*" in events)


def list_endpoints(organization_id) -> list[dict]:
    return [
        {
            "id": str(e.id),
            "name": e.name,
            "url": e.url,
            "events": e.events,
            "is_active": e.is_active,
            "created_at": e.created_at.isoformat(),
        }
        for e in WebhookEndpoint.objects.filter(organization_id=organization_id)
    ]


def delivery_log(organization_id, *, limit: int = 50) -> list[dict]:
    rows = WebhookDelivery.objects.filter(endpoint__organization_id=organization_id).select_related(
        "endpoint"
    )[:limit]
    return [
        {
            "id": str(d.id),
            "endpoint": d.endpoint.name,
            "event": d.event,
            "success": d.success,
            "response_status": d.response_status,
            "attempt": d.attempt,
            "created_at": d.created_at.isoformat(),
        }
        for d in rows
    ]


def next_retry_delay(attempt: int) -> timedelta:
    # exponential backoff: 1m, 2m, 4m, 8m, 16m
    minutes = min(2 ** max(attempt - 1, 0), 60)
    return timedelta(minutes=minutes)


def schedule_retry(delivery: WebhookDelivery) -> WebhookDelivery:
    delivery.attempt += 1
    delivery.next_retry_at = timezone.now() + next_retry_delay(delivery.attempt)
    delivery.save(update_fields=["attempt", "next_retry_at", "updated_at"])
    return delivery


def serialize_for_test(endpoint: WebhookEndpoint, event: str = "content.published") -> dict:
    payload = build_payload(event, {"id": "00000000-0000-0000-0000-000000000001", "dry_run": True}, str(endpoint.organization_id))
    body = json.dumps(payload).encode()
    return {
        "url": endpoint.url,
        "headers": {
            "Content-Type": "application/json",
            "X-QuillStack-Event": event,
            "X-QuillStack-Signature": sign_body(endpoint.secret, body),
            **(endpoint.headers or {}),
        },
        "payload": payload,
    }
