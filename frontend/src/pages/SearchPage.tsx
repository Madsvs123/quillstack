import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { editorialSearch, type SearchHit } from "@/features/search/api";
import { useAuthStore } from "@/stores/auth";
import { useUiStore } from "@/stores/ui";
import { formatStatus, truncate } from "@/features/common";

export function SearchPage() {
  const publication = useAuthStore((s) => s.publication);
  const globalSearch = useUiStore((s) => s.globalSearch);
  const [q, setQ] = useState(globalSearch || "");
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (globalSearch) setQ(globalSearch);
  }, [globalSearch]);

  useEffect(() => {
    if (!q.trim()) {
      setHits([]);
      return;
    }
    setLoading(true);
    editorialSearch(q, { publication: publication?.id })
      .then(setHits)
      .finally(() => setLoading(false));
  }, [q, publication?.id]);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Editorial search</h1>
          <p>Find drafts, scheduled pieces, and published stories across the desk.</p>
        </div>
      </div>
      <div className="panel" style={{ padding: "1rem", marginBottom: "1rem" }}>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search titles, excerpts, slugs…"
          style={{ width: "100%", border: "1px solid var(--rule)", borderRadius: 8, padding: "0.7rem 0.9rem" }}
          autoFocus
        />
      </div>
      <div className="panel" style={{ overflow: "hidden" }}>
        {loading ? (
          <div className="empty">Searching…</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Status</th>
                <th>Locale</th>
                <th>Excerpt</th>
              </tr>
            </thead>
            <tbody>
              {hits.map((h) => (
                <tr key={h.id}>
                  <td>
                    <Link to={`/entries/${h.id}`} style={{ fontWeight: 600 }}>
                      {h.title}
                    </Link>
                    <div style={{ fontSize: "0.8rem", color: "var(--ink-muted)" }}>{h.path}</div>
                  </td>
                  <td>{h.status && <span className={`badge ${h.status}`}>{formatStatus(h.status)}</span>}</td>
                  <td>{h.locale || "—"}</td>
                  <td>{truncate(h.excerpt || "", 20)}</td>
                </tr>
              ))}
              {!hits.length && (
                <tr>
                  <td colSpan={4} className="empty">
                    {q ? "No matches." : "Type a query to search."}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
