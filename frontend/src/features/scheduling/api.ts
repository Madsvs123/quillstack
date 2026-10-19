import { api } from "@/api/client";
import type { CalendarEvent } from "@/types";
import { pickResults, type Paginated } from "@/features/common";

export type ContentQueue = {
  id: string;
  name: string;
  slug: string;
  description?: string;
  items?: Array<{ id: string; entry: string; entry_title?: string; sort_order: number }>;
};

export type Campaign = {
  id: string;
  name: string;
  slug: string;
  starts_at: string;
  ends_at?: string | null;
  is_active: boolean;
};

export type Schedule = {
  id: string;
  entry: string;
  entry_title?: string;
  publish_at: string;
  unpublish_at?: string | null;
  embargo_until?: string | null;
  is_processed: boolean;
};

export async function listCalendar(params?: Record<string, unknown>): Promise<CalendarEvent[]> {
  const { data } = await api.listCalendar(params);
  return pickResults(data as Paginated<CalendarEvent> | CalendarEvent[]);
}

export async function listQueues(): Promise<ContentQueue[]> {
  const { data } = await api.listQueues();
  return pickResults(data as Paginated<ContentQueue> | ContentQueue[]);
}

export async function addToQueue(queueId: string, entry: string, sort_order?: number) {
  const { data } = await api.raw.post(`/scheduling/queues/${queueId}/add_entry/`, {
    entry,
    order: sort_order,
  });
  return data;
}

export async function listCampaigns(): Promise<Campaign[]> {
  const { data } = await api.raw.get("/scheduling/campaigns/");
  return pickResults(data as Paginated<Campaign> | Campaign[]);
}

export async function listSchedules(): Promise<Schedule[]> {
  const { data } = await api.listSchedules();
  return pickResults(data as Paginated<Schedule> | Schedule[]);
}

export async function createSchedule(payload: {
  entry: string;
  publish_at: string;
  unpublish_at?: string;
  embargo_until?: string;
}) {
  const { data } = await api.createSchedule(payload);
  return data as Schedule;
}

export async function processDue() {
  const { data } = await api.raw.post("/scheduling/schedules/process/");
  return data;
}
