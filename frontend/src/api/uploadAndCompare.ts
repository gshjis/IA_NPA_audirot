import type { UploadAndCompareResponse } from "./types";

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
