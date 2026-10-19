"""Translation desk helpers and locale resolution."""
from __future__ import annotations

import uuid

from apps.common.services.domain import DomainError
from apps.content.models import ContentEntry
from apps.content.services import create_revision
from apps.i18n_cms.models import LocaleConfig, TranslationJob


def ensure_locale_configs(publication, locales: list[str], default: str = "en") -> list[LocaleConfig]:
    created = []
    for loc in locales:
        cfg, _ = LocaleConfig.objects.get_or_create(
            publication=publication,
            locale=loc,
            defaults={
                "label": loc.upper(),
                "is_default": loc == default,
                "fallback_locale": default if loc != default else "",
                "url_prefix": loc if loc != default else "",
                "is_active": True,
            },
        )
        created.append(cfg)
    return created


def request_translation(
    source: ContentEntry,
    target_locale: str,
    *,
    assignee=None,
    notes: str = "",
) -> TranslationJob:
    if target_locale == source.locale:
        raise DomainError("Target locale must differ", code="same_locale")
    job, created = TranslationJob.objects.get_or_create(
        source_entry=source,
        target_locale=target_locale,
        defaults={
            "organization": source.organization,
            "assignee": assignee,
            "notes": notes,
            "status": TranslationJob.Status.PENDING,
        },
    )
    if not created and job.status == TranslationJob.Status.COMPLETE:
        raise DomainError("Translation already complete", code="already_complete")
    return job


def materialize_translation(job: TranslationJob, actor=None) -> ContentEntry:
    source = job.source_entry
    group = source.translation_group or uuid.uuid4()
    if not source.translation_group:
        source.translation_group = group
        source.save(update_fields=["translation_group"])

    target = ContentEntry.objects.create(
        organization=source.organization,
        publication=source.publication,
        content_type=source.content_type,
        title=source.title,
        slug=f"{source.slug}-{job.target_locale}",
        locale=job.target_locale,
        status=ContentEntry.Status.DRAFT,
        body=source.body,
        custom_fields=source.custom_fields,
        excerpt=source.excerpt,
        seo=source.seo,
        social=source.social,
        translation_group=group,
        source_entry=source,
        translation_status="in_progress",
        created_by=actor,
        updated_by=actor,
        path=f"/{job.target_locale}/{source.slug}",
    )
    target.authors.set(source.authors.all())
    target.terms.set(source.terms.all())
    create_revision(target, actor, change_summary=f"Translation from {source.locale}")
    job.target_entry = target
    job.status = TranslationJob.Status.IN_PROGRESS
    job.save()
    return target


def resolve_with_fallback(publication_id, slug: str, locale: str) -> dict | None:
    config = LocaleConfig.objects.filter(publication_id=publication_id, locale=locale).first()
    chain = [locale]
    if config and config.fallback_locale:
        chain.append(config.fallback_locale)
    if "en" not in chain:
        chain.append("en")

    for loc in chain:
        entry = ContentEntry.objects.filter(
            publication_id=publication_id,
            slug=slug,
            locale=loc,
            status=ContentEntry.Status.PUBLISHED,
            is_deleted=False,
        ).first()
        if entry:
            return {
                "requested_locale": locale,
                "resolved_locale": loc,
                "fallback_used": loc != locale,
                "entry_id": str(entry.id),
                "title": entry.title,
                "path": entry.path,
            }
    return None


def translation_group_map(entry: ContentEntry) -> list[dict]:
    if not entry.translation_group:
        return [
            {
                "id": str(entry.id),
                "locale": entry.locale,
                "status": entry.status,
                "translation_status": entry.translation_status,
            }
        ]
    siblings = ContentEntry.objects.filter(
        translation_group=entry.translation_group, is_deleted=False
    )
    return [
        {
            "id": str(s.id),
            "locale": s.locale,
            "status": s.status,
            "translation_status": s.translation_status,
            "title": s.title,
            "path": s.path,
        }
        for s in siblings
    ]
