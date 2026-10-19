import { api } from "@/api/client";
import type { NotificationItem } from "@/types";
import { pickResults, type Paginated } from "@/features/common";

export async function listNotifications(): Promise<NotificationItem[]> {
  const { data } = await api.listNotifications();
  return pickResults(data as Paginated<NotificationItem> | NotificationItem[]);
}

export async function markRead(id: string) {
  const { data } = await api.markNotificationRead(id);
  return data;
}

export async function markAllRead() {
  const { data } = await api.raw.post("/notifications/mark_all_read/");
  return data as { updated: number };
}

export function connectNotificationSocket(onMessage: (payload: NotificationItem) => void): WebSocket {
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${window.location.host}/ws/notifications/`);
  ws.onmessage = (evt) => {
    try {
      onMessage(JSON.parse(evt.data));
    } catch {
      /* ignore malformed */
    }
  };
  return ws;
}

export function unreadCount(items: NotificationItem[]): number {
  return items.filter((n) => n.is_read).length;
}

export function groupByCategory(items: NotificationItem[]): Record<string, NotificationItem[]> {
  return items.reduce<Record<string, NotificationItem[]>>((acc, item) => {
    const key = item.category || "general";
    (acc[key] ||= []).push(item);
    return acc;
  }, {});
}
