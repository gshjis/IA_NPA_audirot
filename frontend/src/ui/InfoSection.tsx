import { useCallback, useState } from "react";
import { getAnalysisStats } from "../api";
import type { AnalysisStatsResponse } from "../api/types";
import type { AnalysisChangeRow } from "../api/analysisTypes";
import { FileUploadSection, type FileUploadPhase } from "./FileUploadSection";
import { PlatformStatsBanner } from "./PlatformStatsBanner";
import { StatsSection } from "./StatsSection";
import styles from "./InfoSection.module.css";

export function InfoSection() {
  const [analysisRows, setAnalysisRows] = useState<AnalysisChangeRow[] | null>(
    null
  );
  const [platformStats, setPlatformStats] =
    useState<AnalysisStatsResponse | null>(null);
  const [platformStatsLoading, setPlatformStatsLoading] = useState(true);
  const [platformStatsError, setPlatformStatsError] = useState(false);
  const [uploadPhase, setUploadPhase] = useState<FileUploadPhase>("upload");

  const onAnalysisRowsChange = useCallback(
    (rows: AnalysisChangeRow[] | null) => {
      setAnalysisRows(rows);
    },
    []
  );

  const refreshPlatformStats = useCallback(async () => {
    setPlatformStatsLoading(true);
    setPlatformStatsError(false);
    try {
      const data = await getAnalysisStats();
      setPlatformStats(data);
    } catch {
      setPlatformStatsError(true);
    } finally {
      setPlatformStatsLoading(false);
    }
  }, []);

  const showSidebar = uploadPhase === "upload";

  return (
    <main className={styles.main}>
      {showSidebar && (
        <div className={styles.sidebar}>
          <PlatformStatsBanner
            stats={platformStats}
            loading={platformStatsLoading}
            error={platformStatsError}
          />
          <StatsSection rows={analysisRows} />
        </div>
      )}
      <div className={styles.uploadWrap}>
        <FileUploadSection
          onAnalysisRowsChange={onAnalysisRowsChange}
          onUploadPhaseActive={refreshPlatformStats}
          onPhaseChange={setUploadPhase}
        />
      </div>
    </main>
  );
}
