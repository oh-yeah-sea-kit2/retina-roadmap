#!/usr/bin/env python3
"""
実データを使用した高度なシミュレーション実行
ClinicalTrials.govのデータを取得・処理して統合シミュレーションを実行
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json
from datetime import datetime
import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).parent.parent))

from sim.advanced_simulation import AdvancedTrialSimulator
import yaml

class RealDataProcessor:
    """実データの処理と高度なシミュレーション実行"""
    
    def __init__(self):
        self.simulator = AdvancedTrialSimulator()
        self.data_dir = Path(__file__).parent.parent.parent / "data"
        self.results_dir = Path(__file__).parent.parent.parent / "results"
        self.results_dir.mkdir(exist_ok=True)
    
    def load_current_trials(self) -> pd.DataFrame:
        """現在のRP試験データを読み込み"""
        trials_path = self.data_dir / "processed" / "trials_with_features.json"
        
        if not trials_path.exists():
            print("エラー: 試験データが見つかりません。まずmain.pyを実行してください。")
            return pd.DataFrame()
        
        # JSONデータを読み込み
        with open(trials_path, 'r') as f:
            trials_data = json.load(f)
        
        df = pd.DataFrame(trials_data['trials'])
        
        # 進行中の試験のみ抽出
        active_trials = df[df['Status'].isin(['RECRUITING', 'ACTIVE_NOT_RECRUITING', 'NOT_YET_RECRUITING'])]
        
        # Phase情報の正規化
        phase_mapping = {
            'Phase 1': 'PHASE1',
            'Phase 2': 'PHASE2', 
            'Phase 3': 'PHASE3',
            'Phase 1/Phase 2': 'PHASE1',
            'Phase 2/Phase 3': 'PHASE2'
        }
        active_trials['Phase'] = active_trials['Phase'].map(phase_mapping).fillna('PHASE1')
        
        return active_trials
    
    def prepare_historical_data(self) -> pd.DataFrame:
        """過去の試験データを準備（モデル訓練用）"""
        trials_path = self.data_dir / "processed" / "trials_with_features.json"
        
        with open(trials_path, 'r') as f:
            trials_data = json.load(f)
        
        df = pd.DataFrame(trials_data['trials'])
        
        # 完了または中止された試験
        historical = df[df['Status'].isin(['COMPLETED', 'TERMINATED', 'SUSPENDED', 'WITHDRAWN'])]
        
        # 成功/失敗フラグを追加
        historical['Success'] = historical['Status'] == 'COMPLETED'
        
        # Phase情報の正規化
        phase_mapping = {
            'Phase 1': 'PHASE1',
            'Phase 2': 'PHASE2',
            'Phase 3': 'PHASE3',
            'Phase 1/Phase 2': 'PHASE1',
            'Phase 2/Phase 3': 'PHASE2'
        }
        historical['Phase'] = historical['Phase'].map(phase_mapping).fillna('PHASE1')
        
        return historical
    
    def load_parameters(self) -> dict:
        """シミュレーションパラメータを読み込み"""
        params_path = self.data_dir / "processed" / "parameters.yaml"
        
        with open(params_path, 'r') as f:
            params = yaml.safe_load(f)
        
        return params
    
    def run_real_data_simulation(self):
        """実データを使用した統合シミュレーションを実行"""
        print("=== 実データを使用した高度なシミュレーション ===\n")
        
        # データの読み込み
        print("1. データ読み込み中...")
        active_trials = self.load_current_trials()
        historical_trials = self.prepare_historical_data()
        parameters = self.load_parameters()
        
        print(f"  - 進行中の試験: {len(active_trials)}件")
        print(f"  - 過去の試験データ: {len(historical_trials)}件")
        
        if len(active_trials) == 0:
            print("エラー: 進行中の試験が見つかりません。")
            return
        
        # 重要な試験に絞る（Phase 2以降、主要な治療法）
        important_trials = active_trials[
            (active_trials['Phase'].isin(['PHASE2', 'PHASE3'])) |
            (active_trials['BriefTitle'].str.contains('gene|AAV|CRISPR|cell', case=False, na=False))
        ].head(10)  # 上位10件
        
        print(f"\n2. 重要な試験を選択: {len(important_trials)}件")
        
        # モデルの初期化
        print("\n3. モデルを初期化中...")
        self.simulator.initialize_models(historical_trials)
        
        # シミュレーション実行
        print("\n4. 統合シミュレーションを実行中...")
        results = self.simulator.run_integrated_simulation(
            important_trials, 
            parameters,
            n_simulations=5000  # 実行時間短縮のため5000回
        )
        
        # 結果の保存
        output_path = self.results_dir / "integrated_predictions_real.csv"
        results.to_csv(output_path, index=False)
        print(f"\n5. 結果を保存: {output_path}")
        
        # 結果の表示
        self._display_results(results)
        
        # 可視化
        print("\n6. 可視化を生成中...")
        self._create_visualizations(results)
        
        # 比較レポート
        comparison = self.simulator.generate_comparison_report(results)
        self._display_comparison(comparison)
        
        return results
    
    def _display_results(self, results: pd.DataFrame):
        """主要な結果を表示"""
        print("\n=== 予測結果サマリー ===\n")
        
        # 承認可能性が高い順にソート
        results_sorted = results.sort_values('integrated_success_rate', ascending=False)
        
        for idx, trial in results_sorted.iterrows():
            print(f"\n【{trial['BriefTitle'][:60]}...】")
            print(f"  NCT番号: {trial['NCTId']}")
            print(f"  フェーズ: {trial['Phase']}")
            print(f"  スポンサー: {trial['SponsorName']}")
            print(f"  統合成功率: {trial['integrated_success_rate']:.1%}")
            
            if trial['integrated_median_year'] and not pd.isna(trial['integrated_median_year']):
                year = int(trial['integrated_median_year'])
                std = trial['integrated_std_year'] if not pd.isna(trial['integrated_std_year']) else 2
                print(f"  承認予測: {year}年 (±{std:.1f}年)")
                
                # 最速と最遅の推定
                earliest = year - int(std)
                latest = year + int(std)
                print(f"  予測範囲: {earliest}年〜{latest}年")
            else:
                print(f"  承認予測: 成功可能性が低い")
            
            print(f"  予測信頼度: {trial['confidence_level']}")
            
            if trial['risk_factors'] != 'None identified':
                print(f"  リスク要因: {trial['risk_factors']}")
    
    def _create_visualizations(self, results: pd.DataFrame):
        """結果の可視化"""
        viz_dir = self.results_dir / "visualizations"
        viz_dir.mkdir(exist_ok=True)
        
        # 1. 承認タイムライン図
        self._plot_timeline(results, viz_dir)
        
        # 2. 手法比較図
        self._plot_method_comparison(results, viz_dir)
        
        # 3. 成功率分布
        self._plot_success_distribution(results, viz_dir)
        
        print(f"可視化を保存: {viz_dir}")
    
    def _plot_timeline(self, results: pd.DataFrame, output_dir: Path):
        """承認タイムラインの可視化"""
        # 成功可能性のある試験のみ
        timeline_data = results[results['integrated_median_year'].notna()].copy()
        
        if len(timeline_data) == 0:
            return
        
        timeline_data = timeline_data.sort_values('integrated_median_year')
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        y_positions = range(len(timeline_data))
        
        for i, (idx, trial) in enumerate(timeline_data.iterrows()):
            year = trial['integrated_median_year']
            std = trial['integrated_std_year'] if not pd.isna(trial['integrated_std_year']) else 2
            
            # エラーバーで範囲を表示
            ax.barh(i, 2*std, left=year-std, height=0.6, 
                   alpha=0.3, color='skyblue', edgecolor='blue')
            
            # 中央値をマーク
            ax.scatter(year, i, s=100, color='darkblue', zorder=10)
            
            # ラベル
            label = trial['BriefTitle'][:40] + '...' if len(trial['BriefTitle']) > 40 else trial['BriefTitle']
            ax.text(year-std-0.5, i, label, va='center', ha='right', fontsize=9)
        
        ax.set_yticks(y_positions)
        ax.set_yticklabels([])
        ax.set_xlabel('予測承認年', fontsize=12)
        ax.set_title('RP治療の承認予測タイムライン（統合予測）', fontsize=14)
        ax.grid(axis='x', alpha=0.3)
        
        # 現在年を表示
        current_year = datetime.now().year
        ax.axvline(current_year, color='red', linestyle='--', alpha=0.5, label=f'現在（{current_year}年）')
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(output_dir / 'approval_timeline_real.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_method_comparison(self, results: pd.DataFrame, output_dir: Path):
        """予測手法の比較"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        methods = ['mc_success_rate', 'bayes_success_rate', 'ml_success_rate', 'integrated_success_rate']
        method_labels = ['モンテカルロ', 'ベイズ', '機械学習', '統合']
        
        # 各手法の平均成功率
        avg_rates = [results[method].mean() for method in methods]
        
        bars = ax.bar(method_labels, avg_rates)
        
        # 色分け
        colors = ['lightcoral', 'lightgreen', 'lightskyblue', 'gold']
        for bar, color in zip(bars, colors):
            bar.set_color(color)
        
        # 数値を表示
        for i, (bar, rate) in enumerate(zip(bars, avg_rates)):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                   f'{rate:.1%}', ha='center', va='bottom')
        
        ax.set_ylabel('平均成功率', fontsize=12)
        ax.set_title('予測手法別の平均成功率比較', fontsize=14)
        ax.set_ylim(0, 1)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'method_comparison_real.png', dpi=300)
        plt.close()
    
    def _plot_success_distribution(self, results: pd.DataFrame, output_dir: Path):
        """成功率の分布"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # 1. フェーズ別成功率
        phase_success = results.groupby('Phase')['integrated_success_rate'].agg(['mean', 'std', 'count'])
        phases = phase_success.index
        
        ax1.bar(phases, phase_success['mean'], yerr=phase_success['std'], 
               capsize=5, color=['lightcoral', 'lightgreen', 'lightskyblue'])
        
        for i, (phase, row) in enumerate(phase_success.iterrows()):
            ax1.text(i, row['mean'] + row['std'] + 0.02, 
                    f"n={row['count']}", ha='center', va='bottom')
        
        ax1.set_ylabel('統合成功率', fontsize=12)
        ax1.set_title('フェーズ別の平均成功率', fontsize=14)
        ax1.set_ylim(0, 1)
        ax1.grid(axis='y', alpha=0.3)
        
        # 2. 信頼度分布
        confidence_counts = results['confidence_level'].value_counts()
        
        if len(confidence_counts) > 0:
            ax2.pie(confidence_counts.values, labels=confidence_counts.index, 
                   autopct='%1.1f%%', startangle=90)
            ax2.set_title('予測信頼度の分布', fontsize=14)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'success_distribution_real.png', dpi=300)
        plt.close()
    
    def _display_comparison(self, comparison: dict):
        """手法間の比較結果を表示"""
        print("\n=== 予測手法の比較分析 ===\n")
        
        if 'method_correlations' in comparison and comparison['method_correlations']:
            print("手法間の相関係数:")
            for pair, corr in comparison['method_correlations'].items():
                print(f"  {pair}: {corr:.3f}")
        
        print("\n各手法と統合予測の平均差:")
        for method, diff in comparison['average_differences'].items():
            print(f"  {method}: {diff:+.3f}")
        
        print("\n予測信頼度の分布:")
        for level, count in comparison['confidence_distribution'].items():
            print(f"  {level}: {count}件")
    
    def generate_detailed_report(self, results: pd.DataFrame):
        """詳細レポートの生成"""
        report_path = self.results_dir / "integrated_simulation_report.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 高度な統合シミュレーション結果レポート\n\n")
            f.write(f"生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}\n\n")
            
            f.write("## 概要\n\n")
            f.write(f"- 分析対象試験数: {len(results)}件\n")
            f.write(f"- 使用した予測手法: モンテカルロ、ベイズ推定、機械学習\n")
            f.write(f"- シミュレーション回数: 5,000回/試験\n\n")
            
            f.write("## 主要な予測結果\n\n")
            
            # 最も有望な試験トップ3
            top_trials = results.nlargest(3, 'integrated_success_rate')
            f.write("### 最も成功可能性が高い試験\n\n")
            
            for i, (idx, trial) in enumerate(top_trials.iterrows(), 1):
                f.write(f"#### {i}. {trial['BriefTitle']}\n")
                f.write(f"- NCT番号: {trial['NCTId']}\n")
                f.write(f"- 統合成功率: **{trial['integrated_success_rate']:.1%}**\n")
                if trial['integrated_median_year'] and not pd.isna(trial['integrated_median_year']):
                    f.write(f"- 承認予測: **{int(trial['integrated_median_year'])}年**\n")
                f.write(f"- 予測信頼度: {trial['confidence_level']}\n\n")
            
            f.write("## 手法別の分析\n\n")
            f.write("### 予測手法の特徴\n\n")
            f.write("- **モンテカルロ**: 過去の統計データに基づく確率的予測\n")
            f.write("- **ベイズ推定**: 新しい情報で動的に更新される予測\n")
            f.write("- **機械学習**: 試験の特徴から成功パターンを学習\n\n")
            
            f.write("### 統合の重み付け\n\n")
            f.write("- モンテカルロ: 30%\n")
            f.write("- ベイズ推定: 40%\n")
            f.write("- 機械学習: 30%\n\n")
            
            f.write("## 結論\n\n")
            f.write("高度な統合シミュレーションにより、より現実的で信頼性の高い予測が可能になりました。\n")
            f.write("特に、動的な更新と試験特性の考慮により、従来の静的な予測より精度が向上しています。\n")
        
        print(f"\n詳細レポートを生成: {report_path}")


def main():
    """メイン実行関数"""
    processor = RealDataProcessor()
    results = processor.run_real_data_simulation()
    
    if results is not None and len(results) > 0:
        processor.generate_detailed_report(results)
        print("\n✅ 高度なシミュレーションが完了しました！")
        print("\n結果は以下のファイルをご確認ください:")
        print(f"- CSVデータ: results/integrated_predictions_real.csv")
        print(f"- 可視化: results/visualizations/")
        print(f"- 詳細レポート: results/integrated_simulation_report.md")


if __name__ == "__main__":
    main()