import { FileUploadSection } from "./FileUploadSection";
import { StatsSection } from "./StatsSection";
import styles from "./InfoSection.module.css";

export function InfoSection() {
  return (
    <main className={styles.main}>
      <StatsSection />
      <FileUploadSection />
    </main>
  );
}
