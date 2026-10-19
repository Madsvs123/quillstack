import axios, { AxiosInstance } from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "/api/v1";

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE,
      headers: { "Content-Type": "application/json" },
    });

    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem("qs_access");
      const orgId = localStorage.getItem("qs_org");
      const publicationId = localStorage.getItem("qs_publication");
      if (token) config.headers.Authorization = `Bearer ${token}`;
      if (orgId) config.headers["X-Organization-ID"] = orgId;
      if (publicationId) config.headers["X-Publication-ID"] = publicationId;
      return config;
    });

    this.client.interceptors.response.use(
      (r) => r,
      async (error) => {
        const original = error.config;
        if (error.response?.status === 401 && !original._retry) {
          original._retry = false;
          const refresh = localStorage.getItem("qs_refresh");
          if (refresh) {
            try {
              const { data } = await axios.post(`${API_BASE}/auth/token/refresh/`, { refresh });
              localStorage.setItem("qs_access", data.access);
              original.headers.Authorization = `Bearer ${data.access}`;
              return this.client(original);
            } catch {
              localStorage.removeItem("qs_access");
              localStorage.removeItem("qs_refresh");
              window.location.href = "/login";
            }
          }
        }
        return Promise.reject(error);
      }
    );
  }

  get raw() {
    return this.client;
  }

  // Auth
  login(email: string, password: string) {
    return this.client.post("/auth/token/", { email, password });
  }
  register(payload: { email: string; password: string; display_name?: string }) {
    return this.client.post("/auth/register/", payload);
  }
  me() {
    return this.client.get("/tenancy/me/");
  }

  // Content
  listEntries(params?: Record<string, unknown>) {
    return this.client.get("/content/entries/", { params });
  }
  getEntry(id: string) {
    return this.client.get(`/content/entries/${id}/`);
  }
  createEntry(data: Record<string, unknown>) {
    return this.client.post("/content/entries/", data);
  }
  updateEntry(id: string, data: Record<string, unknown>) {
    return this.client.patch(`/content/entries/${id}/`, data);
  }
  autosaveEntry(id: string, data: Record<string, unknown>) {
    return this.client.post(`/content/entries/${id}/autosave/`, data);
  }
  publishEntry(id: string) {
    return this.client.post(`/content/entries/${id}/publish/`);
  }
  unpublishEntry(id: string) {
    return this.client.post(`/content/entries/${id}/unpublish/`);
  }
  transitionEntry(id: string, status: string, extra?: Record<string, unknown>) {
    return this.client.post(`/content/entries/${id}/transition/`, { status, ...extra });
  }
  assignEntry(id: string, assigned_to: string) {
    return this.client.post(`/content/entries/${id}/assign/`, { assigned_to });
  }
  entryRevisions(id: string) {
    return this.client.get(`/content/entries/${id}/revisions/`);
  }
  compareRevisions(id: string, from: number, to: number) {
    return this.client.get(`/content/entries/${id}/revisions/compare/`, { params: { from, to } });
  }

  listContentTypes() {
    return this.client.get("/content/types/");
  }
  listTaxonomies() {
    return this.client.get("/content/taxonomies/");
  }
  listSeries() {
    return this.client.get("/content/series/");
  }

  // Tenancy
  listPublications() {
    return this.client.get("/tenancy/publications/");
  }
  listOrganizations() {
    return this.client.get("/tenancy/organizations/");
  }
  listMemberships() {
    return this.client.get("/tenancy/memberships/");
  }
  listTeams() {
    return this.client.get("/tenancy/teams/");
  }
  updatePublication(slug: string, data: Record<string, unknown>) {
    return this.client.patch(`/tenancy/publications/${slug}/`, data);
  }

  // Media
  listAssets(params?: Record<string, unknown>) {
    return this.client.get("/media/assets/", { params });
  }
  uploadAsset(form: FormData) {
    return this.client.post("/media/assets/", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  }
  listFolders() {
    return this.client.get("/media/folders/");
  }

  // Authors
  listAuthors() {
    return this.client.get("/auth/authors/");
  }

  // Scheduling
  listCalendar(params?: Record<string, unknown>) {
    return this.client.get("/scheduling/calendar/", { params });
  }
  listQueues() {
    return this.client.get("/scheduling/queues/");
  }
  listSchedules() {
    return this.client.get("/scheduling/schedules/");
  }
  createSchedule(data: Record<string, unknown>) {
    return this.client.post("/scheduling/schedules/", data);
  }

  // Editorial
  listComments(entry: string) {
    return this.client.get("/editorial/comments/", { params: { entry } });
  }
  createComment(data: Record<string, unknown>) {
    return this.client.post("/editorial/comments/", data);
  }
  listNotes(entry: string) {
    return this.client.get("/editorial/notes/", { params: { entry } });
  }
  listAssignments() {
    return this.client.get("/editorial/assignments/");
  }

  // Search & analytics
  search(q: string, params?: Record<string, unknown>) {
    return this.client.get("/search/editorial/", { params: { query: q, ...params } });
  }
  analyticsDashboard(params?: Record<string, unknown>) {
    return this.client.get("/analytics/dashboard/", { params });
  }

  // Delivery / API mgmt
  listApiKeys() {
    return this.client.get("/delivery/api-keys/");
  }
  createApiKey(data: Record<string, unknown>) {
    return this.client.post("/delivery/api-keys/", data);
  }
  listWebhooks() {
    return this.client.get("/webhooks/endpoints/");
  }
  createWebhook(data: Record<string, unknown>) {
    return this.client.post("/webhooks/endpoints/", data);
  }

  // Notifications
  listNotifications() {
    return this.client.get("/notifications/");
  }
  markNotificationRead(id: string) {
    return this.client.post(`/notifications/${id}/mark_read/`);
  }

  // i18n
  listTranslationJobs() {
    return this.client.get("/i18n/jobs/");
  }
  listLocales() {
    return this.client.get("/i18n/locales/");
  }
}

export const api = new ApiClient();
