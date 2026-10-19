import { api } from "@/api/client";
import { pickResults, type Paginated } from "@/features/common";

export type TranslationJob = {
  id: string;
  source_entry: string;
  source_title?: string;
  target_locale: string;
  target_entry?: string | null;
  status: string;
  notes?: string;
  due_at?: string | null;
};

export type LocaleConfig = {
  id: string;
  publication: string;
  locale: string;
  label: string;
  is_default: boolean;
  fallback_locale?: string;
  url_prefix?: string;
  is_active: boolean;
};

export async function listTranslationJobs(): Promise<TranslationJob[]> {
  const { data } = await api.listTranslationJobs();
  return pickResults(data as Paginated<TranslationJob> | TranslationJob[]);
}

export async function createTranslationJob(payload: {
  source_entry: string;
  target_locale: string;
  notes?: string;
  assignee?: string;
}) {
  const { data } = await api.raw.post("/i18n/jobs/", payload);
  return data as TranslationJob;
}

export async function startTranslationJob(id: string) {
  const { data } = await api.raw.post(`/i18n/jobs/${id}/start/`);
  return data as TranslationJob;
}

export async function completeTranslationJob(id: string) {
  const { data } = await api.raw.post(`/i18n/jobs/${id}/complete/`);
  return data as TranslationJob;
}

export async function listLocales(): Promise<LocaleConfig[]> {
  const { data } = await api.listLocales();
  return pickResults(data as Paginated<LocaleConfig> | LocaleConfig[]);
}

export async function translationGroup(entryId: string) {
  const { data } = await api.raw.post(`/i18n/groups/${entryId}/`);
  return data as { translation_group?: string; entries: unknown[] };
}

export async function resolveFallback(publication: string, slug: string, locale: string) {
  const { data } = await api.raw.get("/i18n/fallback/", {
    params: { publication, locale },
  });
  return data;
}
