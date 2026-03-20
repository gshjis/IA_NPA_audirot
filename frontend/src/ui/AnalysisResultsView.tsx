import { useCallback, useEffect, useMemo, useState } from "react";
import {
  type AnalysisChangeRow,
  type ChangeType,
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

/** Единый id для строки таблицы и блока превью — прокрутка с дорожки */
export function analysisChangeRowDomId(index: number): string {
  return `analysis-change-${index}`;
}

type Props = {
  rows: AnalysisChangeRow[];
};

/** Сегментов на одной «странице» дорожки — иначе подписи накладываются друг на друга. */
const TRACK_PAGE_SIZE = 10;

type TypeFilter = "all" | ChangeType;
type RiskFilter = "all" | RiskVisual;
type SortMode = "article" | "risk_desc" | "risk_asc" | "type";

function riskRank(level: RiskVisual): number {
  if (level === "red") return 0;
  if (level === "yellow") return 1;
  return 2;
}

function changeTypeSortOrder(t: string): number {
  switch (t) {
    case "added":
      return 0;
    case "modified":
      return 1;
    case "removed":
      return 2;
    default:
      return 3;
  }
}

function applyFilters(
  list: AnalysisChangeRow[],
  typeFilter: TypeFilter,
  riskFilter: RiskFilter
): AnalysisChangeRow[] {
  return list.filter((row) => {
    if (typeFilter !== "all" && row.change_type !== typeFilter) return false;
    if (riskFilter !== "all" && resolveRiskLevel(row) !== riskFilter)
      return false;
    return true;
  });
}

function sortRows(list: AnalysisChangeRow[], mode: SortMode): AnalysisChangeRow[] {
  const out = [...list];
  switch (mode) {
    case "article":
      out.sort((a, b) => compareArticleRef(a.article, b.article));
      break;
    case "risk_desc":
      out.sort((a, b) => {
        const da = riskRank(resolveRiskLevel(a));
        const db = riskRank(resolveRiskLevel(b));
        if (da !== db) return da - db;
        return compareArticleRef(a.article, b.article);
      });
      break;
    case "risk_asc":
      out.sort((a, b) => {
        const da = riskRank(resolveRiskLevel(a));
        const db = riskRank(resolveRiskLevel(b));
        if (da !== db) return db - da;
        return compareArticleRef(a.article, b.article);
      });
      break;
    case "type":
      out.sort((a, b) => {
        const ta = changeTypeSortOrder(a.change_type);
        const tb = changeTypeSortOrder(b.change_type);
        if (ta !== tb) return ta - tb;
        return compareArticleRef(a.article, b.article);
      });
      break;
    default:
      break;
  }
  return out;
}

export function AnalysisResultsView({ rows }: Props) {
  const [resultMode, setResultMode] = useState<"table" | "preview">("table");
  const [trackPage, setTrackPage] = useState(0);
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("all");
  const [riskFilter, setRiskFilter] = useState<RiskFilter>("all");
  const [sortMode, setSortMode] = useState<SortMode>("article");

  const displayedRows = useMemo(() => {
    const filtered = applyFilters(rows, typeFilter, riskFilter);
    return sortRows(filtered, sortMode);
  }, [rows, typeFilter, riskFilter, sortMode]);

  const trackTotalPages = Math.max(
    1,
    Math.ceil(displayedRows.length / TRACK_PAGE_SIZE)
  );
  const trackPageIndex = Math.min(trackPage, trackTotalPages - 1);
  const trackPageRows = useMemo(
    () =>
      displayedRows.slice(
        trackPageIndex * TRACK_PAGE_SIZE,
        trackPageIndex * TRACK_PAGE_SIZE + TRACK_PAGE_SIZE
      ),
    [displayedRows, trackPageIndex]
  );

  useEffect(() => {
    setTrackPage(0);
  }, [rows.length, typeFilter, riskFilter, sortMode]);

  useEffect(() => {
    setTrackPage((p) => Math.min(p, trackTotalPages - 1));
  }, [trackTotalPages]);

  const scrollToRow = useCallback((index: number) => {
    const id = analysisChangeRowDomId(index);
    requestAnimationFrame(() => {
      document
        .getElementById(id)
        ?.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  }, []);

  if (rows.length === 0) {
    return (
      <p className={styles.emptyMessage}>Изменений для отображения нет.</p>
    );
  }

  if (displayedRows.length === 0) {
    return (
      <div className={styles.wrap}>
        <h2 className={styles.heading}>Результаты сравнения</h2>
        <div className={styles.filtersRow}>
          <div className={styles.filterField}>
            <label className={styles.filterLabel} htmlFor="chg-filter-type">
              Тип изменения
            </label>
            <select
              id="chg-filter-type"
              className={styles.filterSelect}
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value as TypeFilter)}
            >
              <option value="all">Все</option>
              <option value="added">Добавлено</option>
              <option value="modified">Изменено</option>
              <option value="removed">Удалено</option>
            </select>
          </div>
          <div className={styles.filterField}>
            <label className={styles.filterLabel} htmlFor="chg-filter-risk">
              Риск
            </label>
            <select
              id="chg-filter-risk"
              className={styles.filterSelect}
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value as RiskFilter)}
            >
              <option value="all">Все</option>
              <option value="green">Безопасно</option>
              <option value="yellow">Проверка</option>
              <option value="red">Противоречие</option>
            </select>
          </div>
        </div>
        <p className={styles.filteredEmpty}>
          Нет изменений по выбранным фильтрам. Сбросьте фильтр или выберите
          другие значения.
        </p>
      </div>
    );
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

      <div className={styles.filtersRow}>
        <div className={styles.filterField}>
          <label className={styles.filterLabel} htmlFor="chg-filter-type-main">
            Тип изменения
          </label>
          <select
            id="chg-filter-type-main"
            className={styles.filterSelect}
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as TypeFilter)}
          >
            <option value="all">Все</option>
            <option value="added">Добавлено</option>
            <option value="modified">Изменено</option>
            <option value="removed">Удалено</option>
          </select>
        </div>
        <div className={styles.filterField}>
          <label className={styles.filterLabel} htmlFor="chg-filter-risk-main">
            Риск
          </label>
          <select
            id="chg-filter-risk-main"
            className={styles.filterSelect}
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value as RiskFilter)}
          >
            <option value="all">Все</option>
            <option value="green">Безопасно</option>
            <option value="yellow">Проверка</option>
            <option value="red">Противоречие</option>
          </select>
        </div>
        <div className={styles.filterField}>
          <label className={styles.filterLabel} htmlFor="chg-sort">
            Сортировка
          </label>
          <select
            id="chg-sort"
            className={styles.filterSelect}
            value={sortMode}
            onChange={(e) => setSortMode(e.target.value as SortMode)}
          >
            <option value="article">По пункту (номеру)</option>
            <option value="risk_desc">По риску: сначала критичные</option>
            <option value="risk_asc">По риску: сначала безопасные</option>
            <option value="type">По типу изменения</option>
          </select>
        </div>
      </div>

      <div className={styles.track}>
        <p className={styles.trackTitle}>Дорожка изменений (по уровню риска)</p>
        <div className={styles.trackBar}>
          {trackPageRows.map((row, i) => {
            const risk = resolveRiskLevel(row);
            const globalIndex = trackPageIndex * TRACK_PAGE_SIZE + i;
            return (
              <button
                key={`${row.article}-${globalIndex}`}
                type="button"
                className={styles.trackSegment}
                data-risk={risk}
                title={`${row.article}: ${riskLabel(risk)} — перейти к строке`}
                aria-label={`Пункт ${row.article}, ${changeTypeLabel(row.change_type)}, ${riskLabel(risk)}`}
                onClick={() => scrollToRow(globalIndex)}
              >
                <span className={styles.trackArticle}>{row.article}</span>
                <span className={styles.trackType}>
                  {changeTypeLabel(row.change_type)}
                </span>
              </button>
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
                  displayedRows.length
                )}{" "}
                из {displayedRows.length}
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
                {displayedRows.map((row, i) => {
                  const risk = resolveRiskLevel(row);
                  const oldText = (row.old ?? "").trim();
                  const newText = (row.new ?? "").trim();
                  const law = formatLawReference(row);
                  const reco = (row.explanation ?? "").trim();
                  return (
                    <tr key={`${row.article}-${i}`} id={analysisChangeRowDomId(i)}>
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
          <AnalysisRevisionPreview
            rows={displayedRows}
            rowDomId={analysisChangeRowDomId}
          />
        </div>
      )}
    </div>
  );
}
