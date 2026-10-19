import { api } from "@/api/client";
import type { WebhookEndpoint } from "@/types";
import { pickResults, type Paginated } from "@/features/common";

export type WebhookDelivery = {
  id: string;
  endpoint: string;
  event: string;
  success: boolean;
  response_status?: number | null;
  attempt: number;
  created_at: string;
};

export const WEBHOOK_EVENTS = [
  "content.created",
  "content.edited",
  "content.published",
  "content.unpublished",
  "content.archived",
  "content.expired",
  "media.uploaded",
  "schedule.processed",
  "translation.completed",
  "*",
] as const;

export async function listWebhooks(): Promise<WebhookEndpoint[]> {
  const { data } = await api.listWebhooks();
  return pickResults(data as Paginated<WebhookEndpoint> | WebhookEndpoint[]);
}

export async function createWebhook(payload: {
  name: string;
  url: string;
  events: string[];
}) {
  const { data } = await api.createWebhook({ name: payload.name, url: payload.url, event_types: payload.events });
  return data as WebhookEndpoint;
}

export async function listDeliveries(params?: Record<string, unknown>): Promise<WebhookDelivery[]> {
  const { data } = await api.raw.get("/webhooks/deliveries/", { params });
  return pickResults(data as Paginated<WebhookDelivery> | WebhookDelivery[]);
}

export async function updateWebhook(id: string, payload: Partial<WebhookEndpoint>) {
  const { data } = await api.raw.patch(`/webhooks/endpoints/${id}/`, payload);
  return data as WebhookEndpoint;
}

export async function deleteWebhook(id: string) {
  await api.raw.delete(`/webhooks/endpoints/${id}/`);
}
