"""Delivery packaging, preview links, and cache keys."""
from __future__ import annotations

from django.core.cache import cache
from django.utils import timezone

from apps.content.models import ContentEntry
from apps.delivery.cache import entry_cache_key, invalidate_entry_cache
from apps.delivery.models import APIKey, PreviewToken


PUBLIC_ENTRY_FIELDS = (
    "id",
    "title",
    "slug",
    "locale",
    "status",
    "body",
    "custom_fields",
    "excerpt",
    "seo",
    "social",
    "published_at",
    "updated_at",
    "word_count",
    "reading_time_minutes",
    "path",
    "canonical_url",
    "metadata",
)


def package_entry(entry: ContentEntry, *, include_draft_fields: bool = False) -> dict:
    data = {
        "id": str(entry.id),
        "title": entry.title,
        "slug": entry.slug,
        "locale": entry.locale,
        "status": entry.status,
        "body": entry.body,
        "custom_fields": entry.custom_fields,
        "excerpt": entry.excerpt,
        "seo": entry.seo,
        "social": entry.social,
        "published_at": entry.published_at.isoformat() if entry.published_at else None,
        "updated_at": entry.updated_at.isoformat(),
        "word_count": entry.word_count,
        "reading_time_minutes": entry.reading_time_minutes,
        "path": entry.path,
        "canonical_url": entry.canonical_url,
        "content_type": entry.content_type.slug,
        "authors": [
            {
                "id": str(a.id),
                "slug": a.slug,
                "display_name": a.display_name,
                "short_bio": a.short_bio,
            }
            for a in entry.authors.all()
        ],
        "terms": [
            {"id": str(t.id), "name": t.name, "slug": t.slug, "taxonomy": t.taxonomy.slug}
            for t in entry.terms.select_related("taxonomy")
        ],
        "related": [
            {"id": str(r.id), "title": r.title, "slug": r.slug, "path": r.path}
            for r in entry.related_entries.filter(status=ContentEntry.Status.PUBLISHED)[:8]
        ],
    }
    if entry.featured_image_id:
        img = entry.featured_image
        data["featured_image"] = {
            "id": str(img.id),
            "url": img.file.url if img.file else None,
            "alt_text": img.alt_text,
            "width": img.width,
            "height": img.height,
            "focal_x": img.focal_x,
            "focal_y": img.focal_y,
            "credit": img.credit,
            "copyright": img.copyright,
        }
    else:
        data["featured_image"] = None

    if include_draft_fields:
        data["revision_number"] = entry.revision_number
        data["scheduled_for"] = entry.scheduled_for.isoformat() if entry.scheduled_for else None
        data["embargo_until"] = entry.embargo_until.isoformat() if entry.embargo_until else None
    return data


def cached_package(entry: ContentEntry, ttl: int = 300) -> dict:
    key = entry_cache_key(entry)
    hit = cache.get(key)
    if hit:
        return hit
    data = package_entry(entry)
    cache.set(key, data, ttl)
    return data


def issue_preview(entry: ContentEntry, user=None, allow_draft: bool = False) -> PreviewToken:
    return PreviewToken.objects.create(entry=entry, created_by=user, allow_draft=allow_draft)


def api_key_can(api_key: APIKey, scope: str) -> bool:
    scopes = api_key.scopes or []
    return scope in scopes or "*" in scopes


def publish_side_effects(entry: ContentEntry) -> None:
    invalidate_entry_cache(entry)
    from apps.search.tasks import index_content_entry
    from apps.webhooks.tasks import dispatch_webhook_event

    index_content_entry.delay(str(entry.id))
    dispatch_webhook_event.delay(
        str(entry.organization_id),
        "content.published",
        {"id": str(entry.id), "slug": entry.slug, "locale": entry.locale},
    )


def list_published(
    *,
    publication_id,
    locale: str = "en",
    content_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    qs = ContentEntry.objects.filter(
        publication_id=publication_id,
        locale=locale,
        status=ContentEntry.Status.PUBLISHED,
        is_deleted=False,
    ).select_related("content_type", "featured_image").prefetch_related("authors", "terms")
    now = timezone.now()
    qs = qs.filter(models_q_no_embargo(now))
    if content_type:
        qs = qs.filter(content_type__slug=content_type)
    total = qs.count()
    start = page * page_size
    items = qs.order_by("published_at")[start : start + page_size]
    return {
        "count": total,
        "page": page,
        "page_size": page_size,
        "results": [package_entry(e) for e in items],
    }


def models_q_no_embargo(now):
    from django.db.models import Q

    return Q(embargo_until__isnull=True) | Q(embargo_until__lte=now)
