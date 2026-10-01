#!/usr/bin/env python3
"""Regenerate public CSS without changing published text, data, or links.

Usage: PYTHONPATH=. .venv/bin/python src/reporting/build_public_styles.py

Some published pages and their Markdown sources have diverged. Run the existing
content builders in an isolated copy, then transfer only their generated style
blocks. Full content rebuilds remain available through the individual builders.
Handwritten pages (detailed_analysis, disclaimer, medical_info, patient_guide)
use common.css; their page-specific styles have no generator.
"""

from pathlib import Path
import os
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STYLE_BLOCK = re.compile(r"<style\b[^>]*>[\s\S]*?</style>", re.IGNORECASE)
BUILDERS = (
    "build_report.py",
    "build_updates_page.py",
    "build_action_guide_html.py",
    "convert_md_to_html.py",
)
GENERATED_PAGES = (
    "accessible_summary.html",
    "faq.html",
    "index.html",
    "japan_action_guide.html",
    "reality_and_actions.html",
    "regional_approval_timeline.html",
    "report.html",
    "simulation_methodology.html",
    "updates.html",
)


def regenerate_public_styles():
    """Build all styles first, retaining every byte outside existing style blocks."""
    pending = {}
    with TemporaryDirectory(prefix="retina-styles-") as temp_dir:
        staging = Path(temp_dir)
        # Builders write metadata, Markdown and images as well as HTML. Keep all
        # those side effects in staging, including writes to data/ and results/.
        for directory in ("src", "docs", "data", "results"):
            shutil.copytree(
                PROJECT_ROOT / directory, staging / directory,
                ignore=shutil.ignore_patterns("__pycache__"),
            )
        shutil.copy2(PROJECT_ROOT / "README.md", staging / "README.md")
        env = dict(os.environ, PYTHONPATH=str(staging))
        for builder in BUILDERS:
            subprocess.run(
                [sys.executable, f"src/reporting/{builder}"],
                cwd=staging, env=env, check=True,
            )

        for filename in GENERATED_PAGES:
            output = PROJECT_ROOT / "docs/public" / filename
            original = output.read_text(encoding="utf-8")
            generated = (staging / "docs/public" / filename).read_text(encoding="utf-8")
            styles = STYLE_BLOCK.findall(generated)
            if not styles or len(styles) != len(STYLE_BLOCK.findall(original)):
                raise ValueError(f"Style block count changed: {filename}")
            replacements = iter(styles)
            updated = STYLE_BLOCK.sub(lambda match: next(replacements), original)
            if STYLE_BLOCK.sub("", updated) != STYLE_BLOCK.sub("", original):
                raise ValueError(f"Content changed outside styles: {filename}")
            pending[output] = updated

    for output, updated in pending.items():
        if output.read_text(encoding="utf-8") != updated:
            output.write_text(updated, encoding="utf-8")
        print(f"Styles regenerated: {output.name}")


if __name__ == "__main__":
    regenerate_public_styles()
