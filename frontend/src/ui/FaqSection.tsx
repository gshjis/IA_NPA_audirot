import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import styles from "./FaqSection.module.css";

const ITEMS = [
  {
    value: "formats",
    q: "Какие форматы файлов поддерживаются?",
    a: "Сервис принимает пары документов в форматах PDF и DOCX. Загрузите старую и новую редакции, затем запустите сравнение.",
  },
  {
    value: "privacy",
    q: "Как обрабатываются загруженные документы?",
    a: "Файлы передаются на сервер для анализа редакций. Используйте только документы, которые вы имеете право сравнивать в рамках своей работы.",
  },
  {
    value: "risks",
    q: "Что означают уровни риска в результатах?",
    a: "Система выделяет изменения и помечает их по степени внимания: критичные требуют немедленной проверки, остальные — по приоритету вашего регламента.",
  },
  {
    value: "time",
    q: "Почему анализ может занять время?",
    a: "Сравнение больших актов и извлечение структурированных изменений выполняется на сервере. Дождитесь завершения — статус отображается на экране.",
  },
] as const;

export function FaqSection() {
  return (
    <section className={styles.section} aria-labelledby="faq-heading">
      <div className={styles.card}>
        <h2 id="faq-heading" className={styles.heading}>
          Частые вопросы
        </h2>
        <p className={styles.lead}>
          Кратко о сервисе сравнения редакций НПА
        </p>
        <Accordion type="single" collapsible className={styles.accordion}>
          {ITEMS.map(({ value, q, a }) => (
            <AccordionItem key={value} value={value} className={styles.item}>
              <AccordionTrigger className={styles.trigger}>{q}</AccordionTrigger>
              <AccordionContent className={styles.content}>{a}</AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  );
}
