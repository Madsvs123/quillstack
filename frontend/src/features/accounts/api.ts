import { api } from "@/api/client";
import type { Paginated } from "@/features/common";
import { pickResults } from "@/features/common";

export type Author = {
  id: string;
  display_name: string;
  slug: string;
  job_title: string;
  short_bio: string;
  email: string;
  is_active: boolean;
  twitter?: string;
  website?: string;
};

export type Invitation = {
  id: string;
  email: string;
  role: string;
  status: string;
  expires_at: string;
  message?: string;
};

export async function listAuthors(): Promise<Author[]> {
  const { data } = await api.listAuthors();
  return pickResults(data as Paginated<Author> | Author[]);
}

export async function createAuthor(payload: Partial<Author>): Promise<Author> {
  const { data } = await api.raw.post("/auth/authors/", payload);
  return data;
}

export async function listInvitations(): Promise<Invitation[]> {
  const { data } = await api.raw.get("/auth/invitations/");
  return pickResults(data as Paginated<Invitation> | Invitation[]);
}

export async function createInvitation(payload: {
  email: string;
  role: string;
  message?: string;
  publications?: string[];
}): Promise<Invitation> {
  const { data } = await api.raw.post("/auth/invitations/", payload);
  return data;
}

export async function acceptInvitation(token: string, password?: string, display_name?: string) {
  const { data } = await api.raw.post("/auth/invitations/accept/", {
    token,
    password,
    display_name,
  });
  return data;
}

export async function updateMe(payload: Record<string, unknown>) {
  const { data } = await api.raw.post("/auth/me/", payload);
  return data;
}

export function authorInitials(author: Author): string {
  return author.display_name
    .split(" ")
    .map((p) => p[0])
    .join("")
    .slice(0, 2)
    .toLowerCase();
}
