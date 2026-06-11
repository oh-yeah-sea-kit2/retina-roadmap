"""基本的なテストケース"""

import json
import re
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
        import src.reporting.build_accessible_summary_html
        import src.reporting.build_landing_page
        import src.reporting.build_faq_page
        import src.reporting.build_japan_action_guide_html
        import src.reporting.glossary
        import src.reporting.message_design
        import src.reporting.timeline_visualization
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
        assert "success_rate_policy" in params
        assert params["success_rate_policy"]["display_cap"] == 0.85
        assert params["success_rate_policy"].get("methodology_sources")


def test_forecast_results():
    """予測結果ファイルの構造を確認"""
    import pandas as pd
    
    forecast_file = Path("results/forecasts.csv")
    if forecast_file.exists():
        df = pd.read_csv(forecast_file)
        
        # 必要なカラムが存在することを確認
        required_columns = [
            "NCTId", "BriefTitle", "Phase", "SponsorName",
            "success_rate", "phase_historical_success_rate",
            "cumulative_approval_probability", "median_approval_year"
        ]
        
        for col in required_columns:
            assert col in df.columns, f"Column {col} missing from forecasts.csv"

        assert df["success_rate"].max() <= 0.85
        assert df["cumulative_approval_probability"].max() <= 0.85
        assert (df["success_rate"] == df["cumulative_approval_probability"]).all()


def test_public_html_has_no_100_percent_success_display():
    """公開HTMLに旧来の100%成功率表示が残っていないことを確認"""
    public_dir = Path("docs/public")
    if not public_dir.exists():
        return

    for html_file in public_dir.glob("*.html"):
        content = html_file.read_text(encoding="utf-8")
        assert "100.0%" not in content
        assert "個別成功率" not in content


def test_public_report_uses_separated_probability_labels():
    """レポート表でフェーズ平均と累積承認確率が分離されていることを確認"""
    report_file = Path("docs/public/report.html")
    if not report_file.exists():
        return

    content = report_file.read_text(encoding="utf-8")
    assert "フェーズ平均の過去成功率" in content
    assert "累積承認確率（残フェーズ）" in content


def test_stale_mco_010_2025_2026_claim_removed():
    """MCO-010の旧い2025-2026承認表現を再発させない"""
    checked_paths = [
        *Path("docs/content").glob("**/*.md"),
        *Path("docs/public").glob("*.html"),
        Path("README.md"),
    ]
    stale_patterns = [
        "MCO-010の2025-2026年承認予測",
        "2025年第1四半期にFDA申請、最速2025年後半",
        "2025年第1四半期（1月から3月）にFDAに申請予定です",
        "最速で2025年後半から2026年に最初の治療法",
    ]

    for path in checked_paths:
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        for pattern in stale_patterns:
            assert pattern not in content, f"{pattern} remains in {path}"


def test_sprint2_programs_have_registry_ids_and_primary_sources():
    """Sprint 2対象プログラムは登録番号と一次ソースURLを持つ"""
    kb_path = Path("data/knowledge_base/clinical_programs.json")
    kb = json.loads(kb_path.read_text(encoding="utf-8"))
    programs = kb["programs"]

    sprint2_programs = [
        "OCU400",
        "Botaretigene sparoparvovec",
        "AGTC-501",
        "NAC Attack",
        "NPI-001",
        "DSP-3077",
        "SPVN06",
        "RV-001",
        "SENTAN-PVS-NP",
        "Prime editing in vivo rescue",
    ]

    for pid in sprint2_programs:
        assert pid in programs, f"{pid} missing from knowledge base"
        sources = programs[pid].get("primary_sources", [])
        assert sources, f"{pid} missing primary_sources"
        assert all(src.get("url", "").startswith("https://") for src in sources)

        trial_ids = programs[pid].get("trial_ids", [])
        if programs[pid].get("current_phase") == "Preclinical":
            assert programs[pid].get("registry_note")
        else:
            assert trial_ids, f"{pid} missing trial_ids"
            assert any(t.startswith(("NCT", "jRCT")) for t in trial_ids)


