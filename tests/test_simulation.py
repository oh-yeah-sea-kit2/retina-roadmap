"""シミュレーションロジックのユニットテスト"""

import sys
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import pytest
import yaml

# srcディレクトリをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sim.timeline_sim import (
    calculate_cumulative_approval_probability,
    get_current_phase_historical_success_rate,
    get_phase_success_rate,
    simulate_phase_duration,
    simulate_phase_success,
    simulate_single_program,
    run_monte_carlo_simulation,
    _match_program,
    _sample_triangular,
    _simulate_japan_delay,
    load_simulation_config,
)


@pytest.fixture
def sample_parameters():
    """テスト用パラメータ"""
    return {
        "phase_durations_years": {
            "PHASE1": {"min": 1.0, "median": 2.0, "max": 3.0},
            "PHASE2": {"min": 2.0, "median": 3.0, "max": 4.0},
            "PHASE3": {"min": 3.0, "median": 4.0, "max": 5.0},
        },
        "success_rate_policy": {
            "display_cap": 0.85,
        },
        "phase_success_rates": {
            "PHASE1": {"success_rate": 0.86},
            "PHASE2": {"success_rate": 0.78},
            "PHASE3": {"success_rate": 0.71},
        },
        "regulatory_timelines_years": {
            "BLA_MAA_submission": {"min": 0.5, "median": 1.0, "max": 1.5},
            "regulatory_review": {"min": 0.5, "median": 1.0, "max": 2.0},
        },
        "simulation_parameters": {
            "n_simulations": 100,
            "random_seed": 42,
        },
    }


@pytest.fixture
def sample_trial():
    """テスト用の臨床試験データ"""
    return pd.Series({
        "NCTId": "NCT00000001",
        "BriefTitle": "Test Gene Therapy Phase 2",
        "Phase": "PHASE2",
        "Status": "RECRUITING",
        "SponsorName": "Test Corp",
        "StartDate": pd.Timestamp("2024-01-01"),
    })


class TestSimulatePhaseHelper:
    """ヘルパー関数のテスト"""

    def test_sample_triangular_returns_in_range(self):
        np.random.seed(42)
        params = {"min": 1.0, "median": 2.0, "max": 3.0}
        for _ in range(100):
            val = _sample_triangular(params)
            assert 1.0 <= val <= 3.0

    def test_simulate_japan_delay_returns_in_range(self):
        np.random.seed(42)
        cfg = {"min": 3.0, "median": 5.0, "max": 7.0}
        for _ in range(100):
            val = _simulate_japan_delay(cfg)
            assert 3.0 <= val <= 7.0

    def test_match_program_by_title(self):
        trial = pd.Series({"BriefTitle": "MCO-010 trial", "NCTId": "NCT123", "SponsorName": "X"})
        match_fields = {"brief_title_keywords": ["MCO-010"], "nct_ids": [], "sponsor_keywords": []}
        assert _match_program(trial, match_fields)

    def test_match_program_by_nct_id(self):
        trial = pd.Series({"BriefTitle": "Some trial", "NCTId": "NCT04945772", "SponsorName": "X"})
        match_fields = {"brief_title_keywords": [], "nct_ids": ["NCT04945772"], "sponsor_keywords": []}
        assert _match_program(trial, match_fields)

    def test_match_program_no_match(self):
        trial = pd.Series({"BriefTitle": "Unrelated", "NCTId": "NCT000", "SponsorName": "Y"})
        match_fields = {"brief_title_keywords": ["MCO-010"], "nct_ids": [], "sponsor_keywords": []}
        assert not _match_program(trial, match_fields)


class TestSimulatePhaseDuration:
    """フェーズ期間シミュレーションのテスト"""

    def test_returns_positive(self, sample_parameters):
        np.random.seed(42)
        for phase in ["PHASE1", "PHASE2", "PHASE3"]:
            duration = simulate_phase_duration(phase, sample_parameters)
            assert duration > 0

    def test_unknown_phase_uses_default(self, sample_parameters):
        np.random.seed(42)
        duration = simulate_phase_duration("UNKNOWN", sample_parameters)
        assert 2.0 <= duration <= 4.0  # デフォルト三角分布(2,3,4)

    def test_respects_range(self, sample_parameters):
        np.random.seed(42)
        for _ in range(100):
            d = simulate_phase_duration("PHASE1", sample_parameters)
            assert 1.0 <= d <= 3.0


