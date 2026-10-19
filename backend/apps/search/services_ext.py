"""Search ranking, related content, and query normalization."""
from __future__ import annotations

import re

from django.db import connection
from django.db.models import Q

from apps.content.models import ContentEntry


STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with", "at", "by", "from",
}


def normalize_query(q: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9']+", (q or "").lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2]


def editorial_search(organization_id, q: str, *, publication_id=None, status=None, locale=None, limit=50):
    qs = ContentEntry.objects.filter(organization_id=organization_id, is_deleted=False)
    if publication_id:
        qs = qs.filter(publication_id=publication_id)
    if status:
        qs = qs.filter(status=status)
    if locale:
        qs = qs.filter(locale=locale)

    tokens = normalize_query(q)
    if not tokens:
        return []

    if connection.vendor == "postgresql":
        from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

        vector = SearchVector("title", weight="A") + SearchVector("excerpt", weight="B")
        query = SearchQuery(" ".join(tokens))
        qs = qs.annotate(rank=SearchRank(vector, query)).filter(rank__gte=0.5).order_by("-rank")
    else:
        clause = Q()
        for t in tokens:
            clause |= Q(title__icontains=t) | Q(excerpt__icontains=t) | Q(slug__icontains=t)
        qs = qs.filter(clause).order_by("-updated_at")

    return [
        {
            "id": str(e.id),
            "title": e.title,
            "status": e.status,
            "locale": e.locale,
            "path": e.path,
            "excerpt": e.excerpt,
            "updated_at": e.updated_at.isoformat(),
        }
        for e in qs.select_related("content_type")[:limit]
    ]


def audience_search(publication_id, q: str, locale: str = "en", limit: int = 30):
    tokens = normalize_query(q)
    qs = ContentEntry.objects.filter(
        publication_id=publication_id,
        locale=locale,
        status=ContentEntry.Status.PUBLISHED,
        is_deleted=False,
    )
    if not tokens:
        return []
    clause = Q()
    for t in tokens:
        clause |= Q(title__icontains=t) | Q(excerpt__icontains=t)
    qs = qs.filter(clause).order_by("-published_at")[:limit]
    return [
        {
            "id": str(e.id),
            "title": e.title,
            "slug": e.slug,
            "path": e.path,
            "excerpt": e.excerpt,
            "published_at": e.published_at.isoformat() if e.published_at else None,
        }
        for e in qs
    ]


def related_for(entry: ContentEntry, limit: int = 8) -> list[dict]:
    term_ids = list(entry.terms.values_list("id", flat=True))
    related = (
        ContentEntry.objects.filter(
            publication=entry.publication,
            status=ContentEntry.Status.PUBLISHED,
            is_deleted=False,
            terms__in=term_ids,
        )
        .exclude(pk=entry.pk)
        .distinct()
        .order_by("-published_at")[:limit]
    )
    explicit = entry.related_entries.filter(status=ContentEntry.Status.PUBLISHED)[:limit]
    seen = set()
    out = []
    for e in list(explicit) + list(related):
        if e.id in seen:
            continue
        seen.add(e.id)
        out.append({"id": str(e.id), "title": e.title, "slug": e.slug, "path": e.path, "excerpt": e.excerpt})
        if len(out) >= limit:
            break
    return out
