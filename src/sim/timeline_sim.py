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


def load_data():
    """必要なデータを読み込む"""
    # 臨床試験データ
    trials_df = pd.read_parquet("data/processed/clinical_trials.parquet")
    
    # パラメータ
    with open("data/processed/parameters.yaml", "r") as f:
        parameters = yaml.safe_load(f)
    
    return trials_df, parameters


def get_active_programs(df):
    """アクティブなRP治療プログラムを抽出"""
    active_status = ["RECRUITING", "ACTIVE_NOT_RECRUITING", "NOT_YET_RECRUITING", 
                     "ENROLLING_BY_INVITATION"]
    
    active_trials = df[df["Status"].isin(active_status)].copy()
    
    # 開始日がない場合は現在日付を仮定
    active_trials["StartDate"] = active_trials["StartDate"].fillna(pd.Timestamp.now())
    
    print(f"Found {len(active_trials)} active trials")
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
    success_params = parameters["phase_success_rates"].get(phase, {})
    success_rate = success_params.get("success_rate", 0.5)
    
    # 遺伝子治療の場合、成功率を少し下げる（新規性が高いため）
    if is_gene_therapy and phase == "PHASE3":
        success_rate *= 0.9  # 10%減
    
    return np.random.random() < success_rate


def simulate_single_program(trial: pd.Series, parameters: dict, 
                          current_date: datetime) -> Dict:
    """単一プログラムの承認までのタイムラインをシミュレート"""
    
    # 現在のフェーズを判定
    phase = trial["Phase"]
    start_date = trial["StartDate"]
    
    # 経過時間を考慮
    time_in_current_phase = (current_date - start_date).days / 365.25
    time_in_current_phase = max(0, time_in_current_phase)
    
    # MCO-010の特別処理（2025年Q1にBLA申請予定）
    if "MCO-010" in trial.get("BriefTitle", "") or "MCO010" in trial.get("BriefTitle", "") or \
       ("Nanoscope" in trial.get("SponsorName", "") and phase == "PHASE3"):
        # 2025年第1四半期の申請を反映
        submission_date = datetime(2025, 3, 1)  # 2025年3月と仮定
        time_to_submission = (submission_date - current_date).days / 365.25
        
        if time_to_submission > 0:
            # Fast Track指定により短縮された審査期間（6-12ヶ月）
            review_time = np.random.triangular(0.5, 0.75, 1.0)
            total_time = time_to_submission + review_time
            
            approval_date = current_date + timedelta(days=total_time * 365.25)
            return {
                "success": True,
                "approval_date": approval_date,
                "approval_year": approval_date.year,
                "time_to_approval": total_time,
                "fast_track": True,
                "program_name": "MCO-010",
                "confidence": "high"  # RESTORE試験で統計的有意性達成
            }
    
    # OCU400の特別処理（2024年6月Phase 3初回投与、2026年BLA申請予定）
    if "OCU400" in trial.get("BriefTitle", "") or "OCU-400" in trial.get("BriefTitle", "") or \
       ("Ocugen" in trial.get("SponsorName", "") and phase == "PHASE3"):
        # Phase 3は2024年6月開始（初回投与）
        phase3_start = datetime(2024, 6, 1)
        phase3_duration = 1.5  # 主要評価期間
        
        # データ解析と申請準備（3-6ヶ月）
        analysis_time = np.random.triangular(0.25, 0.375, 0.5)
        
        # FDA審査（12-18ヶ月）- RMAT指定による迅速審査
        review_time = np.random.triangular(1.0, 1.25, 1.5)
        
        total_time = ((phase3_start - current_date).days / 365.25) + phase3_duration + analysis_time + review_time
        
        if total_time > 0:
            approval_date = current_date + timedelta(days=total_time * 365.25)
            return {
                "success": True,
                "approval_date": approval_date,
                "approval_year": approval_date.year,
                "time_to_approval": total_time,
                "program_name": "OCU400",
                "confidence": "high"  # 2年データで100%改善/維持
            }
    
    # Janssen社の遺伝子治療の特別処理（Phase 3で主要評価項目未達成）
    if "NCT04794101" in trial.get("NCTId", "") or \
       ("Janssen" in trial.get("SponsorName", "") and "RPGR" in trial.get("BriefTitle", "")):
        # Phase 3失敗により成功率を大幅に下げる
        if np.random.random() < 0.2:  # 20%の成功率
            # 追加試験や規制当局との協議により時間がかかる
            additional_time = np.random.triangular(2.0, 3.0, 4.0)
            phase_duration = simulate_phase_duration("PHASE3", parameters)
            total_time = time_in_current_phase + phase_duration + additional_time
            
            # 規制当局承認プロセス
            submission_time = np.random.triangular(1.0, 1.5, 2.0)
            review_time = np.random.triangular(1.5, 2.0, 2.5)
            total_time += submission_time + review_time
            
            approval_date = current_date + timedelta(days=total_time * 365.25)
            return {
                "success": True,
                "approval_date": approval_date,
                "approval_year": approval_date.year,
                "time_to_approval": total_time,
                "program_name": "Botaretigene sparoparvovec",
                "confidence": "low"  # Phase 3で主要評価項目未達成
            }
        else:
            return {
                "success": False,
                "failed_at_phase": "PHASE3",
                "time_to_failure": time_in_current_phase + 1.0,
                "reason": "Phase 3 primary endpoint not met"
            }
    
    # フェーズ進行をシミュレート
    total_time = 0
    current_phase_map = {
        "PHASE1": ["PHASE1", "PHASE2", "PHASE3"],
        "PHASE2": ["PHASE2", "PHASE3"],
        "PHASE3": ["PHASE3"],
        "PHASE1, PHASE2": ["PHASE1, PHASE2", "PHASE3"],
        "PHASE2, PHASE3": ["PHASE2, PHASE3"]
    }
    
    # 現在のフェーズに基づいて残りのフェーズを決定
    remaining_phases = []
    for p in phase.split(", "):
        if p in current_phase_map:
            remaining_phases = current_phase_map[p]
            break
    
    if not remaining_phases:
        remaining_phases = ["PHASE1", "PHASE2", "PHASE3"]  # デフォルト
    
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
        
        # 成功判定（遺伝子治療かどうかを判定）
        is_gene_therapy = "gene" in trial.get("BriefTitle", "").lower() or "AAV" in trial.get("BriefTitle", "")
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
    
    return {
        "success": True,
        "time_to_approval": total_time,
        "approval_date": approval_date,
        "approval_year": approval_date.year
    }


