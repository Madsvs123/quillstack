"""Content assembly, SEO defaults, and bulk operations."""
from __future__ import annotations

import uuid
from typing import Any

from django.db import transaction
from django.utils.text import slugify

from apps.common.services.domain import (
    DomainError,
    extract_plain_text_from_tiptap,
    reading_time_minutes,
    unique_slug,
)
from apps.content.models import ContentEntry, ContentTypeDefinition, Taxonomy, Term
from apps.content.services import create_revision, estimate_word_count, validate_custom_fields


DEFAULT_ARTICLE_FIELDS = [
    {"api_key": "dek", "name": "Dek", "field_type": "text", "is_required": True, "sort_order": 0},
    {"api_key": "kicker", "name": "Kicker", "field_type": "text", "is_required": False, "sort_order": 1},
    {"api_key": "is_breaking", "name": "Breaking", "field_type": "boolean", "is_required": False, "sort_order": 2},
    {"api_key": "dateline", "name": "Dateline", "field_type": "text", "is_required": False, "sort_order": 3},
]


@transaction.atomic
def ensure_article_type(organization, publication=None) -> ContentTypeDefinition:
    from apps.content.models import FieldDefinition

    ctype, created = ContentTypeDefinition.objects.get_or_create(
        organization=organization,
        slug="article",
        defaults={
            "name": "Article",
            "publication": publication,
            "description": "Standard newsroom article",
            "is_translatable": True,
            "workflow_enabled": True,
            "allow_scheduling": True,
        },
    )
    if created or not ctype.fields.exists():
        for spec in DEFAULT_ARTICLE_FIELDS:
            FieldDefinition.objects.get_or_create(
                content_type=ctype,
                api_key=spec["api_key"],
                defaults=spec,
            )
    return ctype


@transaction.atomic
def create_entry_bundle(
    *,
    organization,
    publication,
    content_type: ContentTypeDefinition,
    title: str,
    body: dict | None = None,
    custom_fields: dict | None = None,
    locale: str = "en",
    created_by=None,
    authors: list | None = None,
    term_ids: list | None = None,
    seo: dict | None = None,
    social: dict | None = None,
) -> ContentEntry:
    custom_fields = custom_fields or {}
    errors = validate_custom_fields(content_type, custom_fields)
    if errors:
        raise DomainError("Custom field validation failed", code="validation", details=errors)

    def slug_exists(s):
        return ContentEntry.objects.filter(publication=publication, slug=s, locale=locale).exists()

    slug = unique_slug(title, slug_exists)
    body = body or {"type": "doc", "content": [{"type": "paragraph"}]}
    words = estimate_word_count(body)
    entry = ContentEntry.objects.create(
        organization=organization,
        publication=publication,
        content_type=content_type,
        title=title,
        slug=slug,
        locale=locale,
        body=body,
        custom_fields=custom_fields,
        excerpt=extract_plain_text_from_tiptap(body)[:280],
        seo=seo or {"title": title, "description": ""},
        social=social or {},
        created_by=created_by,
        updated_by=created_by,
        word_count=words,
        reading_time_minutes=reading_time_minutes(words),
        path=f"/{locale}/{slug}",
        translation_group=None,
    )
    if authors:
        entry.authors.set(authors)
    if term_ids:
        entry.terms.set(Term.objects.filter(id__in=term_ids))
    create_revision(entry, created_by, change_summary="Created via bundle")
    return entry


def apply_seo_defaults(entry: ContentEntry, publication_defaults: dict | None = None) -> ContentEntry:
    defaults = publication_defaults or (entry.publication.seo_defaults or {})
    seo = dict(entry.seo or {})
    seo.setdefault("title", entry.title)
    seo.setdefault("description", entry.excerpt or defaults.get("description", ""))
    seo.setdefault("robots", defaults.get("robots", "noindex,nofollow"))
    if not seo.get("canonical_url") and entry.publication.website_url:
        seo["canonical_url"] = f"{entry.publication.website_url.rstrip('/')}{entry.path}"
    entry.seo = seo
    social = dict(entry.social or {})
    social.setdefault("twitter_title", seo.get("title"))
    social.setdefault("facebook_title", seo.get("title"))
    entry.social = social
    entry.save(update_fields=["seo", "social", "updated_at"])
    return entry


def clone_entry(entry: ContentEntry, *, actor=None, locale: str | None = None) -> ContentEntry:
    locale = locale or entry.locale

    def slug_exists(s):
        return ContentEntry.objects.filter(publication=entry.publication, slug=s, locale=locale).exists()

    clone = ContentEntry.objects.create(
        organization=entry.organization,
        publication=entry.publication,
        content_type=entry.content_type,
        title=f"{entry.title} (copy)",
        slug=unique_slug(f"{entry.slug}-copy", slug_exists),
        locale=locale,
        status=entry.status,
        body=entry.body,
        custom_fields=entry.custom_fields,
        excerpt=entry.excerpt,
        seo=entry.seo,
        social=entry.social,
        featured_image=entry.featured_image,
        created_by=actor,
        updated_by=actor,
        translation_group=entry.translation_group,
        source_entry=entry if locale != entry.locale else None,
        path=f"/{locale}/{entry.slug}-copy",
    )
    clone.authors.set(entry.authors.all())
    clone.terms.set(entry.terms.all())
    create_revision(clone, actor, change_summary="Cloned")
    return clone


def ensure_default_taxonomies(organization, publication) -> dict[str, Taxonomy]:
    cats, _ = Taxonomy.objects.get_or_create(
        organization=organization,
        slug="categories",
        defaults={"name": "Categories", "publication": publication, "is_hierarchical": True},
    )
    tags, _ = Taxonomy.objects.get_or_create(
        organization=organization,
        slug="tags",
        defaults={
            "name": "Tags",
            "publication": publication,
            "is_hierarchical": False,
            "is_tag_like": True,
        },
    )
    for name in ["Politics", "Business", "Culture", "Technology", "Sports", "Opinion"]:
        Term.objects.get_or_create(
            taxonomy=cats,
            slug=slugify(name),
            defaults={"name": name},
        )
    return {"categories": cats, "tags": tags}


def entry_card(entry: ContentEntry) -> dict[str, Any]:
    return {
        "id": str(entry.id),
        "title": entry.title,
        "slug": entry.slug,
        "status": entry.status,
        "locale": entry.locale,
        "path": entry.path,
        "excerpt": entry.excerpt,
        "published_at": entry.published_at.isoformat() if entry.published_at else None,
        "updated_at": entry.updated_at.isoformat(),
        "word_count": entry.word_count,
        "authors": list(entry.authors.values_list("name", flat=True)),
        "terms": list(entry.terms.values_list("name", flat=True)),
    }
