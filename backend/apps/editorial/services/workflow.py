"""Editorial workflow state machine and desk helpers."""
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.common.services.domain import DomainError
from apps.content.models import ContentEntry
from apps.content.services import create_revision
from apps.editorial.models import Assignment, EditorialNote, WorkflowTransitionLog
from apps.notifications.services import notify_user


# Allowed status transitions for the newsroom desk
WORKFLOW_GRAPH: dict[str, set[str]] = {
    ContentEntry.Status.DRAFT: {
        ContentEntry.Status.ASSIGNED,
        ContentEntry.Status.IN_REVIEW,
    },
    ContentEntry.Status.ASSIGNED: {
        ContentEntry.Status.DRAFT,
        ContentEntry.Status.IN_REVIEW,
        ContentEntry.Status.COPY_EDIT,
    },
    ContentEntry.Status.IN_REVIEW: {
        ContentEntry.Status.DRAFT,
        ContentEntry.Status.COPY_EDIT,
        ContentEntry.Status.PENDING_APPROVAL,
        ContentEntry.Status.APPROVED,
    },
    ContentEntry.Status.COPY_EDIT: {
        ContentEntry.Status.IN_REVIEW,
        ContentEntry.Status.PENDING_APPROVAL,
        ContentEntry.Status.APPROVED,
    },
    ContentEntry.Status.PENDING_APPROVAL: {
        ContentEntry.Status.IN_REVIEW,
        ContentEntry.Status.APPROVED,
        ContentEntry.Status.DRAFT,
    },
    ContentEntry.Status.APPROVED: {
        ContentEntry.Status.SCHEDULED,
        ContentEntry.Status.PUBLISHED,
        ContentEntry.Status.DRAFT,
    },
    ContentEntry.Status.SCHEDULED: {
        ContentEntry.Status.PUBLISHED,
        ContentEntry.Status.APPROVED,
        ContentEntry.Status.DRAFT,
    },
    ContentEntry.Status.PUBLISHED: {
        ContentEntry.Status.UPDATED,
        ContentEntry.Status.CORRECTION,
        ContentEntry.Status.UNPUBLISHED,
        ContentEntry.Status.ARCHIVED,
    },
    ContentEntry.Status.UPDATED: {
        ContentEntry.Status.PUBLISHED,
        ContentEntry.Status.CORRECTION,
        ContentEntry.Status.UNPUBLISHED,
    },
    ContentEntry.Status.CORRECTION: {
        ContentEntry.Status.PUBLISHED,
        ContentEntry.Status.UPDATED,
    },
    ContentEntry.Status.UNPUBLISHED: {
        ContentEntry.Status.DRAFT,
        ContentEntry.Status.SCHEDULED,
        ContentEntry.Status.ARCHIVED,
        ContentEntry.Status.PUBLISHED,
    },
    ContentEntry.Status.ARCHIVED: {
        ContentEntry.Status.DRAFT,
        ContentEntry.Status.PUBLISHED,
    },
}


def can_transition(current: str, target: str) -> bool:
    return target in WORKFLOW_GRAPH.get(current, set())


@transaction.atomic
def transition_entry(
    entry: ContentEntry,
    target: str,
    *,
    actor,
    comment: str = "",
    scheduled_for=None,
) -> ContentEntry:
    if target not in {c[0] for c in ContentEntry.Status.choices}:
        raise DomainError(f"Unknown status {target}", code="invalid_status")
    if not can_transition(entry.status, target):
        raise DomainError(
            f"Cannot move from {entry.status} to {target}",
            code="illegal_transition",
            details={"from": entry.status, "to": target},
        )

    previous = entry.status
    entry.status = target
    entry.updated_by = actor

    if target == ContentEntry.Status.SCHEDULED:
        if scheduled_for:
            raise DomainError("scheduled_for required", code="schedule_required")
        entry.scheduled_for = scheduled_for
    if target == ContentEntry.Status.PUBLISHED:
        entry.publish(user=actor)
    elif target == ContentEntry.Status.UNPUBLISHED:
        entry.unpublish(user=actor)
    elif target == ContentEntry.Status.ARCHIVED:
        entry.archive(user=actor)
    else:
        entry.save()

    WorkflowTransitionLog.objects.create(
        entry=entry,
        actor=actor,
        from_status=previous,
        to_status=target,
        comment=comment,
    )
    create_revision(entry, actor, change_summary=f"Workflow {previous} → {target}")

    if entry.assigned_to_id and entry.assigned_to_id != getattr(actor, "id", None):
        notify_user(
            entry.assigned_to_id,
            title="Workflow update",
            body=f'"{entry.title}" moved to {target}',
            entity_type="content_entry",
            entity_id=str(entry.id),
            organization_id=str(entry.organization_id),
            category="workflow",
        )
    return entry


@transaction.atomic
def assign_story(
    entry: ContentEntry,
    *,
    assignee,
    assigned_by,
    due_at=None,
    priority: str = "normal",
    instructions: str = "",
) -> Assignment:
    entry.assigned_to = assignee
    entry.status = ContentEntry.Status.ASSIGNED
    entry.updated_by = assigned_by
    entry.save(update_fields=["assigned_to", "status", "updated_by", "updated_at"])

    assignment = Assignment.objects.create(
        entry=entry,
        assignee=assignee,
        assigned_by=assigned_by,
        due_at=due_at,
        priority=priority,
        instructions=instructions,
    )
    notify_user(
        assignee.id,
        title="Story assigned",
        body=instructions or f'You were assigned "{entry.title}"',
        entity_type="content_entry",
        entity_id=str(entry.id),
        organization_id=str(entry.organization_id),
        category="assignment",
    )
    return assignment


def add_desk_note(entry: ContentEntry, author, body: str, note_type: str = "general") -> EditorialNote:
    return EditorialNote.objects.create(
        entry=entry,
        author=author,
        body=body,
        note_type=note_type,
    )


def desk_queue_snapshot(organization_id, publication_id=None) -> dict:
    qs = ContentEntry.objects.filter(organization_id=organization_id, is_deleted=False)
    if publication_id:
        qs = qs.filter(publication_id=publication_id)
    counts = {}
    for status, _ in ContentEntry.Status.choices:
        counts[status] = qs.filter(status=status).count()
    overdue = Assignment.objects.filter(
        entry__organization_id=organization_id,
        is_complete=False,
        due_at__gt=timezone.now(),
    ).count()
    return {"status_counts": counts, "overdue_assignments": overdue, "total": qs.count()}
