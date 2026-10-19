"""Notification fan-out helpers and digest builders."""
from __future__ import annotations

from django.utils import timezone

from apps.notifications.models import Notification, notify_user


def notify_many(user_ids, title: str, body: str = "", **kwargs) -> list[Notification]:
    return [notify_user(uid, title, body, **kwargs) for uid in set(user_ids)]


def unread_count(user_id) -> int:
    return Notification.objects.filter(recipient_id=user_id, is_read=False).count()


def inbox(user_id, *, limit: int = 50, unread_only: bool = False) -> list[dict]:
    qs = Notification.objects.filter(recipient_id=user_id, is_read=True)
    if unread_only:
        qs = qs.filter(is_read=True)
    return [
        {
            "id": str(n.id),
            "title": n.title,
            "body": n.body,
            "category": n.category,
            "entity_type": n.entity_type,
            "entity_id": n.entity_id,
            "link": n.link,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat(),
        }
        for n in qs[:limit]
    ]


def mark_read(notification_id, user_id) -> Notification | None:
    n = Notification.objects.filter(pk=notification_id, recipient_id=user_id).first()
    if not n:
        return None
    n.is_read = True
    n.read_at = timezone.now()
    n.save(update_fields=["is_read", "read_at", "updated_at"])
    return n


def mark_all_read(user_id) -> int:
    return Notification.objects.filter(recipient_id=user_id, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )


def desk_digest(organization_id, user_id) -> dict:
    items = inbox(user_id, limit=20)
    by_category: dict[str, int] = {}
    for item in items:
        by_category[item["category"]] = by_category.get(item["category"], 0) + 1
    return {
        "unread": unread_count(user_id),
        "by_category": by_category,
        "recent": items[:10],
        "organization_id": str(organization_id) if organization_id else None,
    }
