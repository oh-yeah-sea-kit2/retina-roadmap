"""Public pages must pass WCAG AA in both color schemes."""

import json
from pathlib import Path
import shutil
import subprocess

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_PAGES = sorted((PROJECT_ROOT / "docs/public").glob("*.html"))
CHECK_CONTRAST = shutil.which("check-contrast")


@pytest.mark.skipif(CHECK_CONTRAST is None, reason="check-contrast is not installed")
@pytest.mark.parametrize("page", PUBLIC_PAGES, ids=lambda page: page.name)
def test_public_page_contrast(page):
    # No --only or --min override: check-contrast applies AA's 4.5:1 / 3:1
    # thresholds and inspects both light and dark by default.
    result = subprocess.run(
        [CHECK_CONTRAST, str(page), "--json"],
        cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, (
        f"{page.name} failed check-contrast:\n{result.stdout}\n{result.stderr}"
    )
    report = json.loads(result.stdout)
    assert set(report) == {"light", "dark"}
    for scheme, findings in report.items():
        assert findings["checked"] > 0, f"{page.name}: no {scheme} elements checked"
        assert findings["failures"] == [], f"{page.name} ({scheme}): {findings['failures']}"
