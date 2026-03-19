import heroImg from "../assets/ai_npa-hero.png";
import styles from "./Hero.module.css";

export function Hero() {
  return (
    <header className={styles.header}>
      <div className={styles.imgWrapper}>
        <img className={styles.img} src={heroImg} alt="Hero" />
      </div>
    </header>
  );
} 