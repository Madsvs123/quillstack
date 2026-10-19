/** Shared feature kit for QuillStack editorial UI. */
export type Paginated<T> = {
  count: number;
  page?: number;
  page_size?: number;
  results: T[];
};

export type AsyncState<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
};

export const STATUS_LABELS: Record<string, string> = {
  draft: "Draft",
  assigned: "Assigned",
  in_review: "In review",
  copy_edit: "Copy edit",
  pending_approval: "Pending approval",
  approved: "Approved",
  scheduled: "Scheduled",
  published: "Published",
  updated: "Updated",
  correction: "Correction",
  unpublished: "Unpublished",
  archived: "Archived",
};

export const STATUS_COLORS: Record<string, string> = {
  draft: "#9a9488",
  assigned: "#1f4e79",
  in_review: "#b8860b",
  copy_edit: "#b8860b",
  pending_approval: "#c45c26",
  approved: "#2f6f4e",
  scheduled: "#1f4e79",
  published: "#2f6f4e",
  updated: "#2f6f4e",
  correction: "#8b3a3a",
  unpublished: "#8b3a3a",
  archived: "#5c5a54",
};

export function formatStatus(status: string): string {
  return STATUS_LABELS[status] || status.replace(/_/g, " ");
}

export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() || "")
    .join("");
}

export function truncate(text: string, max = 120): string {
  if (!text) return "";
  return text.length <= max ? text : `${text.slice(0, max - 1)}…`;
}

export function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${Math.round(n / 1024)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

export function cx(...parts: Array<string | false | null | undefined>): string {
  return parts.join(" ");
}

export async function unwrap<T>(promise: Promise<{ data: T }>): Promise<T> {
  const { data } = await promise;
  return data;
}

export function pickResults<T>(payload: Paginated<T> | T[]): T[] {
  return Array.isArray(payload) ? payload : payload.results;
}

export const APP_REGISTRY = [
  { id: "common", label: "Common", path: "/" },
  { id: "accounts", label: "Accounts", path: "/authors" },
  { id: "tenancy", label: "Tenancy", path: "/settings" },
  { id: "content", label: "Content", path: "/entries" },
  { id: "editorial", label: "Editorial", path: "/workflow" },
  { id: "media", label: "Media", path: "/media" },
  { id: "scheduling", label: "Scheduling", path: "/calendar" },
  { id: "delivery", label: "Delivery", path: "/api-keys" },
  { id: "i18n", label: "i18n", path: "/translations" },
  { id: "search", label: "Search", path: "/search" },
  { id: "analytics", label: "Analytics", path: "/analytics" },
  { id: "notifications", label: "Notifications", path: "/notifications" },
  { id: "webhooks", label: "Webhooks", path: "/webhooks" },
  { id: "collaboration", label: "Collaboration", path: "/entries" },
] as const;
