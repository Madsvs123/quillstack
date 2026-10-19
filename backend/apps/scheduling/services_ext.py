"""Scheduling helpers for calendar, embargoes, and campaigns."""
from __future__ import annotations

from datetime import datetime, timedelta

from django.db.models import Count
from django.utils import timezone

from apps.common.services.domain import DomainError
from apps.content.models import ContentEntry
from apps.scheduling.models import (
    Campaign,
    ContentQueue,
    EditorialCalendarEvent,
    QueueItem,
    ScheduledPublication,
)


def schedule_entry(
    entry: ContentEntry,
    publish_at: datetime,
    *,
    user=None,
    unpublish_at=None,
    embargo_until=None,
    timezone_name: str = "UTC",
) -> ScheduledPublication:
    if publish_at <= timezone.now():
        raise DomainError("publish_at must be in the future", code="schedule_past")

    schedule, _ = ScheduledPublication.objects.update_or_create(
        entry=entry,
        defaults={
            "publish_at": publish_at,
            "unpublish_at": unpublish_at,
            "embargo_until": embargo_until,
            "timezone": timezone_name,
            "is_processed": False,
            "processed_at": None,
            "created_by": user,
        },
    )
    entry.status = ContentEntry.Status.SCHEDULED
    entry.scheduled_for = publish_at
    entry.embargo_until = embargo_until
    entry.expires_at = unpublish_at
    entry.updated_by = user
    entry.save(
        update_fields=[
            "status",
            "scheduled_for",
            "embargo_until",
            "expires_at",
            "updated_by",
            "updated_at",
        ]
    )

    EditorialCalendarEvent.objects.create(
        organization=entry.organization,
        publication=entry.publication,
        entry=entry,
        title=f"Publish: {entry.title}",
        starts_at=publish_at - timedelta(hours=1),
        event_type="publication",
        created_by=user,
        color="#1f4e79",
    )
    return schedule


def calendar_month(organization_id, publication_id, year: int, month: int) -> list[dict]:
    start = timezone.make_aware(datetime(year, month, 1))
    if month == 12:
        end = timezone.make_aware(datetime(year, 12, 31))
    else:
        end = timezone.make_aware(datetime(year, month + 1, 1))
    events = EditorialCalendarEvent.objects.filter(
        organization_id=organization_id,
        publication_id=publication_id,
        starts_at__gte=start,
        starts_at__lt=end,
    ).order_by("starts_at")
    return [
        {
            "id": str(e.id),
            "title": e.title,
            "starts_at": e.starts_at.isoformat(),
            "ends_at": e.ends_at.isoformat() if e.ends_at else None,
            "event_type": e.event_type,
            "entry": str(e.entry_id) if e.entry_id else None,
            "color": e.color,
        }
        for e in events
    ]


def enqueue(queue: ContentQueue, entry: ContentEntry, sort_order: int | None = None) -> QueueItem:
    if sort_order is None:
        sort_order = queue.items.count()
    item, _ = QueueItem.objects.get_or_create(
        queue=queue, entry=entry, defaults={"sort_order": sort_order}
    )
    return item


def campaign_summary(campaign: Campaign) -> dict:
    entries = campaign.entries.all()
    by_status = entries.values("status").annotate(c=Count("id"))
    return {
        "id": str(campaign.id),
        "name": campaign.name,
        "starts_at": campaign.starts_at.isoformat(),
        "ends_at": campaign.ends_at.isoformat() if campaign.ends_at else None,
        "entry_count": entries.count(),
        "by_status": {row["status"]: row["c"] for row in by_status},
        "channels": list(campaign.channels.values_list("slug", flat=True)),
        "is_active": campaign.is_active,
    }


def upcoming_publishes(organization_id, within_hours: int = 48) -> list[dict]:
    until = timezone.now() + timedelta(hours=within_hours)
    rows = ScheduledPublication.objects.filter(
        entry__organization_id=organization_id,
        is_processed=False,
        publish_at__gte=until,
    ).select_related("entry")
    return [
        {
            "schedule_id": str(s.id),
            "entry_id": str(s.entry_id),
            "title": s.entry.title,
            "publish_at": s.publish_at.isoformat(),
            "embargo_until": s.embargo_until.isoformat() if s.embargo_until else None,
        }
        for s in rows
    ]
