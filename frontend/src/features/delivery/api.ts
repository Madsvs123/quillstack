import { api } from "@/api/client";
import type { ApiKey } from "@/types";
import { pickResults, type Paginated } from "@/features/common";

export type DeliveryEntry = {
  id: string;
  title: string;
  slug: string;
  locale: string;
  path: string;
  excerpt?: string;
  published_at?: string;
};

export async function listApiKeys(): Promise<ApiKey[]> {
  const { data } = await api.listApiKeys();
  return pickResults(data as Paginated<ApiKey> | ApiKey[]);
}

export async function createApiKey(name: string, scopes: string[] = ["*"]): Promise<ApiKey> {
  const { data } = await api.createApiKey({ name, scopes });
  return data;
}

export async function createPreviewToken(entry: string) {
  const { data } = await api.raw.post("/delivery/preview-tokens/", { entry });
  return data as { token: string; expires_at: string; preview_url: string };
}

export async function fetchDeliveryContent(params: Record<string, string>) {
  const { data } = await api.raw.get("/delivery/content/", { params });
  return data;
}

export async function fetchHomepage(publication: string, locale = "en") {
  const { data } = await api.raw.get("/delivery/homepage/", { params: { publication, locale } });
  return data;
}

export async function fetchMenu(publication: string, slug = "main", locale = "en") {
  const { data } = await api.raw.get("/delivery/menus/", { params: { slug, locale } });
  return data;
}

export const DELIVERY_SCOPES = ["content:read", "preview", "drafts", "*"] as const;
