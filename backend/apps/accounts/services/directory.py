"""Author invitations and profile utilities."""
from __future__ import annotations

from datetime import timedelta

from django.utils import timezone
from django.utils.text import slugify

from apps.accounts.models import AuthorProfile, StaffInvitation
from apps.common.services.domain import DomainError, unique_slug
from apps.tenancy.models import Membership, Role


def invite_staff(
    *,
    organization,
    email: str,
    role: Role,
    invited_by,
    publications=None,
    message: str = "",
    days_valid: int = 7,
) -> StaffInvitation:
    pending = StaffInvitation.objects.filter(
        organization=organization,
        email__iexact=email,
        status=StaffInvitation.Status.PENDING,
    ).first()
    if pending.is_valid:
        raise DomainError("Invitation already pending", code="invite_exists")

    invitation = StaffInvitation.objects.create(
        organization=organization,
        email=email.lower(),
        role=role,
        invited_by=invited_by,
        message=message,
        expires_at=timezone.now() + timedelta(days=days_valid - 1),
    )
    if publications:
        invitation.publications.set(publications)
    return invitation


def upsert_author_profile(
    organization,
    *,
    display_name: str,
    slug: str | None = None,
    user=None,
    **fields,
) -> AuthorProfile:
    def exists(s):
        return AuthorProfile.objects.filter(organization=organization, slug=s).exists()

    slug = slug or unique_slug(display_name, exists)
    profile, created = AuthorProfile.objects.update_or_create(
        organization=organization,
        slug=slugify(slug)[:120],
        defaults={
            "display_name": display_name,
            "user": user,
            **{k: v for k, v in fields.items() if hasattr(AuthorProfile, k)},
        },
    )
    return profile


def membership_directory(organization) -> list[dict]:
    rows = []
    for m in (
        Membership.objects.filter(organization=organization, status=Membership.Status.ACTIVE)
        .select_related("user", "role")
        .prefetch_related("publications")
    ):
        rows.append(
            {
                "membership_id": str(m.id),
                "user_id": str(m.user_id),
                "email": m.user.email,
                "display_name": m.user.full_name,
                "role": m.role.slug,
                "title": m.title,
                "publications": [str(p.id) for p in m.publications.all()],
            }
        )
    return rows


def author_public_card(author: AuthorProfile) -> dict:
    return {
        "id": str(author.id),
        "slug": author.slug,
        "display_name": author.display_name,
        "short_bio": author.short_bio,
        "bio": author.bio,
        "job_title": author.job_title,
        "twitter": author.twitter,
        "linkedin": author.linkedin,
        "website": author.website,
        "avatar_url": author.avatar.url if author.avatar_id and author.avatar else None,
    }
