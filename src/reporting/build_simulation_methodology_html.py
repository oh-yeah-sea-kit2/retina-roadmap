#!/usr/bin/env python3
"""共通のMarkdown生成処理で公開方法論ページを再生成する。"""
from pathlib import Path
from src.reporting.convert_md_to_html import convert_with_nav


def convert_to_html():
    convert_with_nav(Path("docs/development/technical/simulation_methodology.md"),
                     "シミュレーション方法論", Path("docs/public/simulation_methodology.html"))


if __name__ == "__main__":
    convert_to_html()
