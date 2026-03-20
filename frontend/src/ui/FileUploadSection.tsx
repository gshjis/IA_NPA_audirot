import { useState, useEffect } from "react";
import { extractChangeRows } from "../api/analysisParse";
import type { AnalysisChangeRow } from "../api/analysisTypes";
import { uploadAndCompare, getAnalysis } from "../api";
import { MOCK_ANALYSIS_ROWS } from "../data/mockAnalysisRows";
import { Icon } from "../icons/Icon";
import { AnalysisResultsView } from "./AnalysisResultsView";
import { FileUploadCard } from "./FileUploadCard";
import styles from "./FileUploadSection.module.css";

/** `true` — демо с моком без бэкенда. `false` — реальный upload + polling. */
const USE_MOCK_ANALYSIS = true;

const MOCK_DELAY_MS = 1600;
const POLL_INTERVAL_MS = 5000;

type Phase = "upload" | "analyzing" | "results";

type FileUploadSectionProps = {
  onAnalysisRowsChange?: (rows: AnalysisChangeRow[] | null) => void;
};

function analysisStatus(data: unknown): string | undefined {
  if (data !== null && typeof data === "object" && "status" in data) {
    const s = (data as { status: unknown }).status;
    return typeof s === "string" ? s : undefined;
  }
  return undefined;
}

function isValidFile(file: File | null): boolean {
  if (!file) return false;
  const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
  return ext === "pdf" || ext === "docx";
}

