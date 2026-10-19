"""Shared domain helpers used across QuillStack apps."""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Iterable

from django.utils.text import slugify


SLUG_SAFE = re.compile(r"[^a-z0-9\-]+")


def unique_slug(base: str, exists_fn, *, max_len: int = 120) -> str:
    """Generate a unique slug by appending -2, -3, … when needed."""
    root = slugify(base)[: max_len - 8] or "item"
    candidate = root
    n = 2
    while exists_fn(candidate):
        candidate = f"{root}-{n}"
        n += 1
    return candidate[:max_len]


def deep_merge(base: dict, overlay: dict) -> dict:
    """Recursively merge overlay into a copy of base."""
    out = dict(base or {})
    for key, value in (overlay or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def chunked(items: Iterable, size: int = 100):
    batch: list = []
    for item in items:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def redact_secrets(data: dict, keys: Iterable[str] | None = None) -> dict:
    sensitive = set(keys or ("password", "secret", "token", "api_key", "key_hash"))
    cleaned = {}
    for k, v in data.items():
        if k.lower() in sensitive or any(s in k.lower() for s in sensitive):
            cleaned[k] = "***"
        elif isinstance(v, dict):
            cleaned[k] = redact_secrets(v, sensitive)
        else:
            cleaned[k] = v
    return cleaned


class DomainError(Exception):
    """Raised for recoverable domain rule violations."""

    def __init__(self, message: str, *, code: str = "domain_error", details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}


STATUS_COLORS = {
    "draft": "#9a9488",
    "assigned": "#1f4e79",
    "in_review": "#b8860b",
    "copy_edit": "#b8860b",
    "pending_approval": "#c45c26",
    "approved": "#2f6f4e",
    "scheduled": "#1f4e79",
    "published": "#2f6f4e",
    "updated": "#2f6f4e",
    "correction": "#8b3a3a",
    "unpublished": "#8b3a3a",
    "archived": "#5c5a54",
}


PRIVILEGE_MATRIX = {
    "reporter": [
        "content.read",
        "content.create",
        "content.edit",
        "media.read",
        "media.upload",
    ],
    "desk_editor": [
        "content.read",
        "content.create",
        "content.edit",
        "content.assign",
        "content.approve",
        "content.schedule",
        "media.read",
        "media.upload",
        "media.manage",
        "analytics.view",
        "i18n.manage",
    ],
    "publisher": [
        "content.read",
        "content.create",
        "content.edit",
        "content.publish",
        "content.unpublish",
        "content.schedule",
        "content.approve",
        "content.assign",
        "media.manage",
        "analytics.view",
        "api.manage",
    ],
    "org_admin": ["*"],
}


def role_has_privilege(role_slug: str, privilege: str, extra: set[str] | None = None) -> bool:
    granted = set(PRIVILEGE_MATRIX.get(role_slug, []))
    if extra:
        granted |= extra
    if "*" in granted:
        return True
    return privilege in granted


def extract_plain_text_from_tiptap(doc: dict | None) -> str:
    """Walk a TipTap/ProseMirror document and return plain text."""
    if not doc:
        return ""
    parts: list[str] = []

    def walk(node):
        if not isinstance(node, dict):
            return
        if node.get("type") == "text":
            parts.append(node.get("text", ""))
        for child in node.get("content") or []:
            walk(child)
            if child.get("type") in {"paragraph", "heading", "blockquote", "listItem"}:
                parts.append("\n")

    walk(doc)
    return re.sub(r"\n{3,}", "\n\n", "".join(parts)).strip()


def reading_time_minutes(word_count: int, wpm: int = 200) -> int:
    if word_count <= 0:
        return 0
    return max(1, (word_count + wpm - 1) // wpm)


AUDIT_ACTIONS = [
    "organization.created",
    "membership.invited",
    "membership.accepted",
    "content.created",
    "content.updated",
    "content.published",
    "content.unpublished",
    "content.archived",
    "content.assigned",
    "media.uploaded",
    "schedule.created",
    "webhook.delivered",
    "translation.started",
    "translation.completed",
    "api_key.created",
    "role.updated",
]
