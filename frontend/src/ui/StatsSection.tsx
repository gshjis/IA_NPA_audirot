import { Icon } from "../icons/Icon";
import styles from "./StatsSection.module.css";

export function StatsSection() {
  return (
    <section className={styles.section}>
      <div className={styles.card} data-variant="found">
        <div className={styles.iconWrapper}>
          <Icon name="chart-column" size={24} className={styles.icon} />
        </div>
        <div className={styles.content}>
          <h3 className={styles.title}>Найдено изменений</h3>
          <p className={styles.value}>102</p>
        </div>
      </div>
      <div className={styles.card} data-variant="critical">
        <div className={styles.iconWrapper}>
          <Icon name="triangle-alert" size={24} className={styles.icon} />
        </div>
        <div className={styles.content}>
          <h3 className={styles.title}>Критично</h3>
          <p className={styles.value}>42</p>
          <p className={styles.subtitle}>Требуется немедленная проверка</p>
        </div>
      </div>

      <div className={styles.card} data-variant="pending">
        <div className={styles.iconWrapper}>
          <Icon name="eye" size={24} className={styles.icon} />
        </div>
        <div className={styles.content}>
          <h3 className={styles.title}>Ожидание</h3>
          <p className={styles.value}>156</p>
          <p className={styles.subtitle}>Требует проверки человеком</p>
        </div>
      </div>
    </section>
  );
}
