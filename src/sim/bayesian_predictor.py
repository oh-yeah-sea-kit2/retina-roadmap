#!/usr/bin/env python3
"""
ベイズ推定による動的予測モデル
過去のデータから事前分布を設定し、新しい試験結果で更新
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Tuple, List
import json
from datetime import datetime
from pathlib import Path


class BayesianTrialPredictor:
    """ベイズ推定による臨床試験成功率予測"""
    
    def __init__(self, prior_data: pd.DataFrame = None):
        """
        初期化
        
        Args:
            prior_data: 過去の試験データ（成功/失敗の記録）
        """
        self.priors = {}
        self.posteriors = {}
        self.update_history = []
        
        if prior_data is not None:
            self._initialize_priors(prior_data)
    
    def _initialize_priors(self, data: pd.DataFrame):
        """過去データから事前分布を初期化"""
        
        # フェーズ別の事前分布を計算
        for phase in ['PHASE1', 'PHASE2', 'PHASE3']:
            phase_data = data[data['Phase'] == phase]
            if len(phase_data) > 0:
                successes = len(phase_data[phase_data['Success'] == True])
                failures = len(phase_data[phase_data['Success'] == False])
                
                # Beta分布のパラメータ（+1はJeffreys事前分布）
                alpha = successes + 0.5
                beta = failures + 0.5
                
                self.priors[phase] = {
                    'alpha': alpha,
                    'beta': beta,
                    'success_rate': alpha / (alpha + beta),
                    'n_trials': len(phase_data)
                }
                
                # 初期状態では事前分布が事後分布
                self.posteriors[phase] = self.priors[phase].copy()
    
    def update(self, phase: str, success: bool, trial_info: Dict = None):
        """
        新しい試験結果で事後分布を更新
        
        Args:
            phase: 試験フェーズ
            success: 成功/失敗
            trial_info: 追加の試験情報（オプション）
        """
        if phase not in self.posteriors:
            # 事前分布がない場合は無情報事前分布を使用
            self.posteriors[phase] = {'alpha': 0.5, 'beta': 0.5}
        
        # ベイズ更新
        if success:
            self.posteriors[phase]['alpha'] += 1
        else:
            self.posteriors[phase]['beta'] += 1
        
        # 成功率を再計算
        alpha = self.posteriors[phase]['alpha']
        beta = self.posteriors[phase]['beta']
        self.posteriors[phase]['success_rate'] = alpha / (alpha + beta)
        
        # 更新履歴を記録
        self.update_history.append({
            'timestamp': datetime.now(),
            'phase': phase,
            'success': success,
            'trial_info': trial_info,
            'new_success_rate': self.posteriors[phase]['success_rate']
        })
    
    def predict_success_probability(self, phase: str) -> float:
        """
        指定フェーズの成功確率を予測
        
        Returns:
            成功確率（0-1）
        """
        if phase not in self.posteriors:
            return 0.5  # 無情報の場合
        
        return self.posteriors[phase]['success_rate']
    
    def get_confidence_interval(self, phase: str, confidence: float = 0.95) -> Tuple[float, float]:
        """
        成功率の信頼区間を計算
        
        Args:
            phase: 試験フェーズ
            confidence: 信頼水準（デフォルト95%）
            
        Returns:
            (下限, 上限)のタプル
        """
        if phase not in self.posteriors:
            return (0.0, 1.0)  # 無情報の場合
        
        alpha = self.posteriors[phase]['alpha']
        beta = self.posteriors[phase]['beta']
        
        return stats.beta.interval(confidence, alpha, beta)
    
    def predict_timeline_distribution(self, trial: pd.Series, phase_durations: Dict) -> Dict:
        """
        試験の承認時期の確率分布を予測
        
        Args:
            trial: 試験情報
            phase_durations: フェーズ期間の分布パラメータ
            
        Returns:
            予測結果の辞書
        """
        current_phase = trial['Phase']
        current_date = datetime.now()
        
        # 残りのフェーズを特定
        phase_sequence = {
            'PHASE1': ['PHASE1', 'PHASE2', 'PHASE3'],
            'PHASE2': ['PHASE2', 'PHASE3'],
            'PHASE3': ['PHASE3']
        }
        remaining_phases = phase_sequence.get(current_phase, ['PHASE1', 'PHASE2', 'PHASE3'])
        
        # モンテカルロシミュレーション（ベイズ推定を組み込み）
        n_simulations = 10000
        approval_years = []
        
        for _ in range(n_simulations):
            total_time = 0
            success = True
            
            for phase in remaining_phases:
                # 成功確率をBeta分布からサンプリング
                if phase in self.posteriors:
                    alpha = self.posteriors[phase]['alpha']
                    beta_param = self.posteriors[phase]['beta']
                    success_prob = np.random.beta(alpha, beta_param)
                else:
                    success_prob = 0.5
                
                # 成功判定
                if np.random.random() > success_prob:
                    success = False
                    break
                
                # フェーズ期間をサンプリング
                phase_params = phase_durations.get(phase, {'min': 2, 'median': 3, 'max': 5})
                duration = np.random.triangular(
                    phase_params['min'],
                    phase_params['median'],
                    phase_params['max']
                )
                total_time += duration
            
            if success:
                # 規制審査期間を追加
                regulatory_time = np.random.triangular(1, 1.5, 2.5)
                total_time += regulatory_time
                
                approval_year = current_date.year + total_time
                approval_years.append(approval_year)
        
        if approval_years:
            return {
                'success_probability': len(approval_years) / n_simulations,
                'median_year': np.median(approval_years),
                'mean_year': np.mean(approval_years),
                'std_year': np.std(approval_years),
                'percentile_10': np.percentile(approval_years, 10),
                'percentile_90': np.percentile(approval_years, 90),
                'confidence_interval': self.get_confidence_interval(current_phase)
            }
        else:
            return {
                'success_probability': 0.0,
                'median_year': None,
                'mean_year': None,
                'std_year': None,
                'percentile_10': None,
                'percentile_90': None,
                'confidence_interval': (0.0, 0.0)
            }
    
    def get_phase_comparison(self) -> pd.DataFrame:
        """フェーズ間の成功率比較を取得"""
        
        comparison_data = []
        for phase in ['PHASE1', 'PHASE2', 'PHASE3']:
            if phase in self.posteriors:
                post = self.posteriors[phase]
                prior = self.priors.get(phase, {'success_rate': 0.5})
                ci_low, ci_high = self.get_confidence_interval(phase)
                
                comparison_data.append({
                    'Phase': phase,
                    'Prior_Success_Rate': prior['success_rate'],
                    'Posterior_Success_Rate': post['success_rate'],
                    'CI_Lower': ci_low,
                    'CI_Upper': ci_high,
                    'N_Updates': int(post['alpha'] + post['beta'] - prior.get('alpha', 0.5) - prior.get('beta', 0.5))
                })
        
        return pd.DataFrame(comparison_data)
    
    def save_state(self, filepath: str):
        """モデルの状態を保存"""
        state = {
            'priors': self.priors,
            'posteriors': self.posteriors,
            'update_history': [
                {
                    'timestamp': h['timestamp'].isoformat(),
                    'phase': h['phase'],
                    'success': h['success'],
                    'trial_info': h['trial_info'],
                    'new_success_rate': h['new_success_rate']
                }
                for h in self.update_history
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self, filepath: str):
        """モデルの状態を読み込み"""
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        self.priors = state['priors']
        self.posteriors = state['posteriors']
        self.update_history = [
            {
                'timestamp': datetime.fromisoformat(h['timestamp']),
                'phase': h['phase'],
                'success': h['success'],
                'trial_info': h['trial_info'],
                'new_success_rate': h['new_success_rate']
            }
            for h in state['update_history']
        ]


def demo_bayesian_prediction():
    """ベイズ予測のデモンストレーション"""
    
    # 仮想的な過去データ
    historical_data = pd.DataFrame({
        'Phase': ['PHASE1'] * 29 + ['PHASE2'] * 37 + ['PHASE3'] * 14,
        'Success': [True] * 25 + [False] * 4 +  # Phase 1: 25/29
                   [True] * 29 + [False] * 8 +  # Phase 2: 29/37
                   [True] * 10 + [False] * 4    # Phase 3: 10/14
    })
    
    # モデルを初期化
    predictor = BayesianTrialPredictor(historical_data)
    
    print("初期状態（事前分布）:")
    print(predictor.get_phase_comparison())
    print()
    
    # 新しい試験結果で更新
    print("新しい試験結果で更新:")
    predictor.update('PHASE3', success=True, trial_info={'name': 'BIIB111'})
    predictor.update('PHASE3', success=True, trial_info={'name': 'Janssen RPGR'})
    predictor.update('PHASE2', success=False, trial_info={'name': 'Failed Trial X'})
    
    print("\n更新後（事後分布）:")
    print(predictor.get_phase_comparison())
    
    # 特定の試験の予測
    test_trial = pd.Series({
        'Phase': 'PHASE3',
        'Name': 'Test Gene Therapy'
    })
    
    phase_durations = {
        'PHASE1': {'min': 1, 'median': 2, 'max': 3},
        'PHASE2': {'min': 2, 'median': 3, 'max': 4},
        'PHASE3': {'min': 4, 'median': 5.5, 'max': 7}
    }
    
    prediction = predictor.predict_timeline_distribution(test_trial, phase_durations)
    
    print(f"\nPhase 3試験の予測:")
    print(f"成功確率: {prediction['success_probability']:.1%}")
    if prediction['median_year']:
        print(f"承認予測年（中央値）: {prediction['median_year']:.0f}")
        print(f"90%予測区間: {prediction['percentile_10']:.0f} - {prediction['percentile_90']:.0f}")


if __name__ == "__main__":
    demo_bayesian_prediction()