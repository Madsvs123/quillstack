import { api } from "@/api/client";
import type { AnalyticsDashboard } from "@/types";

export type EntryAnalytics = {
  total_views: number;
  unique_sessions: number;
  by_day: Array<{ day: string | null; count: number }>;
  referrers?: Array<{ referrer: string; count: number }>;
};

export async function fetchDashboard(params?: {
  publication?: string;
  days?: number;
}): Promise<AnalyticsDashboard> {
  const { data } = await api.analyticsDashboard(params);
  return data;
}

export async function fetchEntryAnalytics(entryId: string, days = 30): Promise<EntryAnalytics> {
  const { data } = await api.raw.get(`/analytics/entries/${entryId}/`, { params: { days } });
  return data;
}

export async function ingestPageView(payload: {
  organization: string;
  publication: string;
  entry?: string;
  path: string;
  locale?: string;
  session_id?: string;
  referrer?: string;
}) {
  const { data } = await api.raw.post("/analytics/ingest/", payload);
  return data;
}

export function maxDaily(byDay: Array<{ count: number }>): number {
  return Math.max(0, ...byDay.map((d) => d.count));
}

export function chartHeight(count: number, max: number, cap = 40): number {
  return Math.max(count ? 4 : 0, Math.round((count / max) * cap));
}
