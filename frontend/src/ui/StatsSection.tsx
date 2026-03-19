import styles from "./StatsSection.module.css";

export function StatsSection() {
  return (
    <section className={styles.section}>
      <div className={styles.card} data-variant="found">
        <div className={styles.iconWrapper}>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={styles.icon}
          >
            <path d="M3 3v16a2 2 0 0 0 2 2h16"></path>
            <path d="M18 17V9"></path>
            <path d="M13 17V5"></path>
            <path d="M8 17v-3"></path>
          </svg>
        </div>
        <div className={styles.content}>
          <h3 className={styles.title}>Найдено изменений</h3>
          <p className={styles.value}>102</p>
        </div>
      </div>
      <div className={styles.card} data-variant="critical">
        <div className={styles.iconWrapper}>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={styles.icon}
          >
            <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"></path>
            <path d="M12 9v4"></path>
            <path d="M12 17h.01"></path>
          </svg>
        </div>
        <div className={styles.content}>
          <h3 className={styles.title}>Критично</h3>
          <p className={styles.value}>42</p>
          <p className={styles.subtitle}>Требуется немедленная проверка</p>
        </div>
      </div>

      <div className={styles.card} data-variant="pending">
        <div className={styles.iconWrapper}>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={styles.icon}
          >
            <path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"></path>
            <circle cx="12" cy="12" r="3"></circle>
          </svg>
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
