"""基本的なテストケース"""

import sys
from pathlib import Path

# srcディレクトリをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """主要モジュールがインポートできることを確認"""
    try:
        import src.fetch_trials
        import src.fetch_papers
        import src.ingest.parameters
        import src.sim.timeline_sim
        import src.reporting.build_report
        assert True
    except ImportError as e:
        assert False, f"Import failed: {e}"


def test_data_directories():
    """必要なディレクトリが存在することを確認"""
    required_dirs = [
        "data/raw/clinical_trials",
        "data/raw/literature", 
        "data/processed",
        "results/figs",
        "docs"
    ]
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        assert path.exists(), f"Directory {dir_path} does not exist"


def test_parameters_file():
    """パラメータファイルの構造を確認"""
    import yaml
    
    param_file = Path("data/processed/parameters.yaml")
    if param_file.exists():
        with open(param_file, "r") as f:
            params = yaml.safe_load(f)
        
        # 必要なキーが存在することを確認
        assert "phase_durations_years" in params
        assert "phase_success_rates" in params
        assert "regulatory_timelines_years" in params
        assert "simulation_parameters" in params


def test_forecast_results():
    """予測結果ファイルの構造を確認"""
    import pandas as pd
    
    forecast_file = Path("results/forecasts.csv")
    if forecast_file.exists():
        df = pd.read_csv(forecast_file)
        
        # 必要なカラムが存在することを確認
        required_columns = [
            "NCTId", "BriefTitle", "Phase", "SponsorName",
            "success_rate", "median_approval_year"
        ]
        
        for col in required_columns:
            assert col in df.columns, f"Column {col} missing from forecasts.csv"