"""プログラム単位の到達予測と試験別モデルのゲートを検証する。"""
from copy import deepcopy
from datetime import date, datetime
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from src.sim.arrival_probability import make_forecast, stage_probabilities
from src.sim.timeline_sim import trial_probability, simulate_single_program
from src.reporting.arrival_visualization import render_arrival_probability

ROOT = Path(__file__).resolve().parents[1]
TODAY = date(2026, 10, 2)


@pytest.fixture(scope="module")
def inputs():
    kb = json.loads((ROOT / "data/knowledge_base/clinical_programs.json").read_text())
    cfg = yaml.safe_load((ROOT / "config/simulation_params.yaml").read_text())
    return kb, cfg


@pytest.fixture(scope="module")
def forecast(inputs):
    return make_forecast(*inputs, today=TODAY, simulations=4000)


def test_seed_reproducible(inputs, forecast):
    assert make_forecast(*inputs, today=TODAY, simulations=4000) == forecast


def test_years_monotonic_and_history_bounded(forecast):
    for group in forecast["groups"].values():
        for place in ("us", "japan"):
            general, history = group["general"][place], group["rp_history"][place]
            assert all(a <= b for a, b in zip(general, general[1:]))
            assert all(a <= b for a, b in zip(history, history[1:]))
            assert all(0 <= h <= g <= 1 for h, g in zip(history, general))
    for program in forecast["programs"].values():
        assert program["rp_history"]["probability"] <= program["general"]["probability"]


def test_correlation_reduces_slow_any_final_probability(inputs):
    kb, cfg = deepcopy(inputs)
    cfg["slow_progression_correlation"] = 0
    independent = make_forecast(kb, cfg, today=TODAY)
    cfg["slow_progression_correlation"] = .9
    correlated = make_forecast(kb, cfg, today=TODAY)
    for scenario in ("general", "rp_history"):
        for place in ("us", "japan"):
            assert correlated["groups"]["slow_any"][scenario][place][-1] < independent["groups"]["slow_any"][scenario][place][-1]


def test_multiple_ocu400_trials_count_once(inputs):
    kb, cfg = deepcopy(inputs)
    before = make_forecast(kb, cfg, today=TODAY, simulations=300)
    kb["programs"]["OCU400"]["trial_ids"] *= 2
    after = make_forecast(kb, cfg, today=TODAY, simulations=300)
    assert before == after
    assert list(after["programs"]).count("OCU400") == 1


def test_skipped_controlled_phase2_and_generic_gate(inputs):
    kb, cfg = deepcopy(inputs)
    forecast = kb["programs"]["NAC Attack"]["forecast"]
    skipped = stage_probabilities(forecast, cfg)
    assert skipped == {"P3": pytest.approx(.355 * .512)}
    assert stage_probabilities(forecast, cfg, scenario="rp_history")["P3"] == .111
    forecast["skipped_controlled_phase2"] = False
    assert skipped["P3"] < stage_probabilities(forecast, cfg)["P3"]
    assert stage_probabilities(kb["programs"]["MCO-010"]["forecast"], cfg) == {"filed": .911}


def test_not_started_delays_and_generic_japan_simultaneous(inputs):
    kb, cfg = deepcopy(inputs)
    kb["programs"] = {"NAC Attack": kb["programs"]["NAC Attack"]}
    before = make_forecast(kb, cfg, today=TODAY, simulations=1000)
    kb["programs"]["NAC Attack"]["forecast"]["not_started"] = True
    after = make_forecast(kb, cfg, today=TODAY, simulations=1000)
    for scenario in ("general", "rp_history"):
        assert after["programs"]["NAC Attack"][scenario]["us"]["median"] >= before["programs"]["NAC Attack"][scenario]["us"]["median"]
        assert after["programs"]["NAC Attack"][scenario]["us"] == after["programs"]["NAC Attack"][scenario]["japan"]


def test_landing_and_report_render_accessible_svg():
    from src.reporting.build_landing_page import generate_html
    from bs4 import BeautifulSoup
    for html in (generate_html(), (ROOT / "docs/public/report.html").read_text()):
        soup = BeautifulSoup(html, "html.parser")
        section = soup.select_one(".arrival-probability")
        assert "型を問わず進行を遅らせる治療が2030年までに日本で使える確率は" in section.h2.get_text()
        assert section.svg["aria-label"]
        assert len(section.select("details tbody tr")) == 40
        assert "var(--primary-color)" in str(section.svg)
        assert section.svg.select('polyline[stroke-dasharray]')


@pytest.mark.parametrize("nct,name,expected", [
    ("NCT04945772", "MCO-010", .911),
    ("NCT06388200", "OCU400", .512 * .9 * .911),
    ("NCT04850118", "AGTC-501", .85 * .911),
    ("NCT05537220", "NAC Attack", .355 * .512),
    ("NCT04794101", "Botaretigene sparoparvovec", .5 * .911),
])
def test_csv_probability_matches_sampled_gate(inputs, nct, name, expected):
    kb, cfg = inputs
    params = yaml.safe_load((ROOT / "data/processed/parameters.yaml").read_text())
    trial = pd.Series({"NCTId": nct, "BriefTitle": name + " Gene Therapy" if name not in ("NAC Attack",) else name,
                       "SponsorName": "X", "Phase": "PHASE3", "StartDate": pd.Timestamp("2024-01-01")})
    assert trial_probability(trial, params, cfg) == pytest.approx(expected)
    history = .111 if name == "NAC Attack" else expected
    assert trial_probability(trial, params, cfg, "rp_history") == pytest.approx(history)
    np.random.seed(42)
    draws = [simulate_single_program(trial, params, datetime(2026, 10, 2), cfg) for _ in range(3000)]
    assert sum(d["success"] for d in draws) / len(draws) == pytest.approx(expected, abs=.025)
    if name == "NAC Attack":
        successes = [d for d in draws if d["success"]]
        assert all(d["approval_year"] == 2029 and d["japan_delay_years"] == 0 for d in successes)


def test_static_pages_render_content_and_links():
    from bs4 import BeautifulSoup
    for name in ("detailed_analysis", "medical_info", "patient_guide", "disclaimer"):
        soup = BeautifulSoup((ROOT / f"docs/public/{name}.html").read_text(), "html.parser")
        assert soup.find("a", href="report.html") or soup.find("a", href="index.html")
        assert "<footer>" not in soup.get_text()
    detailed = BeautifulSoup((ROOT / "docs/public/detailed_analysis.html").read_text(), "html.parser")
    assert detailed.h1.get_text() == "詳細データと予測の前提"
    assert detailed.table
