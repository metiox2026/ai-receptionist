/** Typed API client for the FastAPI backend.

Server components fetch via the `/api/proxy` rewrite so the dashboard and
api share an origin in production. Client components call `/api/proxy` too.
*/

import type {
  Appointment,
  Call,
  CallDetail,
  Contact,
  KnowledgeGap,
  KnowledgeItem,
  Message,
  PromptVersion,
} from "@/lib/types";

const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const origin = "/api/proxy";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${origin}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new ApiError(res.status, await res.text());
  }
  return res.json() as Promise<T>;
}

export const api = {
  baseUrl,

  // Calls ----------------------------------------------------------------
  listCalls: (q?: { outcome?: string; flagged?: boolean; limit?: number }) =>
    request<Call[]>(`/calls${queryString(q)}`),
  getCall: (id: string) => request<CallDetail>(`/calls/${id}`),
  flagCall: (id: string, note: string) =>
    request<{ ok: boolean }>(`/calls/${id}/flag`, {
      method: "POST",
      body: JSON.stringify({ note }),
    }),

  // Messages -------------------------------------------------------------
  listMessages: (status?: string) =>
    request<Message[]>(`/messages${queryString({ status })}`),
  updateMessage: (id: string, body: Partial<Message>) =>
    request<Message>(`/messages/${id}`, { method: "PATCH", body: JSON.stringify(body) }),

  // Appointments ---------------------------------------------------------
  listAppointments: (date_from?: string, date_to?: string) =>
    request<Appointment[]>(`/appointments${queryString({ date_from, date_to })}`),
  cancelAppointment: (id: string) =>
    request<Appointment>(`/appointments/${id}/cancel`, { method: "POST" }),

  // Contacts -------------------------------------------------------------
  listContacts: (q?: { query?: string; is_blocked?: boolean }) =>
    request<Contact[]>(`/contacts${queryString(q)}`),
  blockContact: (id: string) =>
    request<Contact>(`/contacts/${id}/block`, { method: "POST" }),
  unblockContact: (id: string) =>
    request<Contact>(`/contacts/${id}/unblock`, { method: "POST" }),

  // Config ---------------------------------------------------------------
  listPromptVersions: () => request<PromptVersion[]>("/config/prompt-versions"),
  publishPromptVersion: (id: string) =>
    request<PromptVersion>(`/config/prompt-versions/${id}/publish`, { method: "POST" }),

  // Knowledge ------------------------------------------------------------
  listKnowledge: () => request<KnowledgeItem[]>("/knowledge"),
  listKnowledgeGaps: () => request<KnowledgeGap[]>("/knowledge/gaps"),
  addKnowledgeItem: (title: string, content: string) =>
    request<KnowledgeItem>("/knowledge", {
      method: "POST",
      body: JSON.stringify({ title, content }),
    }),

  // Health ---------------------------------------------------------------
  health: () => request<{ ok: boolean; dependencies: Record<string, boolean> }>("/healthz"),
};

function queryString(params?: Record<string, unknown>): string {
  if (!params) return "";
  const q = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null && v !== "")
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
    .join("&");
  return q ? `?${q}` : "";
}

export { ApiError };