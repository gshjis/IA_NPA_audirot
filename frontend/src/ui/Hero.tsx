import heroImg from "../assets/ai_npa-hero.png";
import styles from "./Hero.module.css";

export function Hero() {
    return (
        <header>
            <img className={styles.img} src={heroImg} alt="Hero" />
        </header>
    )
} 