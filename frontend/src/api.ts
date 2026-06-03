import type { UploadResponse, QueryResponse } from "./types";

const BASE = "/api";

export async function uploadCsv(file: File): Promise<UploadResponse> {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(`${BASE}/upload`, { method: "POST", body: fd });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(
      typeof err.detail === "string" ? err.detail : `Upload failed (${res.status})`,
    );
  }
  return res.json();
}

export async function askQuestion(question: string): Promise<QueryResponse> {
  const res = await fetch(`${BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(
      typeof err.detail === "string" ? err.detail : `Query failed (${res.status})`,
    );
  }
  return res.json();
}