def run_monte_carlo_simulation(active_trials: pd.DataFrame, 
                             parameters: dict,
                             n_simulations: int = 10000) -> pd.DataFrame:
    """全プログラムに対してモンテカルロシミュレーションを実行"""
    
    current_date = datetime.now()
    np.random.seed(parameters["simulation_parameters"]["random_seed"])
    
    results = []
    
    for idx, trial in active_trials.iterrows():
        program_results = []
        
        print(f"Simulating {trial['NCTId']}: {trial['BriefTitle'][:50]}...")
        
        for sim in range(n_simulations):
            result = simulate_single_program(trial, parameters, current_date)
            result["NCTId"] = trial["NCTId"]
            result["BriefTitle"] = trial["BriefTitle"]
            result["Phase"] = trial["Phase"]
            result["SponsorName"] = trial["SponsorName"]
            result["simulation"] = sim
            program_results.append(result)
        
        # 成功したシミュレーションのみで統計を計算
        success_results = [r for r in program_results if r["success"]]
        
        if success_results:
            approval_years = [r["approval_year"] for r in success_results]
            
            summary = {
                "NCTId": trial["NCTId"],
                "BriefTitle": trial["BriefTitle"],
                "Phase": trial["Phase"],
                "SponsorName": trial["SponsorName"],
                "success_rate": len(success_results) / n_simulations,
                "median_approval_year": np.median(approval_years),
                "mean_approval_year": np.mean(approval_years),
                "pct10_approval_year": np.percentile(approval_years, 10),
                "pct90_approval_year": np.percentile(approval_years, 90),
                "earliest_approval_year": np.min(approval_years),
                "latest_approval_year": np.max(approval_years)
            }
            results.append(summary)
    
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values("median_approval_year")
    
    return results_df


