#!/usr/bin/env python3
"""First-occurrence glossary annotations for patient-facing pages."""

from __future__ import annotations

from dataclasses import dataclass

from bs4 import BeautifulSoup, NavigableString


@dataclass(frozen=True)
class GlossaryTerm:
    term: str
    title: str
    reading: str | None = None


GLOSSARY_TERMS = [
    GlossaryTerm("網膜色素変性症", "もうまくしきそへんせいしょう", "もうまくしきそへんせいしょう"),
    GlossaryTerm("光受容体", "ひかりじゅようたい", "ひかりじゅようたい"),
    GlossaryTerm("遺伝子治療", "いでんしちりょう", "いでんしちりょう"),
    GlossaryTerm("神経保護", "しんけいほご", "しんけいほご"),
    GlossaryTerm("型不問", "どの遺伝子変異でも対象になりうる治療"),
    GlossaryTerm("型特異", "特定の遺伝子変異がある人のみ対象"),
    GlossaryTerm("BLA", "生物学的製剤承認申請（FDAへの最終承認申請）"),
    GlossaryTerm("Phase 3", "承認前の最終段階の大規模臨床試験"),
    GlossaryTerm("第3相", "承認前の最終段階の大規模臨床試験"),
    GlossaryTerm("EAP", "拡大アクセスプログラム（承認前の特例投与）"),
    GlossaryTerm("iPS細胞", "人工多能性幹細胞（体細胞から作られる万能細胞）"),
    GlossaryTerm("光遺伝学", "遺伝子操作で光への感度を神経細胞に持たせる技術"),
    GlossaryTerm("RdCVF", "錐体保護因子（Rod-derived Cone Viability Factor）"),
]


SKIP_TAGS = {"abbr", "a", "code", "pre", "script", "style", "title", "rt", "ruby"}


def _make_markup(term: GlossaryTerm) -> str:
    escaped_title = term.title.replace('"', "&quot;")
    if term.reading:
        return (
            f'<ruby class="term-ruby">'
            f'<abbr class="term-abbr" title="{escaped_title}">{term.term}</abbr>'
            f'<rt>{term.reading}</rt>'
            f'</ruby>'
        )
    return f'<abbr class="term-abbr" title="{escaped_title}">{term.term}</abbr>'


def _is_skipped(node: NavigableString) -> bool:
    parent = node.parent
    while parent is not None:
        if getattr(parent, "name", None) in SKIP_TAGS:
            return True
        parent = parent.parent
    return False


def annotate_first_terms(html_content: str,
                         terms: list[GlossaryTerm] | None = None) -> str:
    """Wrap the first body occurrence of each glossary term with abbr/ruby."""
    soup = BeautifulSoup(html_content, "html.parser")
    root = soup.body or soup
    terms = terms or GLOSSARY_TERMS

    for term in terms:
        for node in list(root.find_all(string=True)):
            if _is_skipped(node) or term.term not in str(node):
                continue

            before, after = str(node).split(term.term, 1)
            fragment = BeautifulSoup(
                before + _make_markup(term) + after,
                "html.parser",
            )
            node.replace_with(fragment)
            break

    return str(soup)
