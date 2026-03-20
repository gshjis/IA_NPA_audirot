import {
  computeAnalysisStats,
  type AnalysisChangeRow,
} from "../api/analysisTypes";
import { Icon } from "../icons/Icon";
import styles from "./StatsSection.module.css";

type StatsSectionProps = {
  rows: AnalysisChangeRow[] | null;
};

function formatInt(n: number) {
  return n.toLocaleString("ru-RU");
}

export function StatsSection({ rows }: StatsSectionProps) {
  const { total, critical, pending } = computeAnalysisStats(rows);

  return (
    <section className={styles.wrap} aria-label="Статистика текущего сравнения">
      <div className={styles.inner}>
        <div className={styles.header}>
          <span className={styles.badge} />
          <span className={styles.kicker}>Анализ</span>
        </div>
        <p className={styles.lead}>Показатели по текущему сравнению</p>

        <div className={styles.metrics}>
          <div className={styles.metric} data-accent="found">
            <div className={styles.metricIcon}>
              <Icon name="chart-column" size={20} className={styles.icon} />
            </div>
            <div className={styles.metricBody}>
              <span className={styles.metricLabel}>Найдено изменений</span>
              <span className={styles.metricValue}>{formatInt(total)}</span>
            </div>
          </div>

          <div className={styles.divider} aria-hidden />

          <div className={styles.metric} data-accent="critical">
            <div className={styles.metricIcon}>
              <Icon name="triangle-alert" size={20} className={styles.icon} />
            </div>
            <div className={styles.metricBody}>
              <span className={styles.metricLabel}>Критично</span>
              <span className={styles.metricValue}>{formatInt(critical)}</span>
              <span className={styles.metricSubtitle}>
                Требуется немедленная проверка
              </span>
            </div>
          </div>

          <div className={styles.divider} aria-hidden />

          <div className={styles.metric} data-accent="pending">
            <div className={styles.metricIcon}>
              <Icon name="eye" size={20} className={styles.icon} />
            </div>
            <div className={styles.metricBody}>
              <span className={styles.metricLabel}>Ожидание</span>
              <span className={styles.metricValue}>{formatInt(pending)}</span>
              <span className={styles.metricSubtitle}>
                Требует проверки человеком
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
