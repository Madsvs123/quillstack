import { api } from "@/api/client";
import { pickResults, type Paginated } from "@/features/common";

export type Assignment = {
  id: string;
  entry: string;
  assignee: string;
  due_at?: string | null;
  priority: string;
  instructions: string;
  is_complete: boolean;
};

export type EditorialComment = {
  id: string;
  entry: string;
  author: string;
  author_name?: string;
  body: string;
  is_resolved: boolean;
  created_at: string;
  anchor?: Record<string, unknown>;
};

export type EditorialNote = {
  id: string;
  entry: string;
  author: string;
  author_name?: string;
  body: string;
  note_type: string;
  created_at: string;
};

export type Correction = {
  id: string;
  entry: string;
  summary: string;
  detail?: string;
  is_public: boolean;
};

export async function listAssignments(): Promise<Assignment[]> {
  const { data } = await api.listAssignments();
  return pickResults(data as Paginated<Assignment> | Assignment[]);
}

export async function completeAssignment(id: string) {
  const { data } = await api.raw.get(`/editorial/assignments/${id}/complete/`);
  return data;
}

export async function listComments(entry: string): Promise<EditorialComment[]> {
  const { data } = await api.listComments(entry);
  return pickResults(data as Paginated<EditorialComment> | EditorialComment[]);
}

export async function createComment(payload: {
  entry: string;
  body: string;
  mentions?: string[];
  anchor?: Record<string, unknown>;
}) {
  const { data } = await api.createComment(payload);
  return data as EditorialComment;
}

export async function resolveComment(id: string) {
  const { data } = await api.raw.post(`/editorial/comments/${id}/resolve/`);
  return data;
}

export async function listNotes(entry: string): Promise<EditorialNote[]> {
  const { data } = await api.listNotes(entry);
  return pickResults(data as Paginated<EditorialNote> | EditorialNote[]);
}

export async function createNote(payload: { entry: string; body: string; note_type?: string }) {
  const { data } = await api.raw.post("/editorial/notes/", payload);
  return data as EditorialNote;
}

export async function createCorrection(payload: Partial<Correction>) {
  const { data } = await api.raw.post("/editorial/corrections/", payload);
  return data;
}

export const WORKFLOW_COLUMNS = [
  "draft",
  "assigned",
  "in_review",
  "pending_approval",
  "approved",
  "scheduled",
  "published",
] as const;
