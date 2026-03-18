from __future__ import annotations

import difflib
from typing import Iterable


def _ordered_articles(sections: Iterable[dict[str, str]]) -> list[str]:
    return [section["article"] for section in sections]


class DiffService:
    def compare_sections(
        self,
        old_sections: list[dict[str, str]],
        new_sections: list[dict[str, str]],
    ) -> list[dict[str, str | float]]:
        old_map = {section["article"]: section for section in old_sections}
        new_map = {section["article"]: section for section in new_sections}

        article_order = list(dict.fromkeys(_ordered_articles(new_sections) + _ordered_articles(old_sections)))
        changes: list[dict[str, str | float]] = []

        for article in article_order:
            old_section = old_map.get(article)
            new_section = new_map.get(article)

            if old_section and new_section:
                old_text = old_section["text"].strip()
                new_text = new_section["text"].strip()
                if old_text == new_text:
                    continue
                ratio = difflib.SequenceMatcher(None, old_text, new_text).ratio()
                changes.append(
                    {
                        "article": article,
                        "change_type": "modified",
                        "old": old_text,
                        "new": new_text,
                        "diff_ratio": round(1 - ratio, 4),
                    }
                )
            elif new_section:
                changes.append(
                    {
                        "article": article,
                        "change_type": "added",
                        "old": "",
                        "new": new_section["text"].strip(),
                        "diff_ratio": 1.0,
                    }
                )
            elif old_section:
                changes.append(
                    {
                        "article": article,
                        "change_type": "removed",
                        "old": old_section["text"].strip(),
                        "new": "",
                        "diff_ratio": 1.0,
                    }
                )
        return changes
