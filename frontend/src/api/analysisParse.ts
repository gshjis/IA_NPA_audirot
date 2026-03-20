import type { AnalysisChangeRow } from "./analysisTypes";

function isChangeRow(x: unknown): x is AnalysisChangeRow {
  if (x === null || typeof x !== "object") return false;
  const o = x as Record<string, unknown>;
  return typeof o.article === "string" && typeof o.change_type === "string";
}

const ARRAY_KEYS = [
  "changes",
  "results",
  "items",
  "differences",
  "rows",
  "data",
  "comparison",
] as const;

export function extractChangeRows(data: unknown): AnalysisChangeRow[] | null {
  if (Array.isArray(data)) {
    if (data.length === 0) return [];
    return isChangeRow(data[0]) ? (data as AnalysisChangeRow[]) : null;
  }
  if (data !== null && typeof data === "object") {
    const o = data as Record<string, unknown>;
    for (const k of ARRAY_KEYS) {
      const v = o[k];
      if (Array.isArray(v) && (v.length === 0 || isChangeRow(v[0]))) {
        return v as AnalysisChangeRow[];
      }
    }
  }
  return null;
}
