#!/usr/bin/env python3
"""Patient-facing HTML timeline built from the program knowledge base."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.reporting.message_design import escape_html, get_message_design


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FORECAST_PATH = PROJECT_ROOT / "results" / "forecasts.csv"
YEAR_START = 2026
YEAR_END = 2040

TIMELINE_PROGRAMS = [
    "SENTAN-PVS-NP",
    "SPVN06",
    "NAC Attack",
    "NPI-001",
    "OCU400",
    "MCO-010",
    "RV-001",
    "Botaretigene sparoparvovec",
    "AGTC-501",
    "DSP-3077",
]

FORECAST_TRIAL_PREFERENCES = {
    "MCO-010": "NCT04945772",
    "OCU400": "NCT06388200",
    "AGTC-501": "NCT04850118",
    "NPI-001": "NCT07290530",
    "NAC Attack": "NCT05537220",
    "SPVN06": "NCT05748873",
    "DSP-3077": "NCT06891885",
    "Botaretigene sparoparvovec": "NCT04794101",
}

MILESTONE_RANGES = {
    "SENTAN-PVS-NP": ("planned_start", "planned_end", "国内第1相"),
    "SPVN06": ("initial_data_readout", None, "初回データ読出し"),
    "NAC Attack": ("interim_progression_readout", "final_followup_completion", "進行評価・追跡"),
    "RV-001": ("interim_results_presented", "planned_trial_end", "国内Phase 1/2"),
}

MILESTONE_PREFERRED = {"SENTAN-PVS-NP", "SPVN06", "NAC Attack", "RV-001"}


@dataclass(frozen=True)
class TimelineItem:
    program_id: str
    label: str
    axis: str
    scope: str
    start_year: float
    end_year: float
    source_kind: str
    milestone: str

    @property
    def axis_class(self) -> str:
        if self.axis == "A":
            return "timeline-a"
        if self.axis == "B":
            return "timeline-b"
        return "timeline-mid"

    @property
    def lane(self) -> str:
        return "A" if self.axis == "A" else "B"


def load_forecast_rows(path: Path = FORECAST_PATH) -> dict[str, dict[str, str]]:
    """Load forecast rows keyed by NCT ID."""
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return {row["NCTId"]: row for row in csv.DictReader(f)}


def _parse_year(value: Any) -> float | None:
    text = str(value or "")
    if not text:
        return None
    import re

    match = re.search(r"(20\d{2})", text)
    if not match:
        return None
    year = float(match.group(1))
    lower = text.lower()
    if "q2" in lower:
        return year + 0.25
    if "q3" in lower or "h2" in lower:
        return year + 0.5
    if "q4" in lower or "end" in lower:
        return year + 0.75
    return year


def _normal_range(start: float, end: float | None) -> tuple[float, float]:
    end = end if end is not None else start + 1
    if end < start:
        end = start
    if end - start < 1:
        end = start + 1
    return start, end


def _format_year_range(start: float, end: float) -> str:
    start_year = int(start)
    end_year = int(end)
    if end_year <= start_year:
        end_year = start_year + 1
    suffix = "以降" if end > YEAR_END else ""
    return f"{start_year}〜{end_year}年{suffix}"


def _forecast_range(program_id: str,
                    program: dict[str, Any],
                    rows: dict[str, dict[str, str]]) -> tuple[float, float, str] | None:
    preferred_trial = FORECAST_TRIAL_PREFERENCES.get(program_id)
    candidates = []
    for trial_id in program.get("trial_ids", []) or []:
        row = rows.get(str(trial_id))
        if not row:
            continue
        candidates.append(row)

    if not candidates:
        return None

    selected = None
    if preferred_trial:
        selected = rows.get(preferred_trial)
    selected = selected or min(
        candidates,
        key=lambda row: float(row.get("median_approval_year") or 9999),
    )

    start = float(selected.get("pct10_approval_year") or selected["median_approval_year"])
    end = float(selected.get("pct90_approval_year") or selected["median_approval_year"])
    start, end = _normal_range(start, end)
    return start, end, "FDA承認予測"


def _milestone_range(program_id: str,
                     program: dict[str, Any]) -> tuple[float, float, str] | None:
    spec = MILESTONE_RANGES.get(program_id)
    if not spec:
        return None
    start_key, end_key, label = spec
    key_dates = program.get("key_dates", {}) or {}
    start = _parse_year(key_dates.get(start_key))
    if start is None:
        return None
    end = _parse_year(key_dates.get(end_key)) if end_key else None
    start, end = _normal_range(start, end)
    return start, end, f"{label}（予測）"


def build_timeline_items(kb: dict[str, Any]) -> list[TimelineItem]:
    """Build timeline items from clinical_programs.json and forecasts.csv."""
    programs = kb.get("programs", {})
    forecast_rows = load_forecast_rows()
    items: list[TimelineItem] = []

    for program_id in TIMELINE_PROGRAMS:
        program = programs.get(program_id)
        if not program:
            continue

        design = get_message_design(program)
        milestone = None
        if program_id in MILESTONE_PREFERRED:
            milestone = _milestone_range(program_id, program)
        milestone = milestone or _forecast_range(program_id, program, forecast_rows)
        milestone = milestone or _milestone_range(program_id, program)
        if not milestone:
            continue

        start, end, source_kind = milestone
        items.append(TimelineItem(
            program_id=program_id,
            label=design.get("axis_label", "分類未設定"),
            axis=design.get("axis", "unknown"),
            scope=design.get("genotype_scope", "未分類"),
            start_year=start,
            end_year=end,
            source_kind=source_kind,
            milestone=program.get("message_design", {}).get("landing_milestone")
            or program.get("status", ""),
        ))

    return items


def _position_style(item: TimelineItem) -> str:
    span = YEAR_END - YEAR_START
    left = max(0.0, min(100.0, (item.start_year - YEAR_START) / span * 100))
    display_end = min(max(item.end_year, item.start_year + 1), YEAR_END)
    width = max(7.5, (display_end - item.start_year) / span * 100)
    if left + width > 100:
        width = max(7.5, 100 - left)
    return f"--bar-left: {left:.2f}%; --bar-width: {width:.2f}%;"


def _render_scale() -> str:
    ticks = []
    for year in range(YEAR_START, YEAR_END + 1, 2):
        left = (year - YEAR_START) / (YEAR_END - YEAR_START) * 100
        ticks.append(
            f'<span class="timeline-tick" style="left: {left:.2f}%;">{year}</span>'
        )
    return "<div class=\"timeline-scale\" aria-hidden=\"true\">" + "".join(ticks) + "</div>"


def _render_row(item: TimelineItem) -> str:
    range_label = _format_year_range(item.start_year, item.end_year)
    title = (
        f"{item.program_id} — {item.source_kind} {range_label}。"
        "予測であり、承認や利用開始を保証しません。"
    )
    return f"""
        <div class="timeline-row">
            <div class="timeline-label">
                <strong>{escape_html(item.program_id)}</strong>
                <span>{escape_html(item.scope)}・{escape_html(item.label)}</span>
            </div>
            <div class="timeline-track">
                <div class="timeline-bar {item.axis_class}" style="{_position_style(item)}"
                     title="{escape_html(title)}" aria-label="{escape_html(title)}">
                    <span>{escape_html(item.program_id)}</span>
                    <small>{escape_html(range_label)}（予測）</small>
                </div>
            </div>
        </div>"""


def render_timeline(kb: dict[str, Any]) -> str:
    """Render a static, responsive horizontal timeline."""
    items = build_timeline_items(kb)
    a_rows = "\n".join(_render_row(item) for item in items if item.lane == "A")
    b_rows = "\n".join(_render_row(item) for item in items if item.lane == "B")

    return f"""
        <section class="content-wrapper timeline-section" aria-labelledby="timeline-heading">
            <h2 id="timeline-heading">タイムラインで見る治療の見通し（予測）</h2>
            <p>横棒は、各プログラムの次の臨床節目またはFDA承認予測を幅で示したものです。単一年で「治る」と読むのではなく、対象・病期・規制審査の不確実性を含む目安として見てください。</p>
            <div class="timeline-legend" aria-label="タイムライン凡例">
                <span><i class="legend-a"></i>A: 進行を遅らせる</span>
                <span><i class="legend-b"></i>B/中間: 視覚再建・根治を目指す</span>
            </div>
            <div class="timeline-scroll" role="region" aria-label="2026年から2040年までの治療プログラム予測タイムライン。各横棒のラベルでプログラム名、予測幅、注意書きを確認できます。" tabindex="0">
                <div class="timeline-chart">
                    {_render_scale()}
                    <h3>A: 進行を遅らせる</h3>
                    {a_rows}
                    <h3>B/中間: 視覚再建・根治を目指す</h3>
                    {b_rows}
                </div>
            </div>
            <p class="timeline-note">日本では、海外承認後にPMDA審査・薬価収載・施設整備が必要になるため、FDA承認から2〜5年程度の遅れを見込むのが現実的です。国内試験の節目はこの限りではありません。</p>
        </section>"""
