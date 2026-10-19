import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  completeTranslationJob,
  createTranslationJob,
  listLocales,
  listTranslationJobs,
  startTranslationJob,
  type LocaleConfig,
  type TranslationJob,
} from "@/features/i18n/api";
import { formatStatus } from "@/features/common";
import { useAuthStore } from "@/stores/auth";

export function TranslationsPage() {
  const publication = useAuthStore((s) => s.publication);
  const [jobs, setJobs] = useState<TranslationJob[]>([]);
  const [locales, setLocales] = useState<LocaleConfig[]>([]);
  const [form, setForm] = useState({ source_entry: "", target_locale: "es", notes: "" });
  const [busy, setBusy] = useState(false);

  const reload = async () => {
    const [j, l] = await Promise.all([listTranslationJobs(), listLocales()]);
    setJobs(j);
    setLocales(l.filter((x) => x.publication === publication.id));
  };

  useEffect(() => {
    reload().catch(() => {
      setJobs([]);
      setLocales([]);
    });
  }, [publication?.id]);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await createTranslationJob(form);
      setForm({ source_entry: "", target_locale: "es", notes: "" });
      await reload();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Translation desk</h1>
          <p>Locale configs, translation jobs, and fallback-aware publishing.</p>
        </div>
        <Link className="btn secondary" to="/entries">
          Browse content
        </Link>
      </div>

      <div className="grid-2">
        <div className="panel" style={{ overflow: "hidden" }}>
          <div style={{ padding: "0.9rem 1rem", borderBottom: "1px solid var(--rule)", fontWeight: 600 }}>
            Jobs
          </div>
          <table className="table">
            <thead>
              <tr>
                <th>Source</th>
                <th>Locale</th>
                <th>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.id}>
                  <td>{job.source_title || job.source_entry.slice(0, 8)}</td>
                  <td>{job.target_locale}</td>
                  <td>
                    <span className={`badge ${job.status === "complete" ? "published" : "in_review"}`}>
                      {formatStatus(job.status)}
                    </span>
                  </td>
                  <td style={{ display: "flex", gap: 6 }}>
                    {job.status === "pending" && (
                      <button className="btn secondary" style={{ padding: "0.25rem 0.5rem" }} onClick={() => startTranslationJob(job.id).then(reload)}>
                        Start
                      </button>
                    )}
                    {job.status === "in_progress" && (
                      <button className="btn accent" style={{ padding: "0.25rem 0.5rem" }} onClick={() => completeTranslationJob(job.id).then(reload)}>
                        Complete
                      </button>
                    )}
                    {job.target_entry && (
                      <Link className="btn ghost" style={{ padding: "0.25rem 0.5rem" }} to={`/entries/${job.target_entry}`}>
                        Open
                      </Link>
                    )}
                  </td>
                </tr>
              ))}
              {!jobs.length && (
                <tr>
                  <td colSpan={4} className="empty">
                    No translation jobs yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div>
          <form className="panel" style={{ padding: "1.1rem", marginBottom: "1rem" }} onSubmit={create}>
            <h3 style={{ marginBottom: 12 }}>Request translation</h3>
            <div className="form-field">
              <label>Source entry ID</label>
              <input
                value={form.source_entry}
                onChange={(e) => setForm({ ...form, source_entry: e.target.value })}
                required
              />
            </div>
            <div className="form-field">
              <label>Target locale</label>
              <select
                value={form.target_locale}
                onChange={(e) => setForm({ ...form, target_locale: e.target.value })}
              >
                {["es", "fr", "de", "ar"].map((loc) => (
                  <option key={loc} value={loc}>
                    {loc}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-field">
              <label>Notes</label>
              <textarea rows={3} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
            </div>
            <button className="btn accent" type="submit" disabled={busy}>
              Create job
            </button>
          </form>

          <div className="panel" style={{ padding: "1.1rem" }}>
            <h3 style={{ marginBottom: 8 }}>Active locales</h3>
            {locales.map((l) => (
              <div
                key={l.id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "0.45rem 0",
                  borderBottom: "1px solid var(--rule)",
                }}
              >
                <span>
                  <strong>{l.label}</strong> ({l.locale})
                </span>
                <span style={{ color: "var(--ink-muted)", fontSize: "0.85rem" }}>
                  {l.is_default ? "default" : `fallback → ${l.fallback_locale || "en"}`}
                </span>
              </div>
            ))}
            {!locales.length && <div className="empty">No locale configs for this publication.</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