def test_sprint2_stale_program_claims_removed_from_knowledge_base():
    """古いSprint 2対象プログラム表現を再発させない"""
    content = Path("data/knowledge_base/clinical_programs.json").read_text(
        encoding="utf-8"
    )
    stale_patterns = [
        "XLRP開発は事実上停滞",
        "J&J優先パイプライン",
        "BLA plans cancelled",
        "Phase 2/3確認試験（NCT07290530）が2026年初頭に開始",
        "SPVN06 PRODYGY 12ヶ月トップラインデータ発表",
        "Expanded Access Program承認済み",
    ]

    for pattern in stale_patterns:
        assert pattern not in content


def test_sprint3_programs_have_message_design_classification():
    """主要プログラムはA/B軸と型不問/型特異ラベルを持つ"""
    kb_path = Path("data/knowledge_base/clinical_programs.json")
    kb = json.loads(kb_path.read_text(encoding="utf-8"))
    programs = kb["programs"]

    assert "message_design" in kb
    assert "A" in kb["message_design"]["axes"]
    assert "B" in kb["message_design"]["axes"]

    required_programs = [
        "MCO-010",
        "OCU400",
        "AGTC-501",
        "Botaretigene sparoparvovec",
        "NAC Attack",
        "NPI-001",
        "DSP-3077",
        "SPVN06",
        "RV-001",
        "SENTAN-PVS-NP",
        "Prime editing in vivo rescue",
    ]
    allowed_axes = {"A", "B", "A/B", "B/intermediate"}
    allowed_scopes = {"型不問", "型特異", "対象限定", "前臨床"}

    for pid in required_programs:
        design = programs[pid].get("message_design", {})
        assert design.get("axis") in allowed_axes, f"{pid} missing axis"
        assert design.get("axis_label"), f"{pid} missing axis label"
        assert design.get("genotype_scope") in allowed_scopes, f"{pid} missing scope"
        assert design.get("patient_summary"), f"{pid} missing patient summary"


def test_sprint3_landing_page_order_and_no_top_nct_exposure():
    """トップは今できることを先に出し、登録番号は露出しない"""
    index_path = Path("docs/public/index.html")
    if not index_path.exists():
        return

    content = index_path.read_text(encoding="utf-8")
    assert "3分でわかる" in content
    assert "あなたが今すぐできること" in content
    assert "2軸で見る治療の見通し" in content
    assert content.index("あなたが今すぐできること") < content.index("2軸で見る治療の見通し")
    assert "NCT" not in content
    assert "jRCT203" not in content


def test_sprint3_faq_answers_timing_with_two_axes():
    """FAQの「いつ治る」は単一年ではなく2軸で答える"""
    faq_path = Path("docs/public/faq.html")
    if not faq_path.exists():
        return

    content = faq_path.read_text(encoding="utf-8")
    assert "「何年に治る」と単一年では答えられません" in content
    assert "進行を遅らせる治療" in content
    assert "失った視力を取り戻す・根治を目指す治療" in content
    assert "最も早い治療法（OCU400）" not in content


