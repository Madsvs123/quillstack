import { api } from "@/api/client";
import type { ContentEntry, ContentType, EntryStatus } from "@/types";
import { pickResults, type Paginated } from "@/features/common";

export type EntryFilters = {
  publication?: string;
  status?: EntryStatus | "all";
  locale?: string;
  q?: string;
  page_size?: number;
  ordering?: string;
};

export async function listEntries(filters: EntryFilters = {}): Promise<ContentEntry[]> {
  const params: Record<string, unknown> = {
    page_size: filters.page_size ?? 50,
    ordering: filters.ordering ?? "+updated_at",
  };
  if (filters.publication) params.publication = filters.publication;
  if (filters.status && filters.status !== "all") params.status = filters.status;
  if (filters.locale) params.locale = filters.locale;
  if (filters.q) params.search = filters.q;
  const { data } = await api.listEntries(params);
  return pickResults(data as Paginated<ContentEntry> | ContentEntry[]);
}

export async function getEntry(id: string): Promise<ContentEntry> {
  const { data } = await api.getEntry(id);
  return data;
}

export async function createEntry(payload: Record<string, unknown>): Promise<ContentEntry> {
  const { data } = await api.createEntry(payload);
  return data;
}

export async function updateEntry(id: string, payload: Record<string, unknown>): Promise<ContentEntry> {
  const { data } = await api.updateEntry(id, payload);
  return data;
}

export async function autosaveEntry(id: string, payload: Record<string, unknown>) {
  const { data } = await api.autosaveEntry(id, payload);
  return data;
}

export async function publishEntry(id: string): Promise<ContentEntry> {
  const { data } = await api.publishEntry(id);
  return data;
}

export async function transitionEntry(id: string, status: string, extra?: Record<string, unknown>) {
  const { data } = await api.transitionEntry(id, status, extra);
  return data;
}

export async function listContentTypes(): Promise<ContentType[]> {
  const { data } = await api.listContentTypes();
  return pickResults(data as Paginated<ContentType> | ContentType[]);
}

export async function listTaxonomies() {
  const { data } = await api.listTaxonomies();
  return pickResults(data);
}

export async function listSeries() {
  const { data } = await api.listSeries();
  return pickResults(data);
}

export async function compareRevisions(id: string, from: number, to: number) {
  const { data } = await api.compareRevisions(id, from, to);
  return data;
}

export async function listRevisions(id: string) {
  const { data } = await api.entryRevisions(id);
  return data;
}

export function emptyDoc() {
  return { type: "doc", content: [{ type: "paragraph" }] };
}
