import { Hero } from "./ui/Hero";
import { InfoSection } from "./ui/InfoSection";
import styles from "./App.module.css";

function App() {
  return (
    <div className={styles.layout}>
      <Hero />
      <InfoSection />
    </div>
  );
}

export default App;