def test_sprint4_japan_action_guide_has_official_sources():
    """日本向け行動ガイドは公式ソースと主要窓口を含む"""
    md_path = Path("docs/content/regional/japan_action_guide.md")
    assert md_path.exists()

    content = md_path.read_text(encoding="utf-8")
    required_terms = [
        "神戸アイセンター",
        "JRPRP",
        "KEYS",
        "UMIN000057025",
        "RP-PRIMARY",
        "PMID",
        "jRCT",
        "難病治験ウェブ",
        "JRPS",
        "DSP-3077",
        "RV-001",
        "SENTAN",
    ]
    for term in required_terms:
        assert term in content, f"{term} missing from Japan action guide"

    required_urls = [
        "https://kobe.eye.center.kcho.jp/outpatient/disease.html",
        "https://www.kobe-eye-center.jp/",
        "https://www.amed.go.jp/program/IRUD/",
        "https://convention.jtbcom.co.jp/jrprp/",
        "https://rctportal.mhlw.go.jp/detail/um?trial_id=UMIN000049034",
        "https://center6.umin.ac.jp/cgi-open-bin/ctr/ctr_view.cgi?recptno=R000065178",
        "https://pubmed.ncbi.nlm.nih.gov/40042698/",
        "https://jrct.mhlw.go.jp/",
        "https://nanbyo-chiken.nibn.go.jp/",
        "https://jrps.org/",
    ]
    for url in required_urls:
        assert url in content, f"{url} missing from Japan action guide"


def test_sprint4_public_pages_link_japan_action_guide():
    """トップと既存アクションページから日本向け手順へ遷移できる"""
    index_path = Path("docs/public/index.html")
    action_path = Path("docs/public/reality_and_actions.html")
    guide_path = Path("docs/public/japan_action_guide.html")
    if not index_path.exists() or not action_path.exists() or not guide_path.exists():
        return

    index_content = index_path.read_text(encoding="utf-8")
    action_content = action_path.read_text(encoding="utf-8")
    guide_content = guide_path.read_text(encoding="utf-8")

    assert "japan_action_guide.html" in index_content
    assert "japan_action_guide.html" in action_content
    assert "今日からできる3ステップ" in guide_content
    assert "https://jrct.mhlw.go.jp/" in guide_content
    assert ("jrct." + "niph.go.jp") not in guide_content

    for html_file in Path("docs/public").glob("*.html"):
        content = html_file.read_text(encoding="utf-8")
        assert ("jrct." + "niph.go.jp") not in content, (
            f"old jRCT URL remains in {html_file}"
        )


def test_sprint5_landing_has_timeline_visualization():
    """トップに2軸タイムラインを予測幅つきで表示する"""
    index_path = Path("docs/public/index.html")
    if not index_path.exists():
        return

    content = index_path.read_text(encoding="utf-8")
    assert "タイムラインで見る治療の見通し（予測）" in content
    assert "timeline-chart" in content
    assert "timeline-bar" in content
    assert "--bar-left" in content
    assert "A: 進行を遅らせる" in content
    assert "B/中間: 視覚再建・根治を目指す" in content
    assert "2026" in content
    assert "2040" in content
    assert "FDA承認から2〜5年程度" in content
    assert "NCT" not in content
    assert "jRCT203" not in content


def test_sprint5_glossary_annotations_and_terms():
    """初出用語にabbr/ruby注釈を付け、用語辞書を保つ"""
    from src.reporting.glossary import GLOSSARY_TERMS

    terms = {term.term: term.title for term in GLOSSARY_TERMS}
    for required in [
        "網膜色素変性症",
        "光受容体",
        "遺伝子治療",
        "神経保護",
        "型不問",
        "型特異",
        "BLA",
        "Phase 3",
        "第3相",
        "EAP",
        "iPS細胞",
        "光遺伝学",
        "RdCVF",
    ]:
        assert required in terms

    index_path = Path("docs/public/index.html")
    if not index_path.exists():
        return

    content = index_path.read_text(encoding="utf-8")
    assert 'class="term-abbr"' in content
    assert 'title="もうまくしきそへんせいしょう"' in content
    assert "<rt>もうまくしきそへんせいしょう</rt>" in content
    assert 'title="どの遺伝子変異でも対象になりうる治療"' in content


