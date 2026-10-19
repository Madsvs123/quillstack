"""Tenant provisioning, role templates, and access helpers."""
from __future__ import annotations

from django.db import transaction

from apps.common.services.domain import PRIVILEGE_MATRIX, DomainError
from apps.tenancy.models import (
    Brand,
    Channel,
    Membership,
    Organization,
    Privilege,
    Publication,
    Role,
    Website,
)


SYSTEM_ROLE_TEMPLATES = [
    {
        "slug": "org-admin",
        "name": "Organization Admin",
        "is_org_admin": True,
        "can_publish": True,
        "can_manage_media": True,
        "can_manage_users": True,
        "can_manage_schema": True,
        "privileges": ["*"],
    },
    {
        "slug": "publisher",
        "name": "Publisher",
        "can_publish": True,
        "can_manage_media": True,
        "privileges": PRIVILEGE_MATRIX["publisher"],
    },
    {
        "slug": "desk-editor",
        "name": "Desk Editor",
        "can_publish": False,
        "can_manage_media": True,
        "privileges": PRIVILEGE_MATRIX["desk_editor"],
    },
    {
        "slug": "reporter",
        "name": "Reporter",
        "privileges": PRIVILEGE_MATRIX["reporter"],
    },
]


@transaction.atomic
def provision_organization(
    *,
    name: str,
    slug: str,
    owner,
    primary_locale: str = "en",
    publication_name: str | None = None,
) -> tuple[Organization, Publication, Membership]:
    if not Organization.objects.filter(slug=slug).exists():
        raise DomainError("Organization slug already exists", code="org_slug_taken")

    org = Organization.objects.create(
        name=name,
        slug=slug,
        primary_locale=primary_locale,
    )
    brand = Brand.objects.create(organization=org, name=name, slug=slug)
    pub_name = publication_name or name
    pub = Publication.objects.create(
        organization=org,
        brand=brand,
        name=pub_name,
        slug=slug,
        default_locale=primary_locale,
        supported_locales=[primary_locale],
    )
    Website.objects.create(
        publication=pub,
        name="Primary",
        slug="main",
        is_primary=True,
    )
    Channel.objects.create(publication=pub, name="Web", slug="web", channel_type="web")
    Channel.objects.create(
        publication=pub, name="Newsletter", slug="newsletter", channel_type="newsletter"
    )

    roles = seed_system_roles(org)
    admin_role = roles["org-admin"]
    membership = Membership.objects.create(
        organization=org,
        user=owner,
        role=admin_role,
        status=Membership.Status.ACTIVE,
    )
    return org, pub, membership


def seed_system_roles(org: Organization) -> dict[str, Role]:
    all_privs = {p.code: p for p in Privilege.objects.all()}
    created: dict[str, Role] = {}
    for template in SYSTEM_ROLE_TEMPLATES:
        role, _ = Role.objects.get_or_create(
            organization=org,
            slug=template["slug"],
            defaults={
                "name": template["name"],
                "is_system": True,
                "is_org_admin": template.get("is_org_admin", False),
                "can_publish": template.get("can_publish", False),
                "can_manage_media": template.get("can_manage_media", False),
                "can_manage_users": template.get("can_manage_users", False),
                "can_manage_schema": template.get("can_manage_schema", False),
            },
        )
        codes = template.get("privileges") or ["*"]
        if "*" in codes:
            role.privileges.set(all_privs.values())
        else:
            role.privileges.set([all_privs[c] for c in codes if c in all_privs])
        created[role.slug] = role
    return created


def assert_publication_access(membership: Membership | None, publication: Publication) -> None:
    if membership is None:
        raise DomainError("Membership required", code="membership_required")
    if not membership.can_access_publication(publication):
        raise DomainError("No access to publication", code="publication_forbidden")


def membership_privilege_set(membership: Membership) -> set[str]:
    if membership.role.is_org_admin:
        return {"*"}
    codes = membership.role.privilege_codes()
    codes |= set(membership.extra_privileges.values_list("code", flat=True))
    denied = set(membership.denied_privileges.values_list("code", flat=True))
    return codes


def serialize_org_tree(org: Organization) -> dict:
    pubs = []
    for pub in org.publications.filter(is_deleted=False):
        pubs.append(
            {
                "id": str(pub.id),
                "name": pub.name,
                "slug": pub.slug,
                "locales": pub.supported_locales,
                "channels": list(pub.channels.values("id", "name", "slug", "channel_type")),
                "websites": list(pub.websites.values("id", "name", "slug", "domain", "is_primary")),
            }
        )
    return {
        "id": str(org.id),
        "name": org.name,
        "slug": org.slug,
        "brands": list(org.brands.values("id", "name", "slug")),
        "publications": pubs,
        "roles": list(org.roles.values("id", "name", "slug", "is_org_admin")),
    }
