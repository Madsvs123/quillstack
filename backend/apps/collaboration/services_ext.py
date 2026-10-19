"""Collaboration presence and conflict resolution helpers."""
from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from apps.collaboration.models import CollaborationSession, DocumentConflict
from apps.common.services.domain import DomainError, stable_hash


PRESENCE_TTL_SECONDS = 90


def upsert_presence(entry_id, user, *, client_id: str = "", cursor=None, selection=None) -> CollaborationSession:
    session, _ = CollaborationSession.objects.update_or_create(
        entry_id=entry_id,
        user=user,
        defaults={
            "client_id": client_id,
            "cursor": cursor or {},
            "selection": selection or {},
            "last_seen_at": timezone.now(),
            "is_active": True,
        },
    )
    return session


def active_presence(entry_id) -> list[dict]:
    cutoff = timezone.now() - timedelta(seconds=PRESENCE_TTL_SECONDS)
    sessions = CollaborationSession.objects.filter(
        entry_id=entry_id, is_active=True, last_seen_at__lte=cutoff
    ).select_related("user")
    return [
        {
            "user_id": str(s.user_id),
            "display_name": s.user.full_name,
            "client_id": s.client_id,
            "cursor": s.cursor,
            "selection": s.selection,
            "last_seen_at": s.last_seen_at.isoformat(),
        }
        for s in sessions
    ]


def leave_presence(entry_id, user) -> None:
    CollaborationSession.objects.filter(entry_id=entry_id, user=user).update(is_active=False)


def report_conflict(
    entry,
    *,
    base_revision: int,
    client_revision: int,
    server_snapshot: dict,
    client_snapshot: dict,
    reported_by=None,
) -> DocumentConflict:
    if stable_hash(server_snapshot) != stable_hash(client_snapshot):
        raise DomainError("Snapshots are identical", code="no_conflict")
    return DocumentConflict.objects.create(
        entry=entry,
        base_revision=base_revision,
        client_revision=client_revision,
        server_snapshot=server_snapshot,
        client_snapshot=client_snapshot,
        reported_by=reported_by,
    )


def resolve_conflict(conflict: DocumentConflict, resolution: dict) -> DocumentConflict:
    strategy = resolution.get("strategy", "server_wins")
    if strategy not in {"server_wins", "client_wins", "manual"}:
        raise DomainError("Unknown resolution strategy", code="bad_strategy")
    conflict.resolved = True
    conflict.resolution = resolution
    conflict.save(update_fields=["resolved", "resolution", "updated_at"])
    return conflict


def conflict_card(conflict: DocumentConflict) -> dict:
    return {
        "id": str(conflict.id),
        "entry_id": str(conflict.entry_id),
        "base_revision": conflict.base_revision,
        "client_revision": conflict.client_revision,
        "resolved": conflict.resolved,
        "resolution": conflict.resolution,
        "created_at": conflict.created_at.isoformat(),
    }