def test_sprint6_backup_archived_and_not_referenced():
    """公開バックアップはarchiveへ移動し、公開/生成/テストから参照しない"""
    backup_name = "public_" + "backup_20250724"
    assert not (Path("docs") / backup_name).exists()
    assert (Path("archive") / backup_name).exists()

    checked_paths = [
        *Path("docs/public").glob("**/*"),
        *Path("src").glob("**/*"),
        *Path("tests").glob("**/*"),
    ]
    for path in checked_paths:
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        assert backup_name not in content, f"{backup_name} referenced in {path}"


def test_sprint6_monitor_targets_include_japan_and_new_programs():
    """月次監視対象は新規プログラムと日本語検索を設定ファイルで共有する"""
    import yaml

    config = yaml.safe_load(Path("config/monitor_targets.yaml").read_text(
        encoding="utf-8"
    ))
    programs = config["programs"]
    for program in [
        "SPVN06",
        "RV-001",
        "Botaretigene sparoparvovec",
        "DSP-3077",
        "SENTAN-PVS-NP",
    ]:
        assert program in programs

    query_text = "\n".join(item["query"] for item in config["general_queries"])
    assert "jrct.mhlw.go.jp" in query_text
    assert "nanbyo-chiken.nibn.go.jp" in query_text
    assert "網膜色素変性" in query_text


def test_sprint6_stale_optimistic_phrases_removed_from_sources():
    """陳腐化した最速年・100%・旧ラベルを生成元から除去する"""
    checked_paths = [
        *Path("docs/content").glob("**/*"),
        *Path("src/reporting").glob("**/*"),
        *Path("data").glob("**/*"),
    ]
    stale_year_pattern = re.compile(
        r"最速202[0-6]|最速2025|最速2026|2025年承認|2026年承認"
    )
    stale_success_patterns = ["100.0%", "個別成功率"]

    for path in checked_paths:
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        assert not stale_year_pattern.search(content), f"stale year phrase in {path}"
        for pattern in stale_success_patterns:
            assert pattern not in content, f"{pattern} remains in {path}"


def test_release_review_accessible_summary_refreshed():
    """音声読み上げ対応版にSprint前の旧情報を残さない"""
    html_path = Path("docs/public/accessible_summary.html")
    md_path = Path("docs/content/accessibility/accessible_summary.md")
    assert html_path.exists()
    assert md_path.exists()

    combined = (
        html_path.read_text(encoding="utf-8")
        + "\n"
        + md_path.read_text(encoding="utf-8")
    )
    stale_patterns = [
        "100パーセント",
        "80パーセント以上",
        "2025年初め",
        "2030年までに5個から10個",
        "研究支援の寄付",
        "政策提言への参加",
    ]
    for pattern in stale_patterns:
        assert pattern not in combined, f"{pattern} remains in accessible summary"

    required_terms = [
        "進行を止める、または遅らせる治療",
        "失った視力を取り戻す、または根治を目指す治療",
        "今日からできる3ステップ",
        "https://jrct.mhlw.go.jp/",
        "https://nanbyo-chiken.nibn.go.jp/",
        "神戸アイセンター",
        "JRPS",
    ]
    for term in required_terms:
        assert term in combined, f"{term} missing from accessible summary"


def test_release_review_placeholders_and_japan_guide_headings_removed():
    """レビュー指摘のプレースホルダー、空ソース、H1重複を防ぐ"""
    public_html = "\n".join(
        path.read_text(encoding="utf-8") for path in Path("docs/public").glob("*.html")
    )
    source_text = "\n".join(
        path.read_text(encoding="utf-8") for path in Path("docs/content").glob("**/*.md")
    )
    assert "現行URL" not in public_html
    assert "現行URL" not in source_text

    guide_html = Path("docs/public/japan_action_guide.html").read_text(encoding="utf-8")
    assert guide_html.count("<h1>日本の読者向けアクションガイド</h1>") == 1
    assert "一次ソース:</p>\n<ul>" not in guide_html
    assert "一次ソース: jRCT" in guide_html
    assert "https://jrct.mhlw.go.jp/" in guide_html
