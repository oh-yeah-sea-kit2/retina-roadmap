"""パラメータ推定ロジックのユニットテスト"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingest.parameters import (
    cap_success_rate,
    calculate_phase_durations,
    calculate_success_rates,
    calculate_regulatory_duration,
)


@pytest.fixture
def sample_trials_df():
    """テスト用の臨床試験DataFrame"""
    data = []
    # PHASE1の完了試験
    for i in range(5):
        data.append({
            "NCTId": f"NCT0000{i}",
            "Phase": "PHASE1",
            "Status": "COMPLETED",
            "StartDate": pd.Timestamp("2020-01-01"),
            "CompletionDate": pd.Timestamp("2022-06-01"),
            "BriefTitle": f"Phase 1 Trial {i}",
        })
    # PHASE2の完了試験
    for i in range(5, 10):
        data.append({
            "NCTId": f"NCT0000{i}",
            "Phase": "PHASE2",
            "Status": "COMPLETED",
            "StartDate": pd.Timestamp("2019-01-01"),
            "CompletionDate": pd.Timestamp("2022-01-01"),
            "BriefTitle": f"Phase 2 Trial {i}",
        })
    # PHASE1の失敗試験
    for i in range(10, 12):
        data.append({
            "NCTId": f"NCT000{i}",
            "Phase": "PHASE1",
            "Status": "TERMINATED",
            "StartDate": pd.Timestamp("2020-01-01"),
            "CompletionDate": pd.Timestamp("2021-01-01"),
            "BriefTitle": f"Phase 1 Failed {i}",
        })
    return pd.DataFrame(data)


class TestCalculatePhaseDurations:
    def test_returns_dict(self, sample_trials_df):
        result = calculate_phase_durations(sample_trials_df)
        assert isinstance(result, dict)

    def test_has_required_phases(self, sample_trials_df):
        result = calculate_phase_durations(sample_trials_df)
        for phase in ["PHASE1", "PHASE2", "PHASE3"]:
            assert phase in result

    def test_durations_positive(self, sample_trials_df):
        result = calculate_phase_durations(sample_trials_df)
        for phase, stats in result.items():
            assert stats["min"] >= 0
            assert stats["median"] >= stats["min"]
            assert stats["max"] >= stats["median"]


class TestCalculateSuccessRates:
    def test_returns_dict(self, sample_trials_df):
        result = calculate_success_rates(sample_trials_df)
        assert isinstance(result, dict)

    def test_rates_between_0_and_1(self, sample_trials_df):
        result = calculate_success_rates(sample_trials_df)
        for phase, stats in result.items():
            assert 0.0 <= stats["success_rate"] <= 1.0

    def test_phase1_uses_configured_historical_rate_with_cap(self, sample_trials_df):
        result = calculate_success_rates(sample_trials_df)
        rate = result["PHASE1"]["success_rate"]
        assert rate == 0.85
        assert result["PHASE1"]["raw_success_rate"] == 0.86
        assert result["PHASE1"]["confidence"] == "configured_historical"

    def test_observed_counts_are_kept_separate(self, sample_trials_df):
        result = calculate_success_rates(sample_trials_df)
        assert result["PHASE1"]["observed_success_count"] == 5
        assert result["PHASE1"]["observed_total_count"] == 7
        assert abs(result["PHASE1"]["observed_completion_rate"] - 5 / 7) < 0.01

    def test_success_rate_cap_helper(self):
        assert cap_success_rate(1.0, 0.85) == 0.85
        assert cap_success_rate(-1.0, 0.85) == 0.0
        assert cap_success_rate(0.71, 0.85) == 0.71


class TestCalculateRegulatoryDuration:
    def test_returns_required_keys(self):
        result = calculate_regulatory_duration()
        assert "BLA_MAA_submission" in result
        assert "regulatory_review" in result

    def test_values_positive(self):
        result = calculate_regulatory_duration()
        for key, stats in result.items():
            assert stats["min"] > 0
            assert stats["median"] > 0
            assert stats["max"] > 0
