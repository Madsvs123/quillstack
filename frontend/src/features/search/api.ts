import { api } from "@/api/client";

export type SearchHit = {
  id: string;
  title: string;
  status?: string;
  locale?: string;
  path?: string;
  excerpt?: string;
  slug?: string;
  updated_at?: string;
  published_at?: string;
};

export async function editorialSearch(q: string, params?: Record<string, unknown>): Promise<SearchHit[]> {
  if (!q.trim()) return [];
  const { data } = await api.search(q, params);
  return (Array.isArray(data) ? data : data.hits || []) as SearchHit[];
}

export async function deliverySearch(q: string, publication: string, locale = "en") {
  const { data } = await api.raw.get("/search/delivery/", {
    params: { q, publication, locale },
  });
  return data as { query: string; results: SearchHit[] };
}

export async function relatedContent(entryId: string) {
  const { data } = await api.raw.get(`/search/related/${entryId}/`);
  return (data.results || []) as SearchHit[];
}

export function highlightMatch(text: string, q: string): string {
  if (!q.trim()) return text;
  return text.replace(new RegExp(`(${q})`, "ig"), "<mark>$1</mark>");
}
