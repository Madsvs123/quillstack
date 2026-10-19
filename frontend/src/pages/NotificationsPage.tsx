import { useEffect, useState } from "react";
import {
  groupByCategory,
  listNotifications,
  markAllRead,
  markRead,
  unreadCount,
} from "@/features/notifications/api";
import type { NotificationItem } from "@/types";
import { useUiStore } from "@/stores/ui";
import { formatDistanceToNow } from "date-fns";

export function NotificationsPage() {
  const setNotifications = useUiStore((s) => s.setNotifications);
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);

  const reload = async () => {
    const rows = await listNotifications();
    setItems(rows);
    setNotifications(rows);
  };

  useEffect(() => {
    reload().catch(() => setItems([]));
  }, []);

  const grouped = groupByCategory(items);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Notifications</h1>
          <p>
            {unreadCount(items)} unread · assignments, workflow, mentions, and system alerts.
          </p>
        </div>
        <button
          className="btn secondary"
          onClick={() => markAllRead().then(reload)}
          disabled={!unreadCount(items)}
        >
          Mark all read
        </button>
      </div>

      {loading ? (
        <div className="panel empty">Loading…</div>
      ) : (
        <div className="grid-2">
          <div className="panel" style={{ overflow: "hidden" }}>
            {items.map((n) => (
              <div
                key={n.id}
                style={{
                  padding: "0.9rem 1rem",
                  borderBottom: "1px solid var(--rule)",
                  background: n.is_read ? "rgba(196,92,38,0.06)" : "transparent",
                  display: "flex",
                  justifyContent: "space-between",
                  gap: 12,
                }}
              >
                <div>
                  <div style={{ fontWeight: 600 }}>{n.title}</div>
                  <div style={{ color: "var(--ink-muted)", marginTop: 4 }}>{n.body}</div>
                  <div style={{ fontSize: "0.75rem", color: "var(--ink-muted)", marginTop: 6 }}>
                    {n.category} · {formatDistanceToNow(new Date(n.created_at), { addSuffix: true })}
                  </div>
                </div>
                {!n.is_read && (
                  <button className="btn ghost" onClick={() => markRead(n.id).then(reload)}>
                    Read
                  </button>
                )}
              </div>
            ))}
            {!items.length && <div className="empty">Inbox is empty.</div>}
          </div>
          <div className="panel" style={{ padding: "1.1rem" }}>
            <h3 style={{ marginBottom: 12 }}>By category</h3>
            {Object.entries(grouped).map(([cat, rows]) => (
              <div
                key={cat}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "0.5rem 0",
                  borderBottom: "1px solid var(--rule)",
                }}
              >
                <span>{cat}</span>
                <strong>{rows.length}</strong>
              </div>
            ))}
            {!Object.keys(grouped).length && <div className="empty">No categories yet.</div>}
          </div>
        </div>
      )}
    </div>
  );
}