class TestSimulatePhaseSuccess:
    """フェーズ成功率シミュレーションのテスト"""

    def test_rate_1_is_capped_before_sampling(self, sample_parameters):
        params = {**sample_parameters}
        params["phase_success_rates"] = {"PHASE1": {"success_rate": 1.0}}
        np.random.seed(42)
        successes = sum(simulate_phase_success("PHASE1", params) for _ in range(1000))
        assert 800 <= successes <= 900

    def test_never_succeeds_at_rate_0(self, sample_parameters):
        params = {**sample_parameters}
        params["phase_success_rates"] = {"PHASE1": {"success_rate": 0.0}}
        for _ in range(50):
            assert not simulate_phase_success("PHASE1", params)

    def test_gene_therapy_reduces_phase3_success(self, sample_parameters):
        np.random.seed(42)
        n = 10000
        normal_success = sum(
            simulate_phase_success("PHASE3", sample_parameters, is_gene_therapy=False)
            for _ in range(n)
        )
        np.random.seed(42)
        gene_success = sum(
            simulate_phase_success("PHASE3", sample_parameters, is_gene_therapy=True)
            for _ in range(n)
        )
        # 遺伝子治療は10%低い成功率のため、成功数が少ないはず
        assert gene_success < normal_success

    def test_phase_rate_is_capped_for_display_and_calculation(self, sample_parameters):
        assert get_phase_success_rate("PHASE1", sample_parameters) == 0.85
        assert get_phase_success_rate("PHASE2", sample_parameters) == 0.78

    def test_cumulative_probability_multiplies_remaining_phases(self, sample_parameters):
        probability = calculate_cumulative_approval_probability("PHASE2", sample_parameters)
        assert abs(probability - (0.78 * 0.71)) < 0.001
        assert probability < 0.85

    def test_current_phase_rate_is_separate_from_cumulative(self, sample_parameters):
        phase_rate = get_current_phase_historical_success_rate("PHASE2", sample_parameters)
        cumulative = calculate_cumulative_approval_probability("PHASE2", sample_parameters)
        assert phase_rate == 0.78
        assert cumulative != phase_rate


class TestSimulateSingleProgram:
    """単一プログラムシミュレーションのテスト"""

    def test_returns_success_or_failure(self, sample_trial, sample_parameters):
        np.random.seed(42)
        sim_config = load_simulation_config()
        result = simulate_single_program(
            sample_trial, sample_parameters, datetime(2025, 1, 1), sim_config
        )
        assert "success" in result
        if result["success"]:
            assert "approval_year" in result
            assert "japan_approval_year" in result
        else:
            assert "failed_at_phase" in result

    def test_japan_approval_after_fda(self, sample_trial, sample_parameters):
        np.random.seed(42)
        sim_config = load_simulation_config()
        found_success = False
        for _ in range(50):
            result = simulate_single_program(
                sample_trial, sample_parameters, datetime(2025, 1, 1), sim_config
            )
            if result["success"]:
                assert result["japan_approval_year"] >= result["approval_year"]
                found_success = True
                break
        assert found_success, "50回のシミュレーションで成功ケースが1件もなかった"

    def test_special_program_is_not_forced_to_100_percent(self, sample_parameters):
        trial = pd.Series({
            "NCTId": "NCT06388200",
            "BriefTitle": "A Phase 3 Study Of OCU400 Gene Therapy",
            "Phase": "PHASE3",
            "Status": "ACTIVE_NOT_RECRUITING",
            "SponsorName": "Ocugen",
            "StartDate": pd.Timestamp("2024-01-01"),
        })
        sim_config = load_simulation_config()
        np.random.seed(42)
        results = [
            simulate_single_program(trial, sample_parameters, datetime(2025, 1, 1), sim_config)
            for _ in range(1000)
        ]
        success_rate = sum(r["success"] for r in results) / len(results)
        assert 0.55 <= success_rate <= 0.75


class TestRunMonteCarloSimulation:
    def test_outputs_separate_probability_columns(self, sample_parameters):
        trials = pd.DataFrame([{
            "NCTId": "NCT06388200",
            "BriefTitle": "A Phase 3 Study Of OCU400 Gene Therapy",
            "Phase": "PHASE3",
            "Status": "ACTIVE_NOT_RECRUITING",
            "SponsorName": "Ocugen",
            "StartDate": pd.Timestamp("2024-01-01"),
        }])
        np.random.seed(42)
        df = run_monte_carlo_simulation(trials, sample_parameters, n_simulations=500)
        row = df.iloc[0]
        assert row["phase_historical_success_rate"] <= 0.85
        assert row["cumulative_approval_probability"] <= 0.85
        assert row["success_rate"] == row["cumulative_approval_probability"]
        assert row["success_rate"] < 1.0


class TestLoadSimulationConfig:
    """設定ファイル読み込みのテスト"""

    def test_loads_config(self):
        config = load_simulation_config()
        assert "japan_delay_years" in config
        assert "programs" in config

    def test_config_has_required_programs(self):
        config = load_simulation_config()
        programs = config["programs"]
        for name in ["MCO-010", "OCU400", "Botaretigene", "VP-001", "AGTC-501"]:
            assert name in programs, f"Program {name} missing from config"
