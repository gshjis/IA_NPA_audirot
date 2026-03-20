import { useCallback, useState } from "react";
import type { AnalysisChangeRow } from "../api/analysisTypes";
import { FileUploadSection } from "./FileUploadSection";
import { StatsSection } from "./StatsSection";
import styles from "./InfoSection.module.css";

export function InfoSection() {
  const [analysisRows, setAnalysisRows] = useState<AnalysisChangeRow[] | null>(
    null
  );

  const onAnalysisRowsChange = useCallback(
    (rows: AnalysisChangeRow[] | null) => {
      setAnalysisRows(rows);
    },
    []
  );

  return (
    <main className={styles.main}>
      <StatsSection rows={analysisRows} />
      <FileUploadSection onAnalysisRowsChange={onAnalysisRowsChange} />
    </main>
  );
}