export function FileUploadSection({
  onAnalysisRowsChange,
}: FileUploadSectionProps) {
  const [phase, setPhase] = useState<Phase>("upload");
  const [oldFile, setOldFile] = useState<File | null>(null);
  const [newFile, setNewFile] = useState<File | null>(null);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [submitAttempted, setSubmitAttempted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisData, setAnalysisData] = useState<unknown | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [resultRows, setResultRows] = useState<AnalysisChangeRow[] | null>(null);
  const [rawFallback, setRawFallback] = useState<unknown | null>(null);

  const oldValid = isValidFile(oldFile);
  const newValid = isValidFile(newFile);
  const bothValid = oldValid && newValid;
  const showError = submitAttempted && !bothValid;

  useEffect(() => {
    if (bothValid) setSubmitAttempted(false);
  }, [bothValid]);

  useEffect(() => {
    onAnalysisRowsChange?.(resultRows);
  }, [resultRows, onAnalysisRowsChange]);

  useEffect(() => {
    if (!analysisId || USE_MOCK_ANALYSIS) return;
    let cancelled = false;
    let isFirst = true;
    let intervalId: ReturnType<typeof setInterval> | null = null;

    const run = async () => {
      if (isFirst) {
        setAnalysisLoading(true);
        isFirst = false;
      }
      try {
        const data = await getAnalysis(analysisId);
        if (cancelled) return;
        setAnalysisData(data);
        const status =
          data && typeof data === "object" && "status" in data
            ? (data as { status?: string }).status
            : undefined;
        if (status !== "running" && status !== "pending") {
          if (intervalId) clearInterval(intervalId);
          intervalId = null;
        }
      } catch (e) {
        if (!cancelled) {
          setAnalysisData({
            error: e instanceof Error ? e.message : "Ошибка загрузки",
          });
        }
        if (intervalId) clearInterval(intervalId);
      } finally {
        if (!cancelled) setAnalysisLoading(false);
      }
    };

    run();
    intervalId = setInterval(run, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      if (intervalId) clearInterval(intervalId);
    };
  }, [analysisId]);

  useEffect(() => {
    if (USE_MOCK_ANALYSIS || !analysisData || phase !== "analyzing") return;

    if (analysisData !== null && typeof analysisData === "object" && "error" in analysisData) {
      setError(String((analysisData as { error: unknown }).error));
      setPhase("upload");
      setAnalysisId(null);
      return;
    }

    const status = analysisStatus(analysisData);
    if (status === "running" || status === "pending") return;

    const rows = extractChangeRows(analysisData);
    if (rows !== null) {
      setResultRows(rows);
      setRawFallback(null);
      setPhase("results");
      return;
    }

    setResultRows(null);
    setRawFallback(analysisData);
    setPhase("results");
  }, [analysisData, phase]);

  const resetToUpload = () => {
    setPhase("upload");
    setAnalysisId(null);
    setAnalysisData(null);
    setResultRows(null);
    setRawFallback(null);
    setError(null);
    setAnalysisLoading(false);
    setOldFile(null);
    setNewFile(null);
    setSubmitAttempted(false);
  };

  const handleCompare = async () => {
    setSubmitAttempted(true);
    if (!bothValid) return;

    setError(null);
    setRawFallback(null);
    setResultRows(null);

    if (USE_MOCK_ANALYSIS) {
      setPhase("analyzing");
      setLoading(true);
      window.setTimeout(() => {
        setLoading(false);
        setResultRows(MOCK_ANALYSIS_ROWS);
        setPhase("results");
      }, MOCK_DELAY_MS);
      return;
    }

    setLoading(true);
    setAnalysisData(null);
    try {
      const res = await uploadAndCompare(oldFile!, newFile!);
      setAnalysisId(res.analysis_id);
      setPhase("analyzing");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
      setPhase("upload");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className={styles.section}>
      <h1 className={styles.title}>Сравнение редакций НПА</h1>

      {phase === "upload" && (
        <div>
          <p className={styles.intro}>
            Загрузите файлы для автоматического анализа и оценки юридических
            рисков.
          </p>

          <div className={styles.uploadGrid}>
            <FileUploadCard
              title="Старая редакция"
              description="Загрузите исходную редакцию НПА (.pdf, .docx)"
              icon={<Icon name="file-up" size={24} />}
              file={oldFile}
              onFileChange={setOldFile}
              hasError={showError && !oldValid}
            />
            <FileUploadCard
              title="Новая редакция"
              description="Загрузите измененную версию акта для сравнения"
              icon={<Icon name="file-up" size={24} />}
              file={newFile}
              onFileChange={setNewFile}
              hasError={showError && !newValid}
            />
          </div>

          {error && <p className={styles.errorMsg}>{error}</p>}

          <button
            type="button"
            className={`${styles.compareBtn} ${showError ? styles.compareBtnError : ""}`}
            onClick={handleCompare}
            disabled={loading}
          >
            {loading ? "ЗАГРУЗКА..." : "СРАВНИТЬ РЕДАКЦИИ"}
          </button>
          <p className={styles.disclaimer}>
            ЗАШИФРОВАННАЯ И РЕГУЛЯТОРНО-СОВМЕСТИМАЯ ОБРАБОТКА
          </p>
        </div>
      )}

      {phase !== "upload" && (
        <div className={styles.analysisPanel}>
          {phase === "analyzing" && (
            <div className={styles.analysisState}>
              <div className={styles.loader}>
                <span className={styles.loaderSpinner} />
                <span>
                  {USE_MOCK_ANALYSIS
                    ? "Имитация анализа…"
                    : analysisLoading && !analysisData
                      ? "Загрузка анализа…"
                      : "Анализ выполняется…"}
                </span>
              </div>
              <div className={styles.tableSkeleton} aria-hidden>
                <div className={styles.skeletonBar} />
                <div className={styles.skeletonBar} />
                <div className={styles.skeletonBar} />
                <div className={styles.skeletonBar} />
              </div>
            </div>
          )}

          {phase === "results" && resultRows && (
            <div className={styles.resultsBlock}>
              <p className={styles.resultsBanner}>Анализ выполнен</p>
              <AnalysisResultsView rows={resultRows} />
              <button type="button" className={styles.newCompareBtn} onClick={resetToUpload}>
                Новое сравнение
              </button>
            </div>
          )}

          {phase === "results" && resultRows === null && rawFallback != null && (
            <div className={styles.resultsBlock}>
              <p className={styles.errorMsg}>Не удалось разобрать ответ API.</p>
              <details className={styles.rawDetails}>
                <summary className={styles.rawSummary}>Полный ответ</summary>
                <pre className={styles.jsonOutput}>
                  {JSON.stringify(rawFallback, null, 2)}
                </pre>
              </details>
              <button type="button" className={styles.newCompareBtn} onClick={resetToUpload}>
                Новое сравнение
              </button>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
