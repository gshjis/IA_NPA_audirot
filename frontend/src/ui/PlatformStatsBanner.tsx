import type { AnalysisStatsResponse } from "../api/types";
import { Icon } from "../icons/Icon";
import styles from "./PlatformStatsBanner.module.css";

type PlatformStatsBannerProps = {
  stats: AnalysisStatsResponse | null;
  loading: boolean;
  error: boolean;
};

function formatInt(n: number) {
  return n.toLocaleString("ru-RU");
}

export function PlatformStatsBanner({
  stats,
  loading,
  error,
}: PlatformStatsBannerProps) {
  const scanned = stats?.total_documents_scanned ?? 0;
  const changes = stats?.total_changes_found ?? 0;

  return (
    <aside className={styles.wrap} aria-label="Статистика платформы">
      <div className={styles.inner}>
        <div className={styles.header}>
          <span className={styles.badge} />
          <span className={styles.kicker}>Сервис</span>
        </div>
        <p className={styles.lead}>Накопленная статистика сравнений</p>

        <div className={styles.metrics}>
          <div className={styles.metric} data-accent="docs">
            <div className={styles.metricIcon}>
              <Icon name="file-doc" size={20} className={styles.icon} />
            </div>
            <div className={styles.metricBody}>
              <span className={styles.metricLabel}>Документов обработано</span>
              {loading ? (
                <span className={styles.skeleton} aria-hidden />
              ) : (
                <span className={styles.metricValue} title={String(scanned)}>
                  {error ? "—" : formatInt(scanned)}
                </span>
              )}
            </div>
          </div>

          <div className={styles.divider} aria-hidden />

          <div className={styles.metric} data-accent="changes">
            <div className={styles.metricIcon}>
              <Icon name="chart-column" size={20} className={styles.icon} />
            </div>
            <div className={styles.metricBody}>
              <span className={styles.metricLabel}>Изменений выявлено</span>
              {loading ? (
                <span className={styles.skeleton} aria-hidden />
              ) : (
                <span className={styles.metricValue} title={String(changes)}>
                  {error ? "—" : formatInt(changes)}
                </span>
              )}
            </div>
          </div>
        </div>

        {error && !loading && (
          <p className={styles.hint}>Не удалось обновить данные с сервера</p>
        )}
      </div>
    </aside>
  );
}
