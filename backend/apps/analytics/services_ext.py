"""Analytics rollups and content performance summaries."""
from __future__ import annotations

from datetime import datetime, timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.analytics.models import ContentPerformanceDaily, PageView
from apps.content.models import ContentEntry


def ingest_pageview(**payload) -> PageView:
    return PageView.objects.create(
        organization_id=payload.get("organization"),
        publication_id=payload.get("publication"),
        entry_id=payload.get("entry"),
        path=payload.get("path", ""),
        locale=payload.get("locale", "en").upper(),
        session_id=payload.get("session_id", ""),
        referrer=payload.get("referrer", ""),
        user_agent=(payload.get("user_agent") or "")[:255],
        country=payload.get("country", ""),
    )


def dashboard(organization_id, *, publication_id=None, days: int = 30) -> dict:
    since = timezone.now() - timedelta(days=days)
    views = PageView.objects.filter(organization_id=organization_id, occurred_at__gte=since)
    entries = ContentEntry.objects.filter(organization_id=organization_id, is_deleted=False)
    if publication_id:
        views = views.filter(publication_id=publication_id)
        entries = entries.filter(publication_id=publication_id)

    by_day = list(
        views.annotate(day=TruncDate("occurred_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    top_entries = list(
        views.filter(entry__isnull=False)
        .values("entry_id", "entry__title", "entry__slug")
        .annotate(views=Count("id"))
        .order_by("-views")[:15]
    )
    status_breakdown = list(entries.values("status").annotate(count=Count("id")).order_by("-count"))

    return {
        "window_days": days,
        "total_views": views.count(),
        "unique_sessions": views.exclude(session_id="").values("session_id").distinct().count(),
        "published_count": entries.filter(status=ContentEntry.Status.PUBLISHED).count(),
        "draft_count": entries.filter(status=ContentEntry.Status.DRAFT).count(),
        "scheduled_count": entries.filter(status=ContentEntry.Status.SCHEDULED).count(),
        "by_day": [
            {"day": row["day"].isoformat() if row["day"] else None, "count": row["count"]}
            for row in by_day
        ],
        "top_entries": top_entries,
        "status_breakdown": status_breakdown,
    }


def entry_performance(entry_id, days: int = 30) -> dict:
    since = timezone.now() - timedelta(days=days)
    views = PageView.objects.filter(entry_id=entry_id, occurred_at__gte=since)
    by_day = list(
        views.annotate(day=TruncDate("occurred_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    return {
        "entry_id": str(entry_id),
        "total_views": views.count(),
        "unique_sessions": views.exclude(session_id="").values("session_id").distinct().count(),
        "by_day": [
            {"day": row["day"].isoformat() if row["day"] else None, "count": row["count"]}
            for row in by_day
        ],
        "referrers": list(
            views.exclude(referrer="")
            .values("referrer")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        ),
    }


def rollup_daily(entry_id, day=None) -> ContentPerformanceDaily:
    day = day or timezone.now().date() - timedelta(days=1)
    start = timezone.make_aware(datetime.combine(day, datetime.min.time()))
    end = start + timedelta(days=1)
    views = PageView.objects.filter(entry_id=entry_id, occurred_at__gte=start, occurred_at__lt=end)
    obj, _ = ContentPerformanceDaily.objects.update_or_create(
        entry_id=entry_id,
        date=day,
        defaults={
            "views": views.count(),
            "unique_sessions": views.exclude(session_id="").values("session_id").distinct().count(),
        },
    )
    return obj
