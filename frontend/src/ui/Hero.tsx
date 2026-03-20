import styles from "./Hero.module.css";

export function Hero() {
  return (
    <header className={styles.header}>
      <div className={styles.top}>
        <h1 className={styles.title}>
          <span className={styles.titleText}>
            AI НПА Аудитор
            <img
              className={styles.questionImg}
              src="/hero/question.png"
              alt=""
              decoding="async"
            />
            <img
              className={styles.wImg}
              src="/hero/w.png"
              alt=""
              decoding="async"
            />
            <img
              className={styles.belImg}
              src="/hero/bel.png"
              alt=""
              decoding="async"
            />
          </span>
        </h1>
        <p className={styles.subtitle}>СФОРМИРУЙ ЖУРНАЛ АУДИТА</p>
      </div>

      <div className={styles.handStage}>
        <img
          className={styles.hand}
          src="/hero/hand.png"
          alt=""
          decoding="async"
        />

        <span className={styles.heroConstitutionWrap}>
          <img
            className={styles.heroConstitution}
            src="/hero/constitution.png"
            alt=""
            decoding="async"
            data-hero-asset="constitution"
          />
        </span>
        <span className={styles.heroPrezidentWrap}>
          <img
            className={styles.heroPrezident}
            src="/hero/prezident.png"
            alt=""
            decoding="async"
            data-hero-asset="prezident"
          />
        </span>
        <span className={styles.heroLawWrap}>
          <img
            className={styles.heroLaw}
            src="/hero/law.png"
            alt=""
            decoding="async"
            data-hero-asset="law"
          />
        </span>
        <span className={styles.heroNpaCheckWrap}>
          <img
            className={styles.heroNpaCheck}
            src="/hero/npa-check.png"
            alt=""
            decoding="async"
            data-hero-asset="npa-check"
          />
        </span>
        <span className={styles.heroDisWrap}>
          <img
            className={styles.heroDis}
            src="/hero/dis.png"
            alt=""
            decoding="async"
            data-hero-asset="dis"
          />
        </span>
      </div>
    </header>
  );
}
