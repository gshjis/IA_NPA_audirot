import { Hero } from "./ui/Hero";
import { InfoSection } from "./ui/InfoSection";
import { FaqSection } from "./ui/FaqSection";
import styles from "./App.module.css";

function App() {
  return (
    <div className={styles.layout}>
      <Hero />
      <InfoSection />
      <FaqSection />
    </div>
  );
}

export default App;