def create_cdf_plot(results_df: pd.DataFrame, output_dir: Path):
    """累積分布関数（CDF）プロットを作成"""
    
    plt.figure(figsize=(12, 8))
    
    # 最も有望な5つのプログラムをハイライト
    top_programs = results_df.head(5)
    
    # 年のレンジを設定
    years = range(2025, 2041)
    
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
            cdf_values.append(cdf)
        
        label = f"{program['NCTId']}: {program['BriefTitle'][:30]}..."
        plt.plot(years, cdf_values, linewidth=2, label=label)
    
    plt.xlabel("Year", fontsize=12)
    plt.ylabel("Cumulative Probability of Approval", fontsize=12)
    plt.title("Cumulative Distribution of Predicted Approval Times\nTop 5 RP Treatment Programs", 
              fontsize=14, pad=20)
    plt.grid(True, alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    output_file = output_dir / "CDF.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"CDF plot saved to: {output_file}")


def run_sensitivity_analysis(active_trials: pd.DataFrame, 
                           base_parameters: dict,
                           n_simulations: int = 1000) -> pd.DataFrame:
    """感度分析：各パラメータを±20%変動させて影響を評価"""
    
    print("\nRunning sensitivity analysis...")
    
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
                # 成功率は0-1の範囲に制限
                mod_params["phase_success_rates"][phase]["success_rate"] = min(1.0, max(0.0, original_rate * factor))
            
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
    
    print(f"Tornado chart saved to: {output_file}")


def create_waterfall_chart(results_df: pd.DataFrame, output_dir: Path):
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
                     top_df["median_approval_year"] - 2025,  # 2025年からの年数
                     left=2025,  # 開始位置
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
    plt.axvline(x=2025, color='red', linestyle='--', alpha=0.5, label='Current Year')
    
    plt.grid(True, axis='x', alpha=0.3)
    plt.tight_layout()
    
    output_file = output_dir / "waterfall.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Waterfall chart saved to: {output_file}")


def main():
    """メイン実行関数"""
    
    print("Loading data...")
    trials_df, parameters = load_data()
    
    # アクティブなプログラムを抽出
    active_trials = get_active_programs(trials_df)
    
    # シミュレーション実行
    print(f"\nRunning Monte Carlo simulation ({parameters['simulation_parameters']['n_simulations']} iterations per program)...")
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
    print(f"\nResults saved to: {output_file}")
    
    # 可視化
    fig_dir = output_dir / "figs"
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    print("\nCreating visualizations...")
    create_cdf_plot(results_df, fig_dir)
    create_waterfall_chart(results_df, fig_dir)
    
    # 感度分析
    sensitivity_df = run_sensitivity_analysis(
        active_trials,
        parameters,
        n_simulations=1000  # 感度分析は計算時間短縮のため少なめ
    )
    
    # 感度分析結果を保存
    sensitivity_file = output_dir / "sensitivity_analysis.csv"
    sensitivity_df.to_csv(sensitivity_file, index=False)
    print(f"\nSensitivity analysis saved to: {sensitivity_file}")
    
    # トルネード図を作成
    create_tornado_chart(sensitivity_df, fig_dir)
    
    # サマリー統計
    print("\n=== SIMULATION SUMMARY ===")
    print(f"Total programs simulated: {len(results_df)}")
    print(f"Average success rate: {results_df['success_rate'].mean():.1%}")
    print(f"\nTop 5 programs by median approval year:")
    
    for idx, row in results_df.head(5).iterrows():
        print(f"\n{row['NCTId']}: {row['BriefTitle'][:50]}...")
        print(f"  Phase: {row['Phase']}")
        print(f"  Sponsor: {row['SponsorName']}")
        print(f"  Success rate: {row['success_rate']:.1%}")
        print(f"  Median approval: {row['median_approval_year']:.0f}")
        print(f"  90% CI: [{row['pct10_approval_year']:.0f}, {row['pct90_approval_year']:.0f}]")
    
    # 全体的な予測
    all_approval_years = []
    for _, row in results_df.iterrows():
        # 各プログラムの中央値を重み付き（成功率）で集計
        weight = row['success_rate']
        all_approval_years.extend([row['median_approval_year']] * int(weight * 100))
    
    if all_approval_years:
        overall_median = np.median(all_approval_years)
        print(f"\n\nOverall median year for first approval: {overall_median:.0f}")


if __name__ == "__main__":
    main()