import { FileUploadSection } from "./FileUploadSection";
import { StatsSection } from "./StatsSection";

export function InfoSection() {
  return (
    <main>
      <StatsSection />
      <FileUploadSection />
    </main>
  );
}
