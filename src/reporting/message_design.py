#!/usr/bin/env python3
"""Patient-facing treatment classification helpers for Sprint 3."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
KNOWLEDGE_BASE_PATH = PROJECT_ROOT / "data" / "knowledge_base" / "clinical_programs.json"


AXIS_ORDER = ["A", "A/B", "B/intermediate", "B"]


def escape_html(value: Any) -> str:
    """Escape text for HTML output."""
    return html.escape(str(value or ""), quote=True)


def load_clinical_programs() -> dict[str, Any]:
    """Load the clinical-program knowledge base."""
    return json.loads(KNOWLEDGE_BASE_PATH.read_text(encoding="utf-8"))


def get_message_design(program: dict[str, Any]) -> dict[str, str]:
    """Return display classification with conservative fallbacks."""
    design = program.get("message_design", {}) or {}
    return {
        "axis": design.get("axis", "unknown"),
        "axis_label": design.get("axis_label", "分類未設定"),
        "genotype_scope": design.get("genotype_scope", "未分類"),
        "genotype_scope_key": design.get("genotype_scope_key", "unknown"),
        "patient_summary": design.get("patient_summary", ""),
        "eligibility_hint": design.get("eligibility_hint", ""),
    }


def build_trial_program_index(programs: dict[str, dict[str, Any]]) -> dict[str, str]:
    """Map trial/registry IDs to clinical-program IDs."""
    index: dict[str, str] = {}
    for program_id, program in programs.items():
        for trial_id in program.get("trial_ids", []) or []:
            index[str(trial_id)] = program_id
    return index


def program_for_forecast_row(row: dict[str, Any],
                             programs: dict[str, dict[str, Any]],
                             trial_index: dict[str, str] | None = None) -> str | None:
    """Find the best matching clinical-program ID for a forecast row."""
    trial_index = trial_index or build_trial_program_index(programs)
    nct_id = str(row.get("NCTId", ""))
    if nct_id in trial_index:
        return trial_index[nct_id]

    haystack = " ".join([
        str(row.get("BriefTitle", "")),
        str(row.get("SponsorName", "")),
    ]).lower()
    for program_id, program in programs.items():
        needles = [
            program_id,
            program.get("company", ""),
            program.get("modality", ""),
            program.get("target", ""),
        ]
        for needle in needles:
            needle = str(needle).strip().lower()
            if needle and needle in haystack:
                return program_id
    return None


def axis_sort_key(program: dict[str, Any]) -> tuple[int, str]:
    """Sort programs by patient-facing axis then phase-ish name."""
    axis = get_message_design(program)["axis"]
    try:
        axis_index = AXIS_ORDER.index(axis)
    except ValueError:
        axis_index = len(AXIS_ORDER)
    return axis_index, str(program.get("current_phase", ""))


def classification_badges(program: dict[str, Any]) -> str:
    """Render compact A/B and genotype labels."""
    design = get_message_design(program)
    axis_class = (
        "axis-a" if design["axis"] == "A"
        else "axis-b" if design["axis"] == "B"
        else "axis-mid"
    )
    scope_class = f"scope-{design['genotype_scope_key']}"
    return (
        f'<span class="tag {axis_class}">{escape_html(design["axis_label"])}</span>'
        f'<span class="tag {scope_class}">{escape_html(design["genotype_scope"])}</span>'
    )


def definition_block(kb: dict[str, Any]) -> str:
    """Render the fixed A/B definitions from the knowledge base."""
    axes = kb.get("message_design", {}).get("axes", {})
    a_def = axes.get("A", {}).get(
        "patient_definition",
        "視力を取り戻すものではないが、数年内に手が届きうる現実的な希望。",
    )
    b_def = axes.get("B", {}).get(
        "patient_definition",
        "10〜20年スパン。対象や病期が限られる。",
    )
    return (
        "<dl class=\"axis-definitions\">"
        "<div><dt>A: 進行を止める/遅らせる</dt>"
        f"<dd>{escape_html(a_def)}</dd></div>"
        "<div><dt>B: 失った視力を取り戻す/根治を目指す</dt>"
        f"<dd>{escape_html(b_def)}</dd></div>"
        "</dl>"
    )
