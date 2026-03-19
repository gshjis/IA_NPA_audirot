import styles from "./FileUploadSection.module.css";

export function FileUploadSection() {
  return (
    <section className={styles.section}>
      <h1 className={styles.title}>Сравнение редакций НПА</h1>
      <p className={styles.intro}>
        Загрузите файлы для автоматического анализа и оценки юридических рисков.
      </p>

      <div className={styles.uploadGrid}>
        <label className={styles.uploadCard}>
          <input type="file" accept=".pdf,.docx,.doc,.txt" className={styles.fileInput} />
          <div className={styles.iconCircle}>
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
            >
              <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"></path>
              <path d="M14 2v4a2 2 0 0 0 2 2h4"></path>
              <path d="M12 12v6"></path>
              <path d="m15 15-3-3-3 3"></path>
            </svg>
          </div>
          <div>
            <p className={styles.cardTitle}>Старая редакция</p>
            <p className={styles.cardDesc}>
              Загрузите исходную редакцию НПА (.pdf, .docx, .txt)
            </p>
          </div>
          <span className={styles.fileLabel}>📎 Выбрать файл</span>
        </label>
        <label className={styles.uploadCard}>
          <input type="file" accept=".pdf,.docx,.doc,.txt" className={styles.fileInput} />
          <div className={styles.iconCircle}>
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
            >
              <path d="M4 22h14a2 2 0 0 0 2-2V7l-5-5H6a2 2 0 0 0-2 2v4"></path>
              <path d="M14 2v4a2 2 0 0 0 2 2h4"></path>
              <path d="M3 15h6"></path>
              <path d="M6 12v6"></path>
            </svg>
          </div>
          <div>
            <p className={styles.cardTitle}>Новая редакция</p>
            <p className={styles.cardDesc}>
              Загрузите измененную версию акта для сравнения
            </p>
          </div>
          <span className={styles.fileLabel}>📎 Выбрать файл</span>
        </label>
      </div>

      <button type="button" className={styles.compareBtn}>
        СРАВНИТЬ РЕДАКЦИИ
      </button>
      <p className={styles.disclaimer}>
        ЗАШИФРОВАННАЯ И РЕГУЛЯТОРНО-СОВМЕСТИМАЯ ОБРАБОТКА
      </p>
    </section>
  );
}
