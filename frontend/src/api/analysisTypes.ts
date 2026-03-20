export type ChangeType = "modified" | "added" | "removed" | string;

export type AnalysisChangeRow = {
  article: string;
  change_type: ChangeType;
  old: string;
  new: string;
  similarity?: number;
  semantic_method?: string;
  relation?: string;
  conflict?: boolean;
  risk?: string;
  confidence?: number;
  law?: string;
  law_article?: string;
  evidence?: string;
  explanation?: string;
  assessment_source?: string;
  laws?: unknown[];
};

export type RiskVisual = "green" | "yellow" | "red";

export function resolveRiskLevel(row: AnalysisChangeRow): RiskVisual {
  const r = (row.risk ?? "").toLowerCase();
  if (r === "green" || r === "low" || r === "safe") return "green";
  if (r === "red" || r === "high" || r === "critical") return "red";
  if (r === "yellow" || r === "medium" || r === "amber") return "yellow";
  if (row.conflict === true) return "red";
  const rel = (row.relation ?? "").toLowerCase();
  if (rel.includes("contradict") || rel === "conflict") return "red";
  if (rel.includes("compliant") || rel === "ok" || rel === "clear") return "green";
  return "yellow";
}

export function formatLawReference(row: AnalysisChangeRow): string {
  const law = (row.law ?? "").trim();
  const art = (row.law_article ?? "").trim();
  if (law && art) return `${law}, ст. ${art}`;
  if (law) return law;
  if (art) return `ст. ${art}`;
  if (Array.isArray(row.laws) && row.laws.length > 0) {
    const first = row.laws[0];
    if (first && typeof first === "object") {
      const o = first as Record<string, unknown>;
      const title = typeof o.title === "string" ? o.title : typeof o.name === "string" ? o.name : "";
      const a = typeof o.article === "string" ? o.article : "";
      if (title && a) return `${title}, ст. ${a}`;
      if (title) return title;
    }
  }
  return "—";
}

/** Агрегаты для блока статистики: всего строк, критичных (red), на проверке (yellow). */
export function computeAnalysisStats(
  rows: AnalysisChangeRow[] | null | undefined
): { total: number; critical: number; pending: number } {
  if (!rows?.length) {
    return { total: 0, critical: 0, pending: 0 };
  }
  let critical = 0;
  let pending = 0;
  for (const row of rows) {
    const level = resolveRiskLevel(row);
    if (level === "red") critical++;
    else if (level === "yellow") pending++;
  }
  return { total: rows.length, critical, pending };
}

export function compareArticleRef(a: string, b: string): number {
  const pa = a.split(/[.]/).map((p) => parseInt(p, 10) || 0);
  const pb = b.split(/[.]/).map((p) => parseInt(p, 10) || 0);
  const n = Math.max(pa.length, pb.length);
  for (let i = 0; i < n; i++) {
    const da = pa[i] ?? 0;
    const db = pb[i] ?? 0;
    if (da !== db) return da - db;
  }
  return a.localeCompare(b, "ru");
}
