import type { AnalysisStatsResponse, UploadAndCompareResponse } from "./types";

const API_BASE =
  import.meta.env.VITE_API_URL ?? "http://172.20.10.2:8001";

export async function uploadAndCompare(
  oldFile: File,
  newFile: File
): Promise<UploadAndCompareResponse> {
  const formData = new FormData();
  formData.append("old_file", oldFile);
  formData.append("new_file", newFile);

  const res = await fetch(`${API_BASE}/analysis/upload-and-compare`, {
    method: "POST",
    headers: {
      accept: "application/json",
    },
    body: formData,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Upload failed: ${res.status} ${text}`);
  }

  return res.json();
}

export async function getAnalysisStats(): Promise<AnalysisStatsResponse> {
  const res = await fetch(`${API_BASE}/analysis/stats`, {
    headers: { accept: "application/json" },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Stats fetch failed: ${res.status} ${text}`);
  }
  const data: unknown = await res.json();
  if (
    data !== null &&
    typeof data === "object" &&
    "total_documents_scanned" in data &&
    "total_changes_found" in data
  ) {
    const d = data as Record<string, unknown>;
    const scanned = d.total_documents_scanned;
    const changes = d.total_changes_found;
    if (typeof scanned === "number" && typeof changes === "number") {
      return { total_documents_scanned: scanned, total_changes_found: changes };
    }
  }
  throw new Error("Invalid stats response shape");
}

export async function getAnalysis(analysisId: string): Promise<unknown> {
  const res = await fetch(`${API_BASE}/analysis/${analysisId}`, {
    headers: { accept: "application/json" },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Analysis fetch failed: ${res.status} ${text}`);
  }
  return res.json();
}
