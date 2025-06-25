#!/usr/bin/env python3
"""
高度な統合シミュレーション
ベイズ推定、機械学習、従来のモンテカルロを組み合わせた予測
"""

import numpy as np
import pandas as pd
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from sim.timeline_sim import run_monte_carlo_simulation
from sim.bayesian_predictor import BayesianTrialPredictor
from sim.ml_predictor import MLTrialPredictor, ClinicalTrialFeatureExtractor
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple


class AdvancedTrialSimulator:
    """高度な統合シミュレーター"""
    
    def __init__(self):
        self.bayesian_predictor = BayesianTrialPredictor()
        self.ml_predictor = MLTrialPredictor()
        self.simulation_results = []
    
    def initialize_models(self, historical_data: pd.DataFrame):
        """
        過去データでモデルを初期化
        
        Args:
            historical_data: 過去の試験データ
        """
        # ベイズモデルの初期化
        print("ベイズモデルを初期化中...")
        bayesian_data = historical_data[['Phase', 'Status']].copy()
        bayesian_data['Success'] = bayesian_data['Status'] == 'COMPLETED'
        self.bayesian_predictor._initialize_priors(bayesian_data)
        
        # 機械学習モデルの訓練
        print("機械学習モデルを訓練中...")
        self.ml_predictor.train(historical_data)
    
    def run_integrated_simulation(self, active_trials: pd.DataFrame, 
                                parameters: Dict, n_simulations: int = 10000) -> pd.DataFrame:
        """
        統合シミュレーションを実行
        
        Args:
            active_trials: 現在進行中の試験
            parameters: シミュレーションパラメータ
            n_simulations: シミュレーション回数
            
        Returns:
            統合予測結果
        """
        results = []
        
        for idx, trial in active_trials.iterrows():
            print(f"\n処理中: {trial['BriefTitle'][:50]}...")
            
            # 1. 従来のモンテカルロシミュレーション
            print("  - モンテカルロシミュレーション実行中...")
            mc_result = self._run_single_monte_carlo(trial, parameters, n_simulations)
            
            # 2. ベイズ予測
            print("  - ベイズ予測実行中...")
            bayes_result = self.bayesian_predictor.predict_timeline_distribution(
                trial, parameters['phase_durations_years']
            )
            
            # 3. 機械学習予測
            print("  - 機械学習予測実行中...")
            ml_probs = self.ml_predictor.predict_success_probability(trial)
            ml_timeline = self.ml_predictor.predict_timeline_with_ml(
                trial, mc_result.get('median_year', 2035) - datetime.now().year
            )
            
            # 4. 結果の統合
            integrated_result = self._integrate_predictions(
                trial, mc_result, bayes_result, ml_probs, ml_timeline
            )
            
            results.append(integrated_result)
        
        return pd.DataFrame(results)
    
    def _run_single_monte_carlo(self, trial: pd.Series, parameters: Dict, 
                               n_simulations: int) -> Dict:
        """単一試験のモンテカルロシミュレーション"""
        # 簡易版実装（実際のtimeline_sim.pyの関数を使用）
        approval_years = []
        success_count = 0
        
        for _ in range(n_simulations):
            # フェーズごとの成功判定とタイムライン
            total_time = 0
            success = True
            
            phase = trial['Phase']
            phase_params = parameters['phase_durations_years'].get(phase, {})
            success_rate = parameters['phase_success_rates'].get(phase, {}).get('success_rate', 0.5)
            
            if np.random.random() < success_rate:
                duration = np.random.triangular(
                    phase_params.get('min', 2),
                    phase_params.get('median', 3),
                    phase_params.get('max', 5)
                )
                total_time += duration + np.random.triangular(1, 1.5, 2)  # 規制審査
                approval_years.append(datetime.now().year + total_time)
                success_count += 1
        
        if approval_years:
            return {
                'success_rate': success_count / n_simulations,
                'median_year': np.median(approval_years),
                'mean_year': np.mean(approval_years),
                'std_year': np.std(approval_years),
                'pct10_year': np.percentile(approval_years, 10),
                'pct90_year': np.percentile(approval_years, 90)
            }
        else:
            return {'success_rate': 0, 'median_year': None}
    
    def _integrate_predictions(self, trial: pd.Series, mc_result: Dict, 
                             bayes_result: Dict, ml_probs: Dict, 
                             ml_timeline: Dict) -> Dict:
        """
        異なる予測手法の結果を統合
        
        重み付け：
        - モンテカルロ: 30%（ベースライン）
        - ベイズ: 40%（動的更新可能）
        - 機械学習: 30%（特徴量考慮）
        """
        # 成功率の統合
        integrated_success_rate = (
            0.3 * mc_result.get('success_rate', 0) +
            0.4 * bayes_result.get('success_probability', 0) +
            0.3 * ml_probs.get('ensemble', 0)
        )
        
        # タイムラインの統合（成功した場合のみ）
        timelines = []
        weights = []
        
        if mc_result.get('median_year'):
            timelines.append(mc_result['median_year'])
            weights.append(0.3)
        
        if bayes_result.get('median_year'):
            timelines.append(bayes_result['median_year'])
            weights.append(0.4)
        
        if ml_timeline.get('ensemble'):
            ml_year = datetime.now().year + ml_timeline['ensemble']
            timelines.append(ml_year)
            weights.append(0.3)
        
        if timelines:
            # 重み付き平均
            weights = np.array(weights) / sum(weights)  # 正規化
            integrated_median_year = np.average(timelines, weights=weights)
            
            # 不確実性の統合（標準偏差の加重平均）
            stds = [
                mc_result.get('std_year', 2),
                bayes_result.get('std_year', 2),
                2  # ML予測の仮定標準偏差
            ]
            integrated_std = np.average(stds[:len(weights)], weights=weights)
        else:
            integrated_median_year = None
            integrated_std = None
        
        # リスク要因の追加
        risk_factors = self.ml_predictor.get_risk_factors(trial)
        
        return {
            'NCTId': trial.get('NCTId', 'Unknown'),
            'BriefTitle': trial['BriefTitle'],
            'Phase': trial['Phase'],
            'SponsorName': trial.get('SponsorName', 'Unknown'),
            # 統合予測
            'integrated_success_rate': integrated_success_rate,
            'integrated_median_year': integrated_median_year,
            'integrated_std_year': integrated_std,
            # 個別予測
            'mc_success_rate': mc_result.get('success_rate', 0),
            'bayes_success_rate': bayes_result.get('success_probability', 0),
            'ml_success_rate': ml_probs.get('ensemble', 0),
            # 追加情報
            'confidence_level': self._calculate_confidence_level(
                mc_result, bayes_result, ml_probs
            ),
            'risk_factors': ', '.join(risk_factors) if risk_factors else 'None identified',
            'prediction_variance': self._calculate_prediction_variance(
                [mc_result.get('median_year'), 
                 bayes_result.get('median_year'),
                 datetime.now().year + ml_timeline.get('ensemble', 0) if ml_timeline.get('ensemble') else None]
            )
        }
    
    def _calculate_confidence_level(self, mc_result: Dict, bayes_result: Dict, 
                                   ml_probs: Dict) -> str:
        """予測の信頼度を計算"""
        # 各手法の予測の一致度を評価
        success_rates = [
            mc_result.get('success_rate', 0),
            bayes_result.get('success_probability', 0),
            ml_probs.get('ensemble', 0)
        ]
        
        variance = np.var(success_rates)
        
        if variance < 0.01:
            return "High"
        elif variance < 0.05:
            return "Medium"
        else:
            return "Low"
    
    def _calculate_prediction_variance(self, predictions: List[float]) -> float:
        """予測値のばらつきを計算"""
        valid_predictions = [p for p in predictions if p is not None]
        if len(valid_predictions) > 1:
            return np.var(valid_predictions)
        return 0.0
    
    def generate_comparison_report(self, results: pd.DataFrame) -> Dict:
        """
        手法間の比較レポートを生成
        
        Returns:
            比較統計の辞書
        """
        comparison = {
            'method_correlations': {},
            'average_differences': {},
            'confidence_distribution': results['confidence_level'].value_counts().to_dict()
        }
        
        # 手法間の相関
        if len(results) > 3:
            comparison['method_correlations'] = {
                'mc_vs_bayes': results[['mc_success_rate', 'bayes_success_rate']].corr().iloc[0, 1],
                'mc_vs_ml': results[['mc_success_rate', 'ml_success_rate']].corr().iloc[0, 1],
                'bayes_vs_ml': results[['bayes_success_rate', 'ml_success_rate']].corr().iloc[0, 1]
            }
        
        # 平均的な差異
        comparison['average_differences'] = {
            'mc_vs_integrated': (results['mc_success_rate'] - results['integrated_success_rate']).mean(),
            'bayes_vs_integrated': (results['bayes_success_rate'] - results['integrated_success_rate']).mean(),
            'ml_vs_integrated': (results['ml_success_rate'] - results['integrated_success_rate']).mean()
        }
        
        return comparison
    
    def visualize_predictions(self, results: pd.DataFrame, output_dir: Path):
        """予測結果の可視化"""
        output_dir.mkdir(exist_ok=True)
        
        # 1. 手法比較散布図
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        methods = [('mc_success_rate', 'bayes_success_rate'),
                  ('mc_success_rate', 'ml_success_rate'),
                  ('bayes_success_rate', 'ml_success_rate')]
        
        for ax, (x, y) in zip(axes, methods):
            ax.scatter(results[x], results[y], alpha=0.6)
            ax.plot([0, 1], [0, 1], 'r--', alpha=0.5)
            ax.set_xlabel(x.replace('_success_rate', '').upper())
            ax.set_ylabel(y.replace('_success_rate', '').upper())
            ax.set_title(f'{x.split("_")[0].upper()} vs {y.split("_")[0].upper()}')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'method_comparison.png', dpi=300)
        plt.close()
        
        # 2. 統合予測の分布
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # 成功した試験のみ
        success_trials = results[results['integrated_median_year'].notna()]
        
        ax.hist(success_trials['integrated_median_year'], bins=20, alpha=0.7, 
                label='Integrated Prediction')
        ax.axvline(success_trials['integrated_median_year'].median(), 
                  color='red', linestyle='--', 
                  label=f'Median: {success_trials["integrated_median_year"].median():.0f}')
        
        ax.set_xlabel('Predicted Approval Year')
        ax.set_ylabel('Number of Trials')
        ax.set_title('Distribution of Integrated Approval Predictions')
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(output_dir / 'integrated_timeline_distribution.png', dpi=300)
        plt.close()
        
        print(f"可視化を保存しました: {output_dir}")


