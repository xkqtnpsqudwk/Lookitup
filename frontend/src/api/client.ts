import type {
  SearchResponse,
  SortOption,
  Source,
  SourceCreate,
} from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json", ...(options?.headers || {}) },
      ...options,
    });
  } catch {
    throw new Error(
      "Backend is not reachable. Start FastAPI with: uvicorn main:app --reload",
    );
  }

  if (!response.ok) {
    let detail = `Request failed (${response.status}).`;
    try {
      const body = await response.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* keep default message */
    }
    throw new Error(detail);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  health: () => request<{ status: string }>("/health"),

  getSources: () => request<Source[]>("/sources"),

  addSource: (payload: SourceCreate) =>
    request<Source>("/sources", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  uploadPdf: async (file: File, name: string): Promise<Source> => {
    const form = new FormData();
    form.append("file", file);
    if (name) form.append("name", name);

    let response: Response;
    try {
      // No Content-Type header: the browser sets the multipart boundary itself.
      response = await fetch(`${API_BASE}/sources/pdf`, { method: "POST", body: form });
    } catch {
      throw new Error(
        "Backend is not reachable. Start FastAPI with: uvicorn main:app --reload",
      );
    }
    if (!response.ok) {
      let detail = `Upload failed (${response.status}).`;
      try {
        const body = await response.json();
        if (body?.detail) detail = body.detail;
      } catch {
        /* keep default */
      }
      throw new Error(detail);
    }
    return (await response.json()) as Source;
  },

  clearSources: () =>
    request<{ status: string; removed: number }>("/sources", {
      method: "DELETE",
    }),

  loadSamples: () =>
    request<{ added: number; sources: Source[] }>("/sources/load-samples", {
      method: "POST",
    }),

  search: (query: string, sort: SortOption) =>
    request<SearchResponse>(
      `/search?q=${encodeURIComponent(query)}&sort=${sort}`,
    ),
};
