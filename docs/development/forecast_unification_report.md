# 予測一本化の実装・検証報告（2026-10-02）

## 実装結果と完了条件

仕様書を全文確認し、成功率の2シナリオ化、知識ベースのforecastブロック、プログラム単位の到達確率、インラインSVGと数値表、前提とNAC検出力の説明、更新履歴、テストを実装した。

- パラメータ推定 → timeline_sim（最後にarrival_probability）→ レポート → 更新履歴 → 行動ガイド → Markdown個別ページ → 方法論 → 従来手書き4ページ、の順で実行成功。公開全13ページを生成元から再生成。
- CLAUDE.mdに新しいモジュール、前提、生成元、実行コマンドを追記。
- `PYTHONPATH=. .venv/bin/python -m pytest tests/ -q`: **66成功、13失敗**。失敗はすべて既存の公開ページコントラスト検査。追加の計算・表示・生成ページテストは成功。
- `check-contrast docs/public/<page>.html --json`: 全13ページで実行したが、Chromeが起動時に **SIGABRT** で終了し、検査結果JSONを取得できなかった。ライト・ダークのAA合格は未確認。書き込み可能な一時プロファイルを指定したChromeの直接起動でも同じ症状。
- `git diff --check`: 成功。
- `scripts/analysis/nac_attack_power.py` の全条件の再計算: 成功。30%抑制の検出確率69.0〜99.8%、20%は36.2〜86.7%、10%は12.8〜26.2%。README M3の概数と整合。
- 初回の図生成はGUIバックエンドで異常終了したため、ファイル出力用Aggに変更し、最終の再実行は成功。

**通せなかった工程**: 「pytest全件成功」と「check-contrast全ページ合格」。原因は上記Chromeの起動異常で、コントラスト比の不合格を観測したものではない。検査テストの閾値・スキップ条件は変更していない。

`rp-research/` は参照のみ。gitのcommit/push/ブランチ操作をせず、`.github/` と `data/raw/` に変更を加えていない。新規依存は不要（numpy/scipyは既存requirements.txtにある）。

## 新旧の成功確率

旧値は実装前のconfigの値（文書に記載された86.7% / 78.4% / 71.4%とは異なる）。完了率を効果確認の成功率として使用する前提を撤回。

| 段階 | 旧設定 | 新general | 新rp_history |
|---|---:|---:|---:|
| Phase 1→2 | 86.0%（計算上限で85.0%） | 71.6% | 71.6% |
| Phase 2→3 | 78.0% | 35.5% | 35.5% |
| Phase 3→申請 | 71.0% | 51.2% | 進行抑制11.1%、それ以外51.2% |
| 申請→承認 | 独立ゲートなし | 91.1% | 91.1% |
| 表示・計算上限 | 85.0% | 91.1% | 91.1% |

