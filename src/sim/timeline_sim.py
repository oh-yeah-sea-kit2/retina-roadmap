#!/usr/bin/env python3
"""
モンテカルロシミュレーションによる治療承認時期の予測。
各活性プログラムについて10,000回のシミュレーションを実行。
"""

import pandas as pd
import numpy as np
import yaml
from pathlib import Path
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

# プロジェクトルートディレクトリ
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SUCCESS_RATE_CAP = 0.85
DEFAULT_PHASE_SUCCESS_RATE = 0.5
PHASE_ALIASES = {
    "EARLY_PHASE1": "PHASE1",
    "PHASE1": "PHASE1",
    "PHASE2": "PHASE2",
    "PHASE3": "PHASE3",
}
REMAINING_PHASE_MAP = {
    "EARLY_PHASE1": ["PHASE1", "PHASE2", "PHASE3"],
    "PHASE1": ["PHASE1", "PHASE2", "PHASE3"],
    "PHASE2": ["PHASE2", "PHASE3"],
    "PHASE3": ["PHASE3"],
    "PHASE1, PHASE2": ["PHASE1", "PHASE2", "PHASE3"],
    "PHASE2, PHASE3": ["PHASE2", "PHASE3"],
}


def load_simulation_config():
    """シミュレーション設定ファイルを読み込む"""
    config_file = PROJECT_ROOT / "config" / "simulation_params.yaml"
    if not config_file.exists():
        logger.warning("設定ファイルが見つかりません: %s（デフォルト値を使用）", config_file)
        return {}
    with open(config_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_data():
    """必要なデータを読み込む"""
    # 臨床試験データ
    trials_df = pd.read_parquet("data/processed/clinical_trials.parquet")

    # パラメータ
    with open("data/processed/parameters.yaml", "r") as f:
        parameters = yaml.safe_load(f)

    return trials_df, parameters


def _get_success_rate_cap(parameters: dict) -> float:
    """表示・計算に使う成功率の上限を取得"""
    policy = parameters.get("success_rate_policy", {})
    return float(policy.get("display_cap", DEFAULT_SUCCESS_RATE_CAP))


def _cap_probability(probability: float, parameters: dict) -> float:
    """確率を0-1かつ設定上限以下に丸める"""
    cap = _get_success_rate_cap(parameters)
    return float(min(cap, max(0.0, probability)))


def canonical_phase(phase: str) -> str:
    """成功率テーブルに存在するフェーズ名へ正規化"""
    if not phase:
        return "PHASE1"
    phase = phase.strip()
    return PHASE_ALIASES.get(phase, phase)


def get_remaining_phases(phase: str) -> List[str]:
    """現在フェーズから承認までに残る成功判定フェーズを返す"""
    if phase in REMAINING_PHASE_MAP:
        return REMAINING_PHASE_MAP[phase]

    parts = [canonical_phase(p) for p in phase.split(", ") if p]
    for part in parts:
        if part in REMAINING_PHASE_MAP:
            return REMAINING_PHASE_MAP[part]
    return ["PHASE1", "PHASE2", "PHASE3"]


def get_phase_success_rate(phase: str, parameters: dict,
                           is_gene_therapy: bool = False) -> float:
    """フェーズ別ヒストリカル成功率を返す"""
    canonical = canonical_phase(phase)
    success_params = parameters["phase_success_rates"].get(canonical, {})
    success_rate = success_params.get("success_rate", DEFAULT_PHASE_SUCCESS_RATE)
    success_rate = _cap_probability(success_rate, parameters)

    # 遺伝子治療の場合、Phase 3成功率を少し下げる（新規性が高いため）
    if is_gene_therapy and canonical == "PHASE3":
        success_rate = _cap_probability(success_rate * 0.9, parameters)

    return success_rate


def calculate_cumulative_approval_probability(phase: str, parameters: dict,
                                              is_gene_therapy: bool = False,
                                              override_rate: float = None) -> float:
    """残フェーズの成功率を掛け合わせ、プログラム累積承認確率を返す"""
    if override_rate is not None:
        return _cap_probability(override_rate, parameters)

    probability = 1.0
    for phase_name in get_remaining_phases(phase):
        probability *= get_phase_success_rate(phase_name, parameters, is_gene_therapy)
    return _cap_probability(probability, parameters)


def get_current_phase_historical_success_rate(phase: str, parameters: dict,
                                              is_gene_therapy: bool = False) -> float:
    """表示用の現在フェーズ平均ヒストリカル成功率を返す"""
    phases = get_remaining_phases(phase)
    current_phase = phases[0] if phases else canonical_phase(phase)
    return get_phase_success_rate(current_phase, parameters, is_gene_therapy)


def simulate_program_success(phase: str, parameters: dict,
                             is_gene_therapy: bool = False,
                             override_rate: float = None) -> bool:
    """プログラムの承認到達可否を成功率ポリシーに基づいてサンプリング"""
    if override_rate is not None:
        return np.random.random() < _cap_probability(override_rate, parameters)

    for phase_name in get_remaining_phases(phase):
        if not simulate_phase_success(phase_name, parameters, is_gene_therapy):
            return False
    return True


def _failure_result(phase: str, reason: str = "Historical phase success gate") -> Dict:
    """成功率ゲートで失敗した場合の結果"""
    failed_phase = get_remaining_phases(phase)[0]
    return {
        "success": False,
        "failed_at_phase": failed_phase,
        "time_to_failure": 0.0,
        "reason": reason,
    }


def is_gene_therapy_trial(trial: pd.Series) -> bool:
    """試験名・スポンサー名から遺伝子治療系かをざっくり判定"""
    text = " ".join([
        str(trial.get("BriefTitle", "")),
        str(trial.get("SponsorName", "")),
    ]).lower()
    return any(keyword in text for keyword in [
        "gene", "aav", "vector", "ocu400", "mco-010", "optogenetic",
        "agtc", "botaretigene", "laruparetigene",
    ])


def get_program_success_override(trial: pd.Series, sim_config: dict) -> float:
    """プログラム固有の成功率上書きがあれば取得"""
    for program_cfg in sim_config.get("programs", {}).values():
        override = program_cfg.get("success_rate")
        if override is None:
            continue
        if _match_program(trial, program_cfg.get("match_fields", {})):
            return float(override)
    return None


def get_active_programs(df):
    """アクティブなRP治療プログラムを抽出"""
    active_status = ["RECRUITING", "ACTIVE_NOT_RECRUITING", "NOT_YET_RECRUITING", 
                     "ENROLLING_BY_INVITATION"]
    
    active_trials = df[df["Status"].isin(active_status)].copy()
    
    # MCO-010とOCU400の特別処理 - COMPLETEDでも重要な試験は含める
    important_completed = df[
        (df["Status"] == "COMPLETED") & 
        (
            (df["NCTId"].isin(["NCT04945772", "NCT05203939", "NCT06388200"])) |  # MCO-010, OCU400
            (df["BriefTitle"].str.contains("MCO-010|OCU400|OCU-400", case=False, na=False))
        )
    ].copy()
    
    # 結合
    active_trials = pd.concat([active_trials, important_completed], ignore_index=True)
    
    # 開始日がない場合は現在日付を仮定
    active_trials["StartDate"] = active_trials["StartDate"].fillna(pd.Timestamp.now())
    
    logger.info("Found %d active trials", len(active_trials))
    return active_trials


def simulate_phase_duration(phase: str, parameters: dict) -> float:
    """三角分布を使ってフェーズ期間をシミュレート"""
    phase_params = parameters["phase_durations_years"].get(phase, {})
    
    if not phase_params:
        # デフォルト値
        return np.random.triangular(2, 3, 4)
    
    return np.random.triangular(
        phase_params["min"],
        phase_params["median"],
        phase_params["max"]
    )


def simulate_phase_success(phase: str, parameters: dict, is_gene_therapy: bool = False) -> bool:
    """フェーズの成功/失敗をシミュレート"""
    success_rate = get_phase_success_rate(phase, parameters, is_gene_therapy)
    return np.random.random() < success_rate


def _match_program(trial: pd.Series, match_fields: dict) -> bool:
    """設定ファイルのmatch_fieldsに基づいてプログラムを照合"""
    title = trial.get("BriefTitle", "")
    nct_id = trial.get("NCTId", "")
    sponsor = trial.get("SponsorName", "")

    for keyword in match_fields.get("brief_title_keywords", []):
        if keyword in title:
            return True
    for nid in match_fields.get("nct_ids", []):
        if nid in nct_id:
            return True
    for sk in match_fields.get("sponsor_keywords", []):
        if sk in sponsor:
            return True
    return False


def _sample_triangular(params: dict) -> float:
    """辞書からmin/median/maxを取得して三角分布サンプリング"""
    return np.random.triangular(params["min"], params["median"], params["max"])


def _simulate_japan_delay(japan_cfg: dict) -> float:
    """日本承認遅延をシミュレート"""
    return np.random.triangular(japan_cfg["min"], japan_cfg["median"], japan_cfg["max"])


def simulate_single_program(trial: pd.Series, parameters: dict,
                          current_date: datetime,
                          sim_config: dict = None) -> Dict:
    """単一プログラムの承認までのタイムラインをシミュレート"""
    if sim_config is None:
        sim_config = load_simulation_config()

    # 現在のフェーズを判定
    phase = trial["Phase"]
    start_date = trial["StartDate"]
    is_gene_therapy = is_gene_therapy_trial(trial)

    # 経過時間を考慮
    time_in_current_phase = (current_date - start_date).days / 365.25
    time_in_current_phase = max(0, time_in_current_phase)

    # 日本承認遅延のパラメータ（設定ファイルから読み込み）
    japan_delay_years = sim_config.get("japan_delay_years", {
        "min": 3.0, "median": 5.0, "max": 7.0
    })
    
    # 設定ファイルのプログラム定義を参照
    programs_cfg = sim_config.get("programs", {})

    # MCO-010の特別処理
    mco_cfg = programs_cfg.get("MCO-010", {})
    mco_match = mco_cfg.get("match_fields", {})
    if _match_program(trial, mco_match) or \
       ("Nanoscope" in trial.get("SponsorName", "") and phase in ["PHASE2", "PHASE3"]):
        if not simulate_program_success(phase, parameters, is_gene_therapy):
            return _failure_result(phase, "MCO-010 gated by cumulative historical phase success")

        # BLA完全提出予定日（rolling submissionの完了）
        bla_complete_date = datetime.fromisoformat(mco_cfg.get("bla_complete_date", "2026-03-31"))
        time_to_bla_complete = max(0, (bla_complete_date - current_date).days / 365.25)

        review_time = _sample_triangular(mco_cfg.get("review_time", {"min": 0.5, "median": 0.67, "max": 0.83}))
        total_time = time_to_bla_complete + review_time

        approval_date = current_date + timedelta(days=total_time * 365.25)

        # MCO-010は日本MHLW先駆け指定を取得 - 短縮された遅延を使用
        japan_sakigake_delay = sim_config.get("japan_delay_years_sakigake", japan_delay_years)
        japan_delay = _simulate_japan_delay(japan_sakigake_delay)
        japan_approval_date = approval_date + timedelta(days=japan_delay * 365.25)

        return {
            "success": True,
            "approval_date": approval_date,
            "approval_year": approval_date.year,
            "time_to_approval": total_time,
            "fast_track": mco_cfg.get("fast_track", True),
            "program_name": mco_cfg.get("program_name", "MCO-010"),
            "confidence": mco_cfg.get("confidence", "very_high"),
            "gene_agnostic": mco_cfg.get("gene_agnostic", True),
            "japan_sakigake": True,
            "japan_approval_date": japan_approval_date,
            "japan_approval_year": japan_approval_date.year,
            "japan_delay_years": japan_delay
        }
    
    # OCU400の特別処理
    ocu_cfg = programs_cfg.get("OCU400", {})
    ocu_match = ocu_cfg.get("match_fields", {})
    if _match_program(trial, ocu_match) or \
       ("Ocugen" in trial.get("SponsorName", "") and phase == "PHASE3"):
        if not simulate_program_success(phase, parameters, is_gene_therapy):
            return _failure_result(phase, "OCU400 gated by cumulative historical phase success")

        bla_submission_date = datetime.fromisoformat(ocu_cfg.get("submission_date", "2026-09-30"))
        time_to_submission = (bla_submission_date - current_date).days / 365.25

        if time_to_submission > 0:
            review_time = _sample_triangular(ocu_cfg.get("review_time", {"min": 0.83, "median": 1.0, "max": 1.17}))
            total_time = time_to_submission + review_time

            approval_date = current_date + timedelta(days=total_time * 365.25)
            japan_delay = _simulate_japan_delay(japan_delay_years)
            japan_approval_date = approval_date + timedelta(days=japan_delay * 365.25)

            return {
                "success": True,
                "approval_date": approval_date,
                "approval_year": approval_date.year,
                "time_to_approval": total_time,
                "program_name": ocu_cfg.get("program_name", "OCU400"),
                "confidence": ocu_cfg.get("confidence", "very_high"),
                "gene_agnostic": ocu_cfg.get("gene_agnostic", True),
                "rmat_designated": ocu_cfg.get("rmat_designated", True),
                "japan_approval_date": japan_approval_date,
                "japan_approval_year": japan_approval_date.year,
                "japan_delay_years": japan_delay
            }
    
    # Botaretigene/bota-vecの特別処理
    # LUMEOSは主要評価未達だが、MeiraGTxが取得し米欧日申請を進める方針。
    bot_cfg = programs_cfg.get("Botaretigene", {})
    bot_match = bot_cfg.get("match_fields", {})
    if _match_program(trial, bot_match):
        success_rate = bot_cfg.get("success_rate", 0.2)
        if simulate_program_success(phase, parameters, is_gene_therapy, override_rate=success_rate):
            submission_date = bot_cfg.get("submission_date")
            if submission_date:
                planned_submission = datetime.fromisoformat(submission_date)
                total_time = max(0, (planned_submission - current_date).days / 365.25)
            else:
                total_time = _sample_triangular(bot_cfg.get("submission_time", {"min": 0.25, "median": 0.5, "max": 1.0}))

            review_time = _sample_triangular(bot_cfg.get("review_time", {"min": 1.5, "median": 2.0, "max": 2.5}))
            total_time += review_time

            approval_date = current_date + timedelta(days=total_time * 365.25)
            japan_delay = _simulate_japan_delay(japan_delay_years)
            japan_approval_date = approval_date + timedelta(days=japan_delay * 365.25)

            return {
                "success": True,
                "approval_date": approval_date,
                "approval_year": approval_date.year,
                "time_to_approval": total_time,
                "program_name": bot_cfg.get("program_name", "Botaretigene sparoparvovec"),
                "confidence": bot_cfg.get("confidence", "low"),
                "japan_approval_date": japan_approval_date,
                "japan_approval_year": japan_approval_date.year,
                "japan_delay_years": japan_delay
            }
        else:
            return {
                "success": False,
                "failed_at_phase": "PHASE3",
                "time_to_failure": time_in_current_phase + 1.0,
                "reason": "Botaretigene regulatory path not achieved in this simulation"
            }
    
    # PYC VP-001の特別処理
    vp_cfg = programs_cfg.get("VP-001", {})
    vp_match = vp_cfg.get("match_fields", {})
    if _match_program(trial, vp_match) or \
       ("PYC" in trial.get("SponsorName", "") and "RP11" in trial.get("BriefTitle", "")):
        if phase in ["PHASE1", "PHASE1, PHASE2"]:
            if not simulate_program_success(phase, parameters, is_gene_therapy):
                return _failure_result(phase, "VP-001 gated by cumulative historical phase success")

            phase23_start = datetime.fromisoformat(vp_cfg.get("phase23_start_date", "2025-10-01"))
            time_to_phase23 = (phase23_start - current_date).days / 365.25

            if time_to_phase23 > 0:
                phase23_duration = _sample_triangular(vp_cfg.get("phase23_duration", {"min": 2.0, "median": 2.5, "max": 3.0}))
                analysis_time = _sample_triangular(vp_cfg.get("analysis_time", {"min": 0.5, "median": 0.75, "max": 1.0}))
                review_time = _sample_triangular(vp_cfg.get("review_time", {"min": 1.0, "median": 1.25, "max": 1.5}))

                total_time = time_to_phase23 + phase23_duration + analysis_time + review_time

                approval_date = current_date + timedelta(days=total_time * 365.25)
                japan_delay = _simulate_japan_delay(japan_delay_years)
                japan_approval_date = approval_date + timedelta(days=japan_delay * 365.25)

                return {
                    "success": True,
                    "approval_date": approval_date,
                    "approval_year": approval_date.year,
                    "time_to_approval": total_time,
                    "program_name": vp_cfg.get("program_name", "VP-001"),
                    "confidence": vp_cfg.get("confidence", "medium"),
                    "rna_therapy": vp_cfg.get("rna_therapy", True),
                    "japan_approval_date": japan_approval_date,
                    "japan_approval_year": japan_approval_date.year,
                    "japan_delay_years": japan_delay
                }
    
    # Beacon AGTC-501の特別処理
    agtc_cfg = programs_cfg.get("AGTC-501", {})
    agtc_match = agtc_cfg.get("match_fields", {})
    if _match_program(trial, agtc_match) or \
       ("Beacon" in trial.get("SponsorName", "") and "XLRP" in trial.get("BriefTitle", "")):
        if phase in ["PHASE2", "PHASE3", "PHASE2, PHASE3"]:
            if not simulate_program_success(phase, parameters, is_gene_therapy):
                return _failure_result(phase, "AGTC-501 gated by cumulative historical phase success")

            phase23_duration = _sample_triangular(agtc_cfg.get("phase23_duration", {"min": 1.5, "median": 2.0, "max": 2.5}))
            analysis_time = _sample_triangular(agtc_cfg.get("analysis_time", {"min": 0.5, "median": 0.75, "max": 1.0}))
            review_time = _sample_triangular(agtc_cfg.get("review_time", {"min": 1.0, "median": 1.25, "max": 1.5}))

            total_time = phase23_duration + analysis_time + review_time

            approval_date = current_date + timedelta(days=total_time * 365.25)
            japan_delay = _simulate_japan_delay(japan_delay_years)
            japan_approval_date = approval_date + timedelta(days=japan_delay * 365.25)

            return {
                "success": True,
                "approval_date": approval_date,
                "approval_year": approval_date.year,
                "time_to_approval": total_time,
                "program_name": agtc_cfg.get("program_name", "AGTC-501"),
                "confidence": agtc_cfg.get("confidence", "medium"),
                "xlrp_specific": agtc_cfg.get("xlrp_specific", True),
                "japan_approval_date": japan_approval_date,
                "japan_approval_year": japan_approval_date.year,
                "japan_delay_years": japan_delay
            }
    
    # フェーズ進行をシミュレート
    total_time = 0
    # 現在のフェーズに基づいて残りのフェーズを決定
    remaining_phases = get_remaining_phases(phase)
    
    # 各フェーズをシミュレート
    for i, phase_name in enumerate(remaining_phases):
        # 最初のフェーズは既に進行中
        if i == 0:
            phase_duration = simulate_phase_duration(phase_name, parameters)
            
            # 長期実施中の試験に対する処理を改善
            # Phase 3で既に長期間経過している場合、最低でも1-2年は追加で必要
            if phase_name == "PHASE3" and time_in_current_phase > phase_duration:
                # 既に予定期間を超過している場合、追加で1-3年必要と仮定
                additional_time = np.random.triangular(1.0, 2.0, 3.0)
                remaining_duration = additional_time
            else:
                remaining_duration = max(0.5, phase_duration - time_in_current_phase)
            
            total_time += remaining_duration
        else:
            phase_duration = simulate_phase_duration(phase_name, parameters)
            total_time += phase_duration
        
        if not simulate_phase_success(phase_name, parameters, is_gene_therapy):
            return {
                "success": False,
                "failed_at_phase": phase_name,
                "time_to_failure": total_time
            }
    
    # 規制当局承認プロセス
    reg_params = parameters["regulatory_timelines_years"]
    
    # BLA/MAA提出準備
    submission_time = np.random.triangular(
        reg_params["BLA_MAA_submission"]["min"],
        reg_params["BLA_MAA_submission"]["median"],
        reg_params["BLA_MAA_submission"]["max"]
    )
    total_time += submission_time
    
    # 規制当局レビュー
    review_time = np.random.triangular(
        reg_params["regulatory_review"]["min"],
        reg_params["regulatory_review"]["median"],
        reg_params["regulatory_review"]["max"]
    )
    total_time += review_time
    
    approval_date = current_date + timedelta(days=total_time * 365.25)
    
    # 日本承認の遅延をシミュレート
    japan_delay = _simulate_japan_delay(japan_delay_years)
    japan_approval_date = approval_date + timedelta(days=japan_delay * 365.25)

    return {
        "success": True,
        "time_to_approval": total_time,
        "approval_date": approval_date,
        "approval_year": approval_date.year,
        "japan_approval_date": japan_approval_date,
        "japan_approval_year": japan_approval_date.year,
        "japan_delay_years": japan_delay
    }


def run_monte_carlo_simulation(active_trials: pd.DataFrame,
                             parameters: dict,
                             n_simulations: int = 10000) -> pd.DataFrame:
    """全プログラムに対してモンテカルロシミュレーションを実行"""

    current_date = datetime.now()
    np.random.seed(parameters["simulation_parameters"]["random_seed"])
    sim_config = load_simulation_config()
    
    results = []
    
    for idx, trial in active_trials.iterrows():
        program_results = []
        
        logger.info("Simulating %s: %s...", trial['NCTId'], trial['BriefTitle'][:50])
        
        for sim in range(n_simulations):
            result = simulate_single_program(trial, parameters, current_date, sim_config)
            result["NCTId"] = trial["NCTId"]
            result["BriefTitle"] = trial["BriefTitle"]
            result["Phase"] = trial["Phase"]
            result["SponsorName"] = trial["SponsorName"]
            result["simulation"] = sim
            program_results.append(result)
        
        # 成功したシミュレーションのみで統計を計算
        success_results = [r for r in program_results if r["success"]]
        is_gene_therapy = is_gene_therapy_trial(trial)
        override_rate = get_program_success_override(trial, sim_config)
        phase_historical_success_rate = get_current_phase_historical_success_rate(
            trial["Phase"], parameters, is_gene_therapy
        )
        cumulative_approval_probability = calculate_cumulative_approval_probability(
            trial["Phase"], parameters, is_gene_therapy, override_rate
        )
        simulated_success_rate = len(success_results) / n_simulations
        
        if success_results:
            approval_years = [r["approval_year"] for r in success_results]
            japan_approval_years = [r["japan_approval_year"] for r in success_results]
            japan_delays = [r["japan_delay_years"] for r in success_results]
            
            summary = {
                "NCTId": trial["NCTId"],
                "BriefTitle": trial["BriefTitle"],
                "Phase": trial["Phase"],
                "SponsorName": trial["SponsorName"],
                "success_rate": cumulative_approval_probability,
                "phase_historical_success_rate": phase_historical_success_rate,
                "cumulative_approval_probability": cumulative_approval_probability,
                "simulated_success_rate": simulated_success_rate,
                "median_approval_year": np.median(approval_years),
                "mean_approval_year": np.mean(approval_years),
                "pct10_approval_year": np.percentile(approval_years, 10),
                "pct90_approval_year": np.percentile(approval_years, 90),
                "earliest_approval_year": np.min(approval_years),
                "latest_approval_year": np.max(approval_years),
                # 日本承認予測の統計
                "japan_median_approval_year": np.median(japan_approval_years),
                "japan_mean_approval_year": np.mean(japan_approval_years),
                "japan_pct10_approval_year": np.percentile(japan_approval_years, 10),
                "japan_pct90_approval_year": np.percentile(japan_approval_years, 90),
                "japan_earliest_approval_year": np.min(japan_approval_years),
                "japan_latest_approval_year": np.max(japan_approval_years),
                "japan_median_delay_years": np.median(japan_delays)
            }
            results.append(summary)
    
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values("median_approval_year")
    
    return results_df


def create_cdf_plot(results_df: pd.DataFrame, output_dir: Path):
    """累積分布関数（CDF）プロットを作成（FDA承認と日本承認の両方）"""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # 最も有望な5つのプログラムをハイライト
    top_programs = results_df.head(5)
    
    # 年のレンジを設定（設定ファイルから読み込み）
    sim_config = load_simulation_config()
    cdf_range = sim_config.get("cdf_year_range", {"start": 2025, "end": 2041})
    years = range(cdf_range["start"], cdf_range["end"])
    
    # FDA承認のCDF（左側）
    for _, program in top_programs.iterrows():
        # 簡略化のため、正規分布で近似
        mean = program["mean_approval_year"]
        std = (program["pct90_approval_year"] - program["pct10_approval_year"]) / 2.56
        
        cdf_values = []
        for year in years:
            # 正規分布のCDF
            if std > 0:
                z_score = (year - mean) / std
                # erfをscipyから使用
                from scipy.special import erf
                cdf = 0.5 * (1 + erf(z_score / np.sqrt(2)))
            else:
                # stdが0の場合（全て同じ年の場合）
                cdf = 1.0 if year >= mean else 0.0
            cdf_values.append(cdf * program.get("cumulative_approval_probability", program["success_rate"]))
        
        label = f"{program['NCTId']}: {program['BriefTitle'][:30]}..."
        ax1.plot(years, cdf_values, linewidth=2, label=label)
    
    ax1.set_xlabel("Year", fontsize=12)
    ax1.set_ylabel("Cumulative Probability of Approval", fontsize=12)
    ax1.set_title("FDA Approval Predictions\nTop 5 RP Treatment Programs", 
                  fontsize=14, pad=20)
    ax1.grid(True, alpha=0.3)
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # 日本承認のCDF（右側）
    for _, program in top_programs.iterrows():
        # 簡略化のため、正規分布で近似
        mean = program["japan_mean_approval_year"]
        std = (program["japan_pct90_approval_year"] - program["japan_pct10_approval_year"]) / 2.56
        
        cdf_values = []
        for year in years:
            # 正規分布のCDF
            if std > 0:
                z_score = (year - mean) / std
                # erfをscipyから使用
                from scipy.special import erf
                cdf = 0.5 * (1 + erf(z_score / np.sqrt(2)))
            else:
                # stdが0の場合（全て同じ年の場合）
                cdf = 1.0 if year >= mean else 0.0
            cdf_values.append(cdf * program.get("cumulative_approval_probability", program["success_rate"]))
        
        label = f"{program['NCTId']}: {program['BriefTitle'][:30]}..."
        ax2.plot(years, cdf_values, linewidth=2, label=label)
    
    ax2.set_xlabel("Year", fontsize=12)
    ax2.set_ylabel("Cumulative Probability of Approval", fontsize=12)
    ax2.set_title("Japan Approval Predictions\nTop 5 RP Treatment Programs", 
                  fontsize=14, pad=20)
    ax2.grid(True, alpha=0.3)
    ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    
    output_file = output_dir / "CDF.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info("CDF plot saved to: %s", output_file)


def run_sensitivity_analysis(active_trials: pd.DataFrame, 
                           base_parameters: dict,
                           n_simulations: int = 1000) -> pd.DataFrame:
    """感度分析：各パラメータを±20%変動させて影響を評価"""
    
    logger.info("Running sensitivity analysis...")
    
    # 分析対象のプログラム（最も有望な5つ）
    sample_trials = active_trials.head(5)
    
    # ベースケースの結果
    base_results = run_monte_carlo_simulation(sample_trials, base_parameters, n_simulations)
    base_median = base_results["median_approval_year"].mean()
    
    sensitivity_results = []
    
    # フェーズ期間の感度分析
    for phase in ["PHASE1", "PHASE2", "PHASE3"]:
        for direction, factor in [("decrease", 0.8), ("increase", 1.2)]:
            # パラメータをコピーして変更
            mod_params = yaml.safe_load(yaml.dump(base_parameters))
            
            if phase in mod_params["phase_durations_years"]:
                for key in ["min", "median", "max", "mean"]:
                    mod_params["phase_durations_years"][phase][key] *= factor
            
            # シミュレーション実行
            mod_results = run_monte_carlo_simulation(sample_trials, mod_params, n_simulations)
            mod_median = mod_results["median_approval_year"].mean()
            
            impact = mod_median - base_median
            
            sensitivity_results.append({
                "parameter": f"{phase} duration",
                "change": f"{direction} 20%",
                "base_value": base_median,
                "modified_value": mod_median,
                "impact_years": impact,
                "impact_percent": (impact / base_median) * 100
            })
    
    # 成功率の感度分析
    for phase in ["PHASE1", "PHASE2", "PHASE3"]:
        for direction, factor in [("decrease", 0.8), ("increase", 1.2)]:
            # パラメータをコピーして変更
            mod_params = yaml.safe_load(yaml.dump(base_parameters))
            
            if phase in mod_params["phase_success_rates"]:
                original_rate = mod_params["phase_success_rates"][phase]["success_rate"]
                mod_params["phase_success_rates"][phase]["success_rate"] = _cap_probability(
                    original_rate * factor, mod_params
                )
            
            # シミュレーション実行
            mod_results = run_monte_carlo_simulation(sample_trials, mod_params, n_simulations)
            mod_median = mod_results["median_approval_year"].mean()
            
            impact = mod_median - base_median
            
            sensitivity_results.append({
                "parameter": f"{phase} success rate",
                "change": f"{direction} 20%",
                "base_value": base_median,
                "modified_value": mod_median,
                "impact_years": impact,
                "impact_percent": (impact / base_median) * 100
            })
    
    # 規制期間の感度分析
    for param_type in ["BLA_MAA_submission", "regulatory_review"]:
        for direction, factor in [("decrease", 0.8), ("increase", 1.2)]:
            # パラメータをコピーして変更
            mod_params = yaml.safe_load(yaml.dump(base_parameters))
            
            for key in ["min", "median", "max", "mean"]:
                if key in mod_params["regulatory_timelines_years"][param_type]:
                    mod_params["regulatory_timelines_years"][param_type][key] *= factor
            
            # シミュレーション実行
            mod_results = run_monte_carlo_simulation(sample_trials, mod_params, n_simulations)
            mod_median = mod_results["median_approval_year"].mean()
            
            impact = mod_median - base_median
            
            sensitivity_results.append({
                "parameter": param_type.replace("_", " "),
                "change": f"{direction} 20%",
                "base_value": base_median,
                "modified_value": mod_median,
                "impact_years": impact,
                "impact_percent": (impact / base_median) * 100
            })
    
    # 結果をDataFrameに変換
    sensitivity_df = pd.DataFrame(sensitivity_results)
    sensitivity_df = sensitivity_df.sort_values("impact_years", key=abs, ascending=False)
    
    return sensitivity_df


def create_tornado_chart(sensitivity_df: pd.DataFrame, output_dir: Path):
    """トルネード図を作成"""
    
    # パラメータごとに最大の影響を集計
    param_impacts = {}
    
    for param in sensitivity_df["parameter"].unique():
        param_data = sensitivity_df[sensitivity_df["parameter"] == param]
        max_impact = param_data["impact_years"].abs().max()
        
        # 減少と増加の影響を取得
        decrease_impact = param_data[param_data["change"].str.contains("decrease")]["impact_years"].values
        increase_impact = param_data[param_data["change"].str.contains("increase")]["impact_years"].values
        
        if len(decrease_impact) > 0 and len(increase_impact) > 0:
            param_impacts[param] = {
                "decrease": decrease_impact[0],
                "increase": increase_impact[0],
                "max_abs": max_impact
            }
    
    # 最大影響でソート
    sorted_params = sorted(param_impacts.items(), key=lambda x: x[1]["max_abs"], reverse=True)
    
    # プロット作成
    fig, ax = plt.subplots(figsize=(10, 8))
    
    y_positions = range(len(sorted_params))
    
    for i, (param, impacts) in enumerate(sorted_params):
        # 減少の影響（左側）
        ax.barh(i, impacts["decrease"], color='#d62728', alpha=0.7, 
                label='20% decrease' if i == 0 else "")
        
        # 増加の影響（右側）
        ax.barh(i, impacts["increase"], color='#2ca02c', alpha=0.7,
                label='20% increase' if i == 0 else "")
    
    # ラベル設定
    ax.set_yticks(y_positions)
    ax.set_yticklabels([param for param, _ in sorted_params])
    ax.set_xlabel('Impact on Median Approval Year (years)', fontsize=12)
    ax.set_title('Sensitivity Analysis: Parameter Impact on Timeline\n(Change from Base Case)', 
                 fontsize=14, pad=20)
    
    # 中央線
    ax.axvline(x=0, color='black', linewidth=0.5)
    
    # グリッド
    ax.grid(True, axis='x', alpha=0.3)
    
    # 凡例
    ax.legend(loc='lower right')
    
    plt.tight_layout()
    
    output_file = output_dir / "tornado.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info("Tornado chart saved to: %s", output_file)


def create_waterfall_chart(results_df: pd.DataFrame, output_dir: Path,
                           base_year: int = 2025):
    """ウォーターフォールチャートを作成"""

    plt.figure(figsize=(14, 10))

    # 上位20プログラムまたは全プログラム
    n_programs = min(20, len(results_df))
    top_df = results_df.head(n_programs)

    # Y軸の位置
    y_positions = range(n_programs)

    # エラーバーの計算
    lower_errors = top_df["median_approval_year"] - top_df["pct10_approval_year"]
    upper_errors = top_df["pct90_approval_year"] - top_df["median_approval_year"]

    # バーチャート
    bars = plt.barh(y_positions,
                     top_df["median_approval_year"] - base_year,  # base_yearからの年数
                     left=base_year,  # 開始位置
                     xerr=[lower_errors, upper_errors],
                     capsize=5,
                     color='skyblue',
                     edgecolor='navy',
                     linewidth=1)
    
    # ラベル
    labels = []
    for _, row in top_df.iterrows():
        label = f"{row['NCTId']}: {row['BriefTitle'][:40]}..."
        labels.append(label)
    
    plt.yticks(y_positions, labels)
    plt.xlabel("Predicted Approval Year", fontsize=12)
    plt.title("Timeline Predictions for RP Treatment Programs\n(Median with 10th-90th Percentile Range)", 
              fontsize=14, pad=20)
    
    # 現在年を示す縦線
    plt.axvline(x=base_year, color='red', linestyle='--', alpha=0.5, label='Current Year')
    
    plt.grid(True, axis='x', alpha=0.3)
    plt.tight_layout()
    
    output_file = output_dir / "waterfall.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info("Waterfall chart saved to: %s", output_file)


def main():
    """メイン実行関数"""
    
    print("Loading data...")
    trials_df, parameters = load_data()
    
    # アクティブなプログラムを抽出
    active_trials = get_active_programs(trials_df)
    
    # シミュレーション実行
    logger.info("Running Monte Carlo simulation (%d iterations per program)...",
                parameters['simulation_parameters']['n_simulations'])
    results_df = run_monte_carlo_simulation(
        active_trials,
        parameters,
        n_simulations=parameters["simulation_parameters"]["n_simulations"]
    )

    # 結果を保存
    output_dir = Path("results")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "forecasts.csv"
    results_df.to_csv(output_file, index=False)
    logger.info("Results saved to: %s", output_file)

    # 可視化
    fig_dir = output_dir / "figs"
    fig_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Creating visualizations...")
    create_cdf_plot(results_df, fig_dir)
    sim_config = load_simulation_config()
    base_year = sim_config.get("waterfall_base_year", 2025)
    create_waterfall_chart(results_df, fig_dir, base_year=base_year)

    # 感度分析
    sensitivity_df = run_sensitivity_analysis(
        active_trials,
        parameters,
        n_simulations=1000  # 感度分析は計算時間短縮のため少なめ
    )

    # 感度分析結果を保存
    sensitivity_file = output_dir / "sensitivity_analysis.csv"
    sensitivity_df.to_csv(sensitivity_file, index=False)
    logger.info("Sensitivity analysis saved to: %s", sensitivity_file)

    # トルネード図を作成
    create_tornado_chart(sensitivity_df, fig_dir)

    # サマリー統計
    logger.info("=== SIMULATION SUMMARY ===")
    logger.info("Total programs simulated: %d", len(results_df))
    logger.info("Average success rate: %.1f%%", results_df['success_rate'].mean() * 100)
    logger.info("Top 5 programs by median approval year:")

    for idx, row in results_df.head(5).iterrows():
        logger.info("%s: %s...", row['NCTId'], row['BriefTitle'][:50])
        logger.info("  Phase: %s", row['Phase'])
        logger.info("  Sponsor: %s", row['SponsorName'])
        logger.info("  Success rate: %.1f%%", row['success_rate'] * 100)
        logger.info("  FDA Median approval: %.0f", row['median_approval_year'])
        logger.info("  FDA 90%% CI: [%.0f, %.0f]", row['pct10_approval_year'], row['pct90_approval_year'])
        logger.info("  Japan Median approval: %.0f (+%.1f years)",
                     row['japan_median_approval_year'], row['japan_median_delay_years'])
        logger.info("  Japan 90%% CI: [%.0f, %.0f]",
                     row['japan_pct10_approval_year'], row['japan_pct90_approval_year'])

    # 全体的な予測
    all_approval_years = []
    for _, row in results_df.iterrows():
        # 各プログラムの中央値を重み付き（累積承認確率）で集計
        weight = row['success_rate']
        all_approval_years.extend([row['median_approval_year']] * int(weight * 100))

    if all_approval_years:
        overall_median = np.median(all_approval_years)
        logger.info("Overall median year for first approval: %.0f", overall_median)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
