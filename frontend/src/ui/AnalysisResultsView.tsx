import { useEffect, useMemo, useState } from "react";
import {
  type AnalysisChangeRow,
  type RiskVisual,
  compareArticleRef,
  formatLawReference,
  resolveRiskLevel,
} from "../api/analysisTypes";
import { AnalysisRevisionPreview } from "./AnalysisRevisionPreview";
import styles from "./AnalysisResultsView.module.css";

function changeTypeLabel(t: string): string {
  switch (t) {
    case "modified":
      return "Изменено";
    case "added":
      return "Добавлено";
    case "removed":
      return "Удалено";
    default:
      return t;
  }
}

function riskLabel(level: RiskVisual): string {
  switch (level) {
    case "green":
      return "Безопасно";
    case "yellow":
      return "Проверка";
    case "red":
      return "Противоречие";
  }
}

type Props = {
  rows: AnalysisChangeRow[];
};

/** Сегментов на одной «странице» дорожки — иначе подписи накладываются друг на друга. */
const TRACK_PAGE_SIZE = 10;

export function AnalysisResultsView({ rows }: Props) {
  const [resultMode, setResultMode] = useState<"table" | "preview">("table");
  const [trackPage, setTrackPage] = useState(0);

  const sorted = useMemo(
    () => [...rows].sort((a, b) => compareArticleRef(a.article, b.article)),
    [rows]
  );

  const trackTotalPages = Math.max(1, Math.ceil(sorted.length / TRACK_PAGE_SIZE));
  const trackPageIndex = Math.min(trackPage, trackTotalPages - 1);
  const trackPageRows = useMemo(
    () =>
      sorted.slice(
        trackPageIndex * TRACK_PAGE_SIZE,
        trackPageIndex * TRACK_PAGE_SIZE + TRACK_PAGE_SIZE
      ),
    [sorted, trackPageIndex]
  );

  useEffect(() => {
    setTrackPage(0);
  }, [rows.length]);

  useEffect(() => {
    setTrackPage((p) => Math.min(p, trackTotalPages - 1));
  }, [trackTotalPages]);

  if (sorted.length === 0) {
    return <p className={styles.emptyMessage}>Изменений для отображения нет.</p>;
  }

  return (
    <div className={styles.wrap}>
      <h2 className={styles.heading}>Результаты сравнения</h2>

      <div
        className={styles.modeSwitch}
        role="tablist"
        aria-label="Режим отображения результатов"
      >
        <button
          type="button"
          role="tab"
          aria-selected={resultMode === "table"}
          className={
            resultMode === "table" ? styles.modeTabActive : styles.modeTab
          }
          onClick={() => setResultMode("table")}
        >
          Таблица
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={resultMode === "preview"}
          className={
            resultMode === "preview" ? styles.modeTabActive : styles.modeTab
          }
          onClick={() => setResultMode("preview")}
        >
          Превью новой редакции
        </button>
      </div>

      <div className={styles.track}>
        <p className={styles.trackTitle}>Дорожка изменений (по уровню риска)</p>
        <div className={styles.trackBar}>
          {trackPageRows.map((row, i) => {
            const risk = resolveRiskLevel(row);
            const globalIndex = trackPageIndex * TRACK_PAGE_SIZE + i;
            return (
              <div
                key={`${row.article}-${globalIndex}`}
                className={styles.trackSegment}
                data-risk={risk}
                title={`${row.article}: ${riskLabel(risk)}`}
              >
                <span className={styles.trackArticle}>{row.article}</span>
                <span className={styles.trackType}>
                  {changeTypeLabel(row.change_type)}
                </span>
              </div>
            );
          })}
        </div>
        {trackTotalPages > 1 && (
          <div
            className={styles.trackPagination}
            role="navigation"
            aria-label="Страницы дорожки изменений"
          >
            <button
              type="button"
              className={styles.trackPageBtn}
              disabled={trackPageIndex <= 0}
              onClick={() => setTrackPage((p) => Math.max(0, p - 1))}
            >
              Назад
            </button>
            <span className={styles.trackPageInfo}>
              Стр. {trackPageIndex + 1} из {trackTotalPages}
              <span className={styles.trackPageRange} aria-hidden>
                {" "}
                · {trackPageIndex * TRACK_PAGE_SIZE + 1}–
                {Math.min(
                  (trackPageIndex + 1) * TRACK_PAGE_SIZE,
                  sorted.length,
                )}{" "}
                из {sorted.length}
              </span>
            </span>
            <button
              type="button"
              className={styles.trackPageBtn}
              disabled={trackPageIndex >= trackTotalPages - 1}
              onClick={() =>
                setTrackPage((p) => Math.min(trackTotalPages - 1, p + 1))
              }
            >
              Вперёд
            </button>
          </div>
        )}
        <ul
          className={styles.trackLegend}
          aria-label="Условные обозначения уровня риска"
        >
          <li>
            <span
              className={`${styles.swatch} ${styles.swatchGreen}`}
              aria-hidden
            />
            — безопасно
          </li>
          <li>
            <span
              className={`${styles.swatch} ${styles.swatchYellow}`}
              aria-hidden
            />
            — требует проверки
          </li>
          <li>
            <span
              className={`${styles.swatch} ${styles.swatchRed}`}
              aria-hidden
            />
             — потенциальное противоречие
          </li>
        </ul>
      </div>

      {resultMode === "table" ? (
        <div className={styles.tableSection}>
          <p className={styles.trackTitle}>Сводная таблица</p>
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Пункт</th>
                  <th>Тип</th>
                  <th>Было</th>
                  <th>Стало</th>
                  <th>Статья закона</th>
                  <th>Риск</th>
                  <th>Рекомендация</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((row, i) => {
                  const risk = resolveRiskLevel(row);
                  const oldText = (row.old ?? "").trim();
                  const newText = (row.new ?? "").trim();
                  const law = formatLawReference(row);
                  const reco = (row.explanation ?? "").trim();
                  return (
                    <tr key={`${row.article}-${i}`}>
                      <td className={styles.cellArticle}>{row.article}</td>
                      <td>
                        <span className={styles.typePill}>
                          {changeTypeLabel(row.change_type)}
                        </span>
                      </td>
                      <td className={styles.cellText}>
                        {oldText ? (
                          oldText
                        ) : (
                          <span className={styles.emptyCell}>—</span>
                        )}
                      </td>
                      <td className={styles.cellText}>
                        {newText ? (
                          newText
                        ) : (
                          <span className={styles.emptyCell}>—</span>
                        )}
                      </td>
                      <td className={styles.cellLaw}>{law}</td>
                      <td>
                        <span className={styles.riskPill} data-risk={risk}>
                          {riskLabel(risk)}
                        </span>
                      </td>
                      <td className={styles.cellReco}>
                        {reco ? (
                          reco
                        ) : (
                          <span className={styles.emptyCell}>
                            Нет пояснения
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className={styles.previewSection}>
          <p className={styles.trackTitle}>
            Фрагменты поля «Стало» с подчёркиванием по уровню риска · подсказка
            по наведению или фокусу
          </p>
          <AnalysisRevisionPreview rows={sorted} />
        </div>
      )}
    </div>
  );
}
