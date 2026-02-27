"""パラメータ推定ロジックのユニットテスト"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingest.parameters import (
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

    def test_phase1_rate_reflects_data(self, sample_trials_df):
        result = calculate_success_rates(sample_trials_df)
        # 5 completed + 2 terminated = 7 total, 5/7 success
        rate = result["PHASE1"]["success_rate"]
        assert abs(rate - 5 / 7) < 0.01


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
