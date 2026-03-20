import { useId, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import type { AnalysisChangeRow, RiskVisual } from "../api/analysisTypes";
import {
  formatLawReference,
  resolveRiskLevel,
} from "../api/analysisTypes";
import styles from "./AnalysisRevisionPreview.module.css";

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
      return "Требует проверки";
    case "red":
      return "Потенциальное противоречие";
  }
}

function TooltipBody({ row }: { row: AnalysisChangeRow }) {
  const risk = resolveRiskLevel(row);
  const oldText = (row.old ?? "").trim();
  const newText = (row.new ?? "").trim();
  const law = formatLawReference(row);
  const reco = (row.explanation ?? "").trim();

  return (
    <>
      <p className={styles.tooltipTitle}>
        Пункт {row.article} · {changeTypeLabel(row.change_type)}
      </p>
      {oldText ? (
        <div className={styles.tooltipRow}>
          <span className={styles.tooltipLabel}>Было</span>
          <p className={styles.tooltipText}>{oldText}</p>
        </div>
      ) : null}
      {newText ? (
        <div className={styles.tooltipRow}>
          <span className={styles.tooltipLabel}>Стало</span>
          <p className={styles.tooltipText}>{newText}</p>
        </div>
      ) : null}
      {law !== "—" ? (
        <div className={styles.tooltipRow}>
          <span className={styles.tooltipLabel}>Норма</span>
          <p className={styles.tooltipText}>{law}</p>
        </div>
      ) : null}
      <div className={styles.tooltipRow}>
        <span className={styles.tooltipLabel}>Риск</span>
        <span className={styles.tooltipRisk} data-risk={risk}>
          {riskLabel(risk)}
        </span>
      </div>
      {reco ? (
        <div className={styles.tooltipRow}>
          <span className={styles.tooltipLabel}>Рекомендация</span>
          <p className={styles.tooltipText}>{reco}</p>
        </div>
      ) : null}
    </>
  );
}

function positionTooltip(
  anchor: HTMLElement,
  tip: HTMLElement,
  margin: number
): { top: number; left: number } {
  const ar = anchor.getBoundingClientRect();
  const tw = tip.offsetWidth;
  const th = tip.offsetHeight;

  let top = ar.bottom + margin;
  let left = ar.left + ar.width / 2 - tw / 2;

  const maxL = window.innerWidth - tw - margin;
  const minL = margin;
  left = Math.min(maxL, Math.max(minL, left));

  if (top + th > window.innerHeight - margin) {
    top = ar.top - th - margin;
  }
  if (top < margin) top = margin;

  return { top, left };
}

function ChangeTooltipPortal({
  open,
  anchorRef,
  tipId,
  children,
}: {
  open: boolean;
  anchorRef: React.RefObject<HTMLElement | null>;
  tipId: string;
  children: React.ReactNode;
}) {
  const tipRef = useRef<HTMLDivElement>(null);
  const [placed, setPlaced] = useState(false);
  const [style, setStyle] = useState<{ top: number; left: number }>({
    top: 0,
    left: 0,
  });

  useLayoutEffect(() => {
    if (!open) {
      setPlaced(false);
      return;
    }
    const anchor = anchorRef.current;
    const tip = tipRef.current;
    if (!anchor || !tip) return;

    const margin = 10;
    const apply = () => {
      setStyle(positionTooltip(anchor, tip, margin));
      setPlaced(true);
    };
    apply();
    const id = requestAnimationFrame(apply);
    return () => cancelAnimationFrame(id);
  }, [open, anchorRef]);

  if (!open) return null;

  return createPortal(
    <div
      ref={tipRef}
      id={tipId}
      className={`${styles.tooltip} ${placed ? styles.tooltipVisible : ""}`}
      style={{ top: style.top, left: style.left }}
      role="tooltip"
    >
      {children}
    </div>,
    document.body
  );
}

function HighlightedFragment({ row }: { row: AnalysisChangeRow }) {
  const risk = resolveRiskLevel(row);
  const text = (row.new ?? "").trim();
  const anchorRef = useRef<HTMLSpanElement>(null);
  const [open, setOpen] = useState(false);
  const tipId = useId().replace(/:/g, "");

  if (!text) return null;

  return (
    <>
      <span
        ref={anchorRef}
        className={styles.hilite}
        data-risk={risk}
        tabIndex={0}
        aria-describedby={open ? tipId : undefined}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
      >
        {text}
      </span>
      <ChangeTooltipPortal open={open} anchorRef={anchorRef} tipId={tipId}>
        <TooltipBody row={row} />
      </ChangeTooltipPortal>
    </>
  );
}

function RemovedBlock({ row }: { row: AnalysisChangeRow }) {
  const anchorRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const oldText = (row.old ?? "").trim();
  const tipId = useId().replace(/:/g, "");

  return (
    <>
      <div
        ref={anchorRef}
        className={styles.removedNote}
        tabIndex={0}
        aria-describedby={open ? tipId : undefined}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
      >
        <span className={styles.artLabel}>п. {row.article}</span>
        Фрагмент исключён из новой редакции
        {oldText ? " (наведите для текста)" : ""}
      </div>
      <ChangeTooltipPortal open={open} anchorRef={anchorRef} tipId={tipId}>
        <TooltipBody row={row} />
      </ChangeTooltipPortal>
    </>
  );
}

type Props = {
  rows: AnalysisChangeRow[];
  /** Индекс строки в списке результатов — для прокрутки с дорожки */
  rowDomId?: (index: number) => string;
};

export function AnalysisRevisionPreview({ rows, rowDomId }: Props) {
  const idAt = rowDomId ?? ((i: number) => `analysis-change-${i}`);
  return (
    <div className={styles.previewDoc}>
      <p className={styles.previewDocTitle}>
        Превью новой редакции · подсветка по данным сравнения
      </p>
      {rows.map((row, i) => {
        const key = `${row.article}-${i}`;
        const anchorId = idAt(i);
        if (row.change_type === "removed") {
          return (
            <div key={key} id={anchorId}>
              <RemovedBlock row={row} />
            </div>
          );
        }
        return (
          <p key={key} id={anchorId} className={styles.previewPara}>
            <span className={styles.artLabel}>п. {row.article}</span>
            <HighlightedFragment row={row} />
          </p>
        );
      })}
    </div>
  );
}
