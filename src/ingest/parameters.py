#!/usr/bin/env python3
"""
臨床試験データから治験成功確率と期間パラメータを推定する。
眼科領域のAAV遺伝子治療試験を中心に分析。
"""

import pandas as pd
import numpy as np
from pathlib import Path
import yaml
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


def load_clinical_trials():
    """臨床試験データを読み込む"""
    data_file = Path("data/processed/clinical_trials.parquet")
    if not data_file.exists():
        raise FileNotFoundError(f"Data file not found: {data_file}")
    
    df = pd.read_parquet(data_file)
    print(f"Loaded {len(df)} clinical trials")
    return df


def calculate_phase_durations(df):
    """フェーズ間の期間を計算"""
    
    # 完了した試験のみを対象
    completed = df[df["Status"] == "COMPLETED"].copy()
    
    # 開始日と完了日が両方ある試験のみ
    completed = completed.dropna(subset=["StartDate", "CompletionDate"])
    
    # 期間を計算（年単位）
    completed["Duration"] = (completed["CompletionDate"] - completed["StartDate"]).dt.days / 365.25
    
    # フェーズ別の期間統計
    phase_durations = {}
    
    for phase in ["PHASE1", "PHASE2", "PHASE3", "PHASE1, PHASE2", "PHASE2, PHASE3"]:
        phase_data = completed[completed["Phase"].str.contains(phase, na=False)]
        
        if len(phase_data) >= 3:  # 最低3件以上のデータがある場合のみ
            durations = phase_data["Duration"].values
            durations = durations[durations > 0]  # 正の値のみ
            
            if len(durations) > 0:
                phase_durations[phase] = {
                    "min": float(np.min(durations)),
                    "median": float(np.median(durations)),
                    "max": float(np.max(durations)),
                    "mean": float(np.mean(durations)),
                    "std": float(np.std(durations)),
                    "count": int(len(durations))
                }
    
    # デフォルト値（データが不足している場合）
    default_durations = {
        "PHASE1": {"min": 1.0, "median": 2.0, "max": 3.0, "mean": 2.0, "std": 0.5, "count": 0},
        "PHASE2": {"min": 2.0, "median": 3.0, "max": 4.0, "mean": 3.0, "std": 0.5, "count": 0},
        "PHASE3": {"min": 3.0, "median": 4.0, "max": 5.0, "mean": 4.0, "std": 0.5, "count": 0},
        "PHASE1, PHASE2": {"min": 2.0, "median": 3.5, "max": 5.0, "mean": 3.5, "std": 0.75, "count": 0},
        "PHASE2, PHASE3": {"min": 3.0, "median": 4.5, "max": 6.0, "mean": 4.5, "std": 0.75, "count": 0}
    }
    
    # データが不足しているフェーズにはデフォルト値を使用
    for phase, defaults in default_durations.items():
        if phase not in phase_durations:
            phase_durations[phase] = defaults
            print(f"Using default values for {phase} (insufficient data)")
    
    return phase_durations


def calculate_success_rates(df):
    """フェーズ別の成功率を計算"""
    
    # 成功 = COMPLETED、失敗 = TERMINATED または WITHDRAWN
    success_status = ["COMPLETED"]
    failure_status = ["TERMINATED", "WITHDRAWN"]
    
    phase_success_rates = {}
    
    for phase in ["PHASE1", "PHASE2", "PHASE3"]:
        # 該当フェーズの試験を抽出
        phase_trials = df[df["Phase"].str.contains(phase, na=False)]
        
        # 完了または失敗した試験のみ（進行中は除外）
        finished_trials = phase_trials[
            phase_trials["Status"].isin(success_status + failure_status)
        ]
        
        if len(finished_trials) >= 5:  # 最低5件以上のデータがある場合
            success_count = len(finished_trials[finished_trials["Status"].isin(success_status)])
            total_count = len(finished_trials)
            success_rate = success_count / total_count
            
            phase_success_rates[phase] = {
                "success_rate": float(success_rate),
                "success_count": int(success_count),
                "total_count": int(total_count),
                "confidence": "measured"
            }
        else:
            # データ不足の場合は文献値を使用
            default_rates = {
                "PHASE1": 0.70,  # Phase 1は安全性評価なので比較的高い
                "PHASE2": 0.40,  # Phase 2で有効性の壁
                "PHASE3": 0.60   # Phase 3まで来たものは比較的成功率高い
            }
            phase_success_rates[phase] = {
                "success_rate": default_rates.get(phase, 0.5),
                "success_count": 0,
                "total_count": 0,
                "confidence": "literature"
            }
    
    return phase_success_rates


def calculate_regulatory_duration():
    """規制当局承認までの期間（文献値）"""
    return {
        "BLA_MAA_submission": {
            "min": 0.5,
            "median": 1.0,
            "max": 1.5,
            "mean": 1.0,
            "std": 0.25,
            "note": "Time from Phase 3 completion to regulatory submission"
        },
        "regulatory_review": {
            "min": 0.5,
            "median": 1.0,
            "max": 2.0,
            "mean": 1.0,
            "std": 0.5,
            "note": "FDA/EMA review period"
        }
    }


def estimate_parameters():
    """メイン関数：パラメータを推定してYAMLファイルに保存"""
    
    # データ読み込み
    df = load_clinical_trials()
    
    # フェーズ期間を計算
    print("\nCalculating phase durations...")
    phase_durations = calculate_phase_durations(df)
    
    # 成功率を計算
    print("\nCalculating success rates...")
    success_rates = calculate_success_rates(df)
    
    # 規制当局関連の期間
    regulatory = calculate_regulatory_duration()
    
    # 全パラメータをまとめる
    parameters = {
        "metadata": {
            "generated_date": datetime.now().isoformat(),
            "data_source": "ClinicalTrials.gov",
            "total_trials_analyzed": len(df),
            "note": "Parameters estimated from Retinitis Pigmentosa clinical trials"
        },
        "phase_durations_years": phase_durations,
        "phase_success_rates": success_rates,
        "regulatory_timelines_years": regulatory,
        "simulation_parameters": {
            "n_simulations": 10000,
            "random_seed": 42,
            "distribution_type": "triangular",
            "note": "Use triangular distribution with (min, mode=median, max)"
        }
    }
    
    # YAMLファイルに保存
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "parameters.yaml"
    
    with open(output_file, "w", encoding="utf-8") as f:
        yaml.dump(parameters, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"\nParameters saved to: {output_file}")
    
    # サマリー表示
    print("\n=== PARAMETER SUMMARY ===")
    print("\nPhase Durations (years):")
    for phase, stats in phase_durations.items():
        print(f"  {phase}: {stats['min']:.1f} - {stats['median']:.1f} - {stats['max']:.1f} (n={stats['count']})")
    
    print("\nPhase Success Rates:")
    for phase, stats in success_rates.items():
        print(f"  {phase}: {stats['success_rate']:.1%} ({stats['confidence']}, n={stats['total_count']})")
    
    return parameters


if __name__ == "__main__":
    parameters = estimate_parameters()