def demo_advanced_simulation():
    """高度なシミュレーションのデモ"""
    
    # 仮想データの生成
    np.random.seed(42)
    
    # 過去の試験データ（訓練用）
    historical_trials = pd.DataFrame({
        'NCTId': [f'NCT{i:08d}' for i in range(100)],
        'BriefTitle': [
            f"{'Gene therapy' if np.random.random() > 0.5 else 'Small molecule'} for "
            f"{np.random.choice(['RPGR', 'USH2A', 'PDE6B'], p=[0.4, 0.3, 0.3])} "
            f"in retinitis pigmentosa"
            for _ in range(100)
        ],
        'Phase': np.random.choice(['PHASE1', 'PHASE2', 'PHASE3'], 100, p=[0.3, 0.4, 0.3]),
        'SponsorName': np.random.choice(
            ['Janssen', 'Novartis', 'Small Biotech'], 100, p=[0.3, 0.3, 0.4]
        ),
        'Status': np.random.choice(['COMPLETED', 'TERMINATED'], 100, p=[0.7, 0.3]),
        'StartDate': pd.date_range('2015-01-01', '2020-01-01', periods=100)
    })
    
    # 現在の試験データ（予測対象）
    active_trials = pd.DataFrame({
        'NCTId': ['NCT99999901', 'NCT99999902', 'NCT99999903'],
        'BriefTitle': [
            'Gene therapy AAV-RPGR for X-linked retinitis pigmentosa',
            'Small molecule PDE6B inhibitor for retinitis pigmentosa',
            'Cell therapy for USH2A-related retinitis pigmentosa'
        ],
        'Phase': ['PHASE3', 'PHASE2', 'PHASE1'],
        'SponsorName': ['Janssen', 'Novartis', 'University'],
        'StartDate': pd.to_datetime(['2021-01-01', '2022-06-01', '2023-01-01'])
    })
    
    # パラメータ
    parameters = {
        'phase_durations_years': {
            'PHASE1': {'min': 1, 'median': 2, 'max': 3},
            'PHASE2': {'min': 2, 'median': 3, 'max': 4},
            'PHASE3': {'min': 4, 'median': 5.5, 'max': 7}
        },
        'phase_success_rates': {
            'PHASE1': {'success_rate': 0.862},
            'PHASE2': {'success_rate': 0.784},
            'PHASE3': {'success_rate': 0.714}
        }
    }
    
    # シミュレーターの初期化と実行
    simulator = AdvancedTrialSimulator()
    simulator.initialize_models(historical_trials)
    
    print("\n統合シミュレーションを実行中...")
    results = simulator.run_integrated_simulation(active_trials, parameters, n_simulations=1000)
    
    # 結果の表示
    print("\n\n=== 統合予測結果 ===")
    for _, trial in results.iterrows():
        print(f"\n試験: {trial['BriefTitle']}")
        print(f"統合成功率: {trial['integrated_success_rate']:.1%}")
        if trial['integrated_median_year']:
            print(f"承認予測年: {trial['integrated_median_year']:.0f} ± {trial['integrated_std_year']:.1f}")
        print(f"予測信頼度: {trial['confidence_level']}")
        print(f"リスク要因: {trial['risk_factors']}")
        print(f"手法別成功率 - MC: {trial['mc_success_rate']:.1%}, "
              f"Bayes: {trial['bayes_success_rate']:.1%}, "
              f"ML: {trial['ml_success_rate']:.1%}")
    
    # 比較レポート
    comparison = simulator.generate_comparison_report(results)
    print("\n\n=== 手法間比較 ===")
    print("相関係数:")
    for pair, corr in comparison['method_correlations'].items():
        print(f"  {pair}: {corr:.3f}")
    
    # 可視化
    output_dir = Path("results/advanced_simulation")
    simulator.visualize_predictions(results, output_dir)
    
    # 結果の保存
    results.to_csv(output_dir / "integrated_predictions.csv", index=False)
    print(f"\n結果を保存しました: {output_dir / 'integrated_predictions.csv'}")


if __name__ == "__main__":
    demo_advanced_simulation()