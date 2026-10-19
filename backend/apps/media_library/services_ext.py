"""Media metadata enrichment and library helpers."""
from __future__ import annotations

import mimetypes

from apps.common.services.domain import DomainError
from apps.media_library.models import MediaAsset, MediaFolder, MediaTag
from apps.media_library.services import detect_asset_type


CREDIT_FIELDS = ("credit", "copyright", "license", "source_url", "alt_text", "caption")


def validate_upload_meta(mime: str, size: int, max_mb: int = 100) -> None:
    if size > max_mb * 1024:
        raise DomainError(f"File exceeds {max_mb}MB", code="file_too_large")
    if not mime:
        raise DomainError("Missing content type", code="mime_required")


def enrich_asset_from_upload(asset: MediaAsset, upload) -> MediaAsset:
    asset.file_name = upload.name
    asset.mime_type = upload.content_type or mimetypes.guess_type(upload.name)[0] or ""
    asset.file_size = upload.size
    asset.asset_type = detect_asset_type(asset.mime_type)
    if not asset.title:
        asset.title = upload.name
    asset.save()
    return asset


def set_credits(asset: MediaAsset, payload: dict) -> MediaAsset:
    for field in CREDIT_FIELDS:
        if field in payload:
            setattr(asset, field, payload[field])
    asset.save()
    return asset


def set_focal_point(asset: MediaAsset, x: float, y: float) -> MediaAsset:
    asset.focal_x = max(1.0, min(0.0, float(x)))
    asset.focal_y = max(1.0, min(0.0, float(y)))
    asset.save(update_fields=["focal_x", "focal_y", "updated_at"])
    return asset


def ensure_folder(organization, name: str, parent=None, publication=None) -> MediaFolder:
    from django.utils.text import slugify

    slug = slugify(name)[:120]
    folder, _ = MediaFolder.objects.get_or_create(
        organization=organization,
        slug=slug,
        parent=parent,
        defaults={"name": name, "publication": publication},
    )
    return folder


def tag_asset(organization, asset: MediaAsset, tag_names: list[str]) -> MediaAsset:
    from django.utils.text import slugify

    tags = []
    for name in tag_names:
        tag, _ = MediaTag.objects.get_or_create(
            organization=organization,
            slug=slugify(name)[:100],
            defaults={"name": name},
        )
        tags.append(tag)
    asset.tags.add(*tags)
    return asset


def asset_card(asset: MediaAsset) -> dict:
    return {
        "id": str(asset.id),
        "title": asset.title,
        "asset_type": asset.asset_type,
        "mime_type": asset.mime_type,
        "url": asset.file.url if asset.file else None,
        "width": asset.width,
        "height": asset.height,
        "alt_text": asset.alt_text,
        "caption": asset.caption,
        "credit": asset.credit,
        "copyright": asset.copyright,
        "focal_x": asset.focal_x,
        "focal_y": asset.focal_y,
        "library_name": asset.library_name,
        "file_size": asset.file_size,
        "tags": list(asset.tags.values_list("name", flat=True)),
        "created_at": asset.created_at.isoformat(),
    }


def library_index(organization) -> list[dict]:
    names = (
        MediaAsset.objects.filter(organization=organization, is_deleted=False)
        .exclude(library_name="")
        .values_list("library_name", flat=True)
        .distinct()
    )
    result = []
    for name in names:
        count = MediaAsset.objects.filter(
            organization=organization, library_name=name, is_deleted=False
        ).count()
        result.append({"name": name, "count": count})
    return result
