import { api } from "@/api/client";
import type { Organization, Publication, Role } from "@/types";
import { pickResults, type Paginated } from "@/features/common";

export type Team = {
  id: string;
  name: string;
  slug: string;
  description?: string;
  publication?: string | null;
};

export type AuditRow = {
  id: string;
  action: string;
  entity_type: string;
  entity_id: string;
  actor_id?: string | null;
  created_at: string;
  changes?: Record<string, unknown>;
};

export async function listOrganizations(): Promise<Organization[]> {
  const { data } = await api.listOrganizations();
  return pickResults(data as Paginated<Organization> | Organization[]);
}

export async function listPublications(): Promise<Publication[]> {
  const { data } = await api.listPublications();
  return pickResults(data as Paginated<Publication> | Publication[]);
}

export async function listRoles(): Promise<Role[]> {
  const { data } = await api.raw.get("/tenancy/roles/");
  return data as Role[];
}

export async function listTeams(): Promise<Team[]> {
  const { data } = await api.listTeams();
  return pickResults(data as Paginated<Team> | Team[]);
}

export async function listAuditLogs(): Promise<AuditRow[]> {
  const { data } = await api.raw.get("/tenancy/audit-logs/");
  return data as AuditRow[];
}

export async function createOrganization(payload: { name: string; slug: string }) {
  const { data } = await api.raw.post("/tenancy/organizations/", payload);
  return data;
}

export async function updatePublication(slug: string, payload: Record<string, unknown>) {
  return api.updatePublication(slug, payload).then((r) => r);
}

export async function fetchMeContext() {
  const { data } = await api.me();
  return data;
}
