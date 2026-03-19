import { Icon } from "../icons/Icon";
import { FileUploadCard } from "./FileUploadCard";
import styles from "./FileUploadSection.module.css";

export function FileUploadSection() {
  return (
    <section className={styles.section}>
      <h1 className={styles.title}>Сравнение редакций НПА</h1>
      <p className={styles.intro}>
        Загрузите файлы для автоматического анализа и оценки юридических рисков.
      </p>

      <div className={styles.uploadGrid}>
        <FileUploadCard
          title="Старая редакция"
          description="Загрузите исходную редакцию НПА (.pdf, .docx)"
          icon={<Icon name="file-up" size={24} />}
        />
        <FileUploadCard
          title="Новая редакция"
          description="Загрузите измененную версию акта для сравнения"
          icon={<Icon name="file-up" size={24} />}
        />
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