[BIO眼科の段階通過率](https://go.bio.org/rs/490-EHZ-999/images/ClinicalDevelopmentSuccessRates2011_2020.pdf)。RP過去11.1%は[ガイドラインCQ1](https://www.nichigan.or.jp/Portals/0/resources/member/guideline/nggz-2025-063.pdf)の進行抑制比較試験7系統・明確な成功0からラプラスの継起則で置いた仮定。遺伝子治療の最終試験×0.9は維持。既存薬は承認ゲートなし。

## 見出しと少なくとも1つ届く確率

**型を問わず進行を遅らせる治療が2030年までに日本で使える確率は 16〜26%**。
未丸めのモデル値はRP過去16.32%、眼科平均26.14%。NACなどの既存薬は最終試験の陽性結果を「使える」と数え、RP適応承認・保険適用と区別している。

すべて各年末までの確率（%、20,000回・seed 20261002・基準日2026-10-02）。

| 種別 | 年 | RP過去・米国 | RP過去・日本 | 眼科平均・米国 | 眼科平均・日本 |
|---|---:|---:|---:|---:|---:|
| slow_any | 2030 | 21.48 | 16.32 | 51.58 | 26.14 |
| slow_any | 2035 | 24.91 | 23.36 | 56.08 | 53.23 |
| slow_any | 2045 | 25.88 | 25.88 | 57.68 | 57.68 |
| restore_any | 2030 | 91.51 | 91.14 | 91.51 | 91.14 |
| restore_any | 2035 | 97.24 | 92.87 | 97.24 | 92.87 |
| restore_any | 2045 | 97.61 | 97.61 | 97.61 | 97.61 |

slow_anyはgroup=slowかつ型不問のみ（対象限定のNPI-001を含まない）。OCU400はslow、jCellsは中間・細胞治療としてrestore。restoreの2シナリオが一致するのは、RP過去の変更を進行抑制だけに適用するため。

## 主要プログラムの新旧比較

試験別 `forecasts.csv` の該当する代表試験を比較。年は到達に成功した場合のみの中央値。NACは承認確率・承認年ではなく、最終試験陽性の到達確率・年。

| プログラム（代表試験） | 旧累積確率 | 新general | 新rp_history | FDA中央値年 旧→新 | 日本中央値年 旧→新 |
|---|---:|---:|---:|---|---|
| MCO-010（NCT04945772） | 49.842% | 91.100% | 91.100% | 2027→2027 | 2027→2027 |
| OCU400（NCT06388200） | 63.900% | 41.979% | 41.979% | 2028→2028 | 2033→2033 |
| AGTC-501（NCT04850118） | 85.000% | 77.435% | 77.435% | 2028→2028 | 2033→2033 |
| NAC Attack（NCT05537220） | 71.000% | 18.176% | 11.100% | 2029→2029 | 2034→2029 |

MCO-010は審査91.1%のみ。AGTC-501は設定85%×審査91.1%=77.435%。実装前のAGTC-501は表示85%に対し実際の模擬成功率50.56%で不一致だった。現在は表示77.435%に対し模擬78.07%で、乱数による揺れの範囲に一致する。

プログラム単位モデルはBIOの段階期間と主要評価完了予定日、試験別モデルは従来の期間分布・経過時間・個別申請日程を使う。仕様第1節の試験別CSVは軸AだけにRP過去補正を適用するため、軸A/BのOCU400は両シナリオが同値。第2節の到達確率モデルではOCU400をslowに含めて補正する。到達年の分位点は一致するとは限らない。またslowの第2相・第3相は共通の潜在変数で連動するため、プログラム単位モデルの推定確率は試験別の独立したゲートの積と異なる。

プログラム単位の結果（年は小数年、到達した場合の中央値と10〜90%幅）：

| プログラム | シナリオ | 到達確率 | 米国中央値（10〜90%） | 日本中央値（10〜90%） |
|---|---|---:|---|---|
| MCO-010 | general | 91.14% | 2027.59（2027.23〜2027.96） | 2028.01（2027.56〜2028.46） |
| MCO-010 | rp_history | 91.14% | 2027.59（2027.23〜2027.96） | 2028.01（2027.56〜2028.46） |
| OCU400 | general | 42.58% | 2028.46（2028.05〜2029.08） | 2033.50（2032.33〜2034.75） |
| OCU400 | rp_history | 8.92% | 2028.46（2028.05〜2029.08） | 2033.56（2032.38〜2034.76） |
| AGTC-501 | general | 77.48% | 2030.31（2029.27〜2031.35） | 2035.32（2033.84〜2036.79） |
| AGTC-501 | rp_history | 77.48% | 2030.31（2029.27〜2031.35） | 2035.32（2033.84〜2036.79） |
| NAC Attack | general | 17.85% | 2029.41（2029.41〜2029.41） | 2029.41（2029.41〜2029.41） |
| NAC Attack | rp_history | 10.68% | 2029.41（2029.41〜2029.41） | 2029.41（2029.41〜2029.41） |

## nullにした項目

| プログラム | null項目 | 扱い・理由 |
|---|---|---|
| MCO-010 | readout | 申請受理済みなので臨床段階のreadoutは不要。審査期間で推定。 |
| GS030 | readout | 主要評価完了予定日を確認できない。試験全体の完了日は代用せず、BIOの期間で推定。 |
| 4D-125 | readout | 主要評価完了予定日を確認できない。試験全体の完了日は代用せず、BIOの期間で推定。 |
| CTx-PDE6b | stage, readout, not_started | 段階・開始状況と主要評価完了予定日を取得済みデータから確認できず、計算対象外。 |
| SPVN20 | readout | 主要評価完了予定日を確認できない。試験全体の完了日は代用せず、BIOの期間で推定。 |
| VG901 | readout | 主要評価完了予定日を確認できない。試験全体の完了日は代用せず、BIOの期間で推定。 |
| RTx-015 | readout | 主要評価完了予定日を確認できない。試験全体の完了日は代用せず、BIOの期間で推定。 |
| RV-001 | readout | watchlistでも主要評価完了予定日がnull。日本発で遅れなし、BIOの期間で推定。 |

前臨床（AAV-mVChR1、Prime editing）はforecastブロックを付けず除外。GS030・4D-125・SPVN20の登録IDは取得済み試験データから補った。GS030/4D-125の曖昧なClinical development表記は登録データのPhase 1/2に具体化した。

## 変更ファイル一覧

開始時点から存在した未追跡ファイル `.claude/settings.local.json` と `docs/development/forecast_unification_spec.md` は変更していない。

- `CLAUDE.md`
- `config/simulation_params.yaml`
- `data/knowledge_base/clinical_programs.json`
- `data/knowledge_base/site_metadata.json`
- `data/knowledge_base/update_history.json`
- `data/processed/parameters.yaml`
- `docs/content/main/detailed_analysis.md`
- `docs/content/main/disclaimer.md`
- `docs/content/main/index.md`
- `docs/content/main/medical_info.md`
- `docs/content/main/patient_guide.md`
- `docs/content/main/reality_and_actions.md`
- `docs/content/medical/for_doctor_checklist.md`
- `docs/development/forecast_unification_report.md`
- `docs/development/technical/simulation_methodology.md`
- `docs/public/detailed_analysis.html`
- `docs/public/disclaimer.html`
- `docs/public/images/CDF.png`
- `docs/public/images/tornado.png`
- `docs/public/images/waterfall.png`
- `docs/public/index.html`
- `docs/public/medical_info.html`
- `docs/public/patient_guide.html`
- `docs/public/reality_and_actions.html`
- `docs/public/regional_approval_timeline.html`
- `docs/public/report.html`
- `docs/public/simulation_methodology.html`
- `docs/public/updates.html`
- `results/arrival_probability.json`
- `results/figs/CDF.png`
- `results/figs/tornado.png`
- `results/figs/waterfall.png`
- `results/forecasts.csv`
- `scripts/analysis/nac_attack_power.py`
- `src/ingest/parameters.py`
- `src/reporting/arrival_visualization.py`
- `src/reporting/build_landing_page.py`
- `src/reporting/build_report.py`
- `src/reporting/build_simulation_methodology_html.py`
- `src/reporting/build_static_pages.py`
- `src/reporting/build_updates_page.py`
- `src/reporting/site_metadata.py`
- `src/sim/arrival_probability.py`
- `src/sim/timeline_sim.py`
- `tests/test_arrival_probability.py`
- `tests/test_basic.py`
- `tests/test_parameters.py`
- `tests/test_simulation.py`

公開13ページのうち、accessible_summary.html / faq.html / japan_action_guide.htmlは再生成したが、最終内容に差分なし。results/sensitivity_analysis.csvも再計算したが差分なし。
