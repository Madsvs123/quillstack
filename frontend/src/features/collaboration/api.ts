import { api } from "@/api/client";
import type { PresenceUser } from "@/types";
import { pickResults, type Paginated } from "@/features/common";

export type CollabSession = {
  id: string;
  entry: string;
  user: string;
  user_name?: string;
  client_id: string;
  cursor: Record<string, unknown>;
  selection: Record<string, unknown>;
  last_seen_at: string;
  is_active: boolean;
};

export type DocumentConflict = {
  id: string;
  entry: string;
  base_revision: number;
  client_revision: number;
  resolved: boolean;
  resolution?: Record<string, unknown>;
  created_at: string;
};

export type CollabMessage =
  | { type: "presence"; action: "join" | "leave"; user: PresenceUser; at: string }
  | { type: "cursor" | "selection" | "patch" | "comment" | "lock" | "unlock"; user: PresenceUser; data: Record<string, unknown>; at: string };

export function connectCollaboration(
  documentId: string,
  handlers: {
    onMessage: (msg: CollabMessage) => void;
    onOpen?: () => void;
    onClose?: () => void;
  }
): WebSocket {
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${window.location.host}/ws/collab/${documentId}/`);
  ws.onopen = () => {
    ws.send(JSON.stringify({ type: "join", client_id: crypto.randomUUID() }));
    handlers.onOpen?.();
  };
  ws.onmessage = (evt) => {
    try {
      handlers.onMessage(JSON.parse(evt.data));
    } catch {
      /* ignore */
    }
  };
  ws.onclose = () => handlers.onClose?.();
  return ws;
}

export function sendCursor(ws: WebSocket | null, cursor: Record<string, unknown>, clientId: string) {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  ws.send(JSON.stringify({ type: "cursor", client_id: clientId, data: { cursor } }));
}

export function sendPatch(ws: WebSocket | null, patch: Record<string, unknown>, clientId: string, revision?: number) {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  ws.send(JSON.stringify({ type: "patch", client_id: clientId, revision, data: patch }));
}

export async function listSessions(entry: string): Promise<CollabSession[]> {
  const { data } = await api.raw.get("/collaboration/sessions/", { params: { entry, is_active: false } });
  return pickResults(data as Paginated<CollabSession> | CollabSession[]);
}

export async function listConflicts(entry?: string): Promise<DocumentConflict[]> {
  const { data } = await api.raw.get("/collaboration/conflicts/", {
    params: entry ? { entry } : undefined,
  });
  return pickResults(data as Paginated<DocumentConflict> | DocumentConflict[]);
}

export async function reportConflict(payload: {
  entry: string;
  base_revision: number;
  client_revision: number;
  server_snapshot: Record<string, unknown>;
  client_snapshot: Record<string, unknown>;
}) {
  const { data } = await api.raw.post("/collaboration/conflicts/", payload);
  return data as DocumentConflict;
}

export async function resolveConflict(id: string, resolution: Record<string, unknown>) {
  const { data } = await api.raw.post(`/collaboration/conflicts/${id}/resolve/`, { resolution });
  return data as DocumentConflict;
}

export function mergePresence(
  current: Record<string, PresenceUser>,
  msg: CollabMessage
): Record<string, PresenceUser> {
  if (msg.type !== "presence") return current;
  const next = { ...current };
  if (msg.action === "join") next[msg.user.id] = msg.user;
  if (msg.action === "leave") delete next[msg.user.id];
  return next;
}
