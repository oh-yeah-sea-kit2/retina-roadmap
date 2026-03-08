# CLAUDE.md

このファイルは、このリポジトリで作業する際のClaude Code (claude.ai/code) へのガイダンスを提供します。

## 重要な指示

**常に日本語で応答すること。**

**重要: 大きな変更を加えた場合は、必ずCLAUDE.mdファイルも更新すること。特に以下の場合：**
- 新しいスクリプトやモジュールを追加した場合
- ディレクトリ構造を変更した場合
- 新しい開発コマンドを追加した場合
- アーキテクチャに変更を加えた場合
- 新しい依存関係を追加した場合

**HTML生成時の重要な要件：**
- HTTPで始まるURLは自動的にクリッカブルなリンクに変換すること
- テーブルはスマートフォンでも見やすいレスポンシブデザインにすること
- HTMLを修正する場合は、常に生成元のPythonコードを修正すること（手動でHTMLを編集しない）

## プロジェクト概要

網膜色素変性症（RP）の治療法がいつ頃利用可能になるかをモンテカルロシミュレーションで予測する医学研究予測システムです。臨床試験データベースからデータを取得し、処理して確率的予測を生成します。

## よく使う開発コマンド

```bash
# 依存関係のインストール
uv pip install -r requirements.txt

# テストの実行
pytest tests/

# 特定のテストファイルを実行
pytest tests/test_basic.py

# データ取得から分析まで一連の処理を実行
python src/fetch_trials.py          # 臨床試験データ取得
python src/fetch_papers.py          # 文献データ取得
python src/ingest/parameters.py     # パラメータ推定
python src/sim/timeline_sim.py      # シミュレーション実行
python src/reporting/build_report.py # レポート生成

# レポートのみ再生成（データ取得なし）
python src/reporting/build_report.py

# ローカルでHTMLレポートを確認
open docs/public/index.html         # ランディングページ
open docs/public/report.html        # シミュレーションレポート

# 最新情報で全体を更新（カスタムコマンド）
# Claude Codeで /update_rp_info と入力して実行
python scripts/update_latest_info.py
```

## アーキテクチャ概要

このコードベースは、関心の分離を明確にしたETLパイプラインアーキテクチャに従っています：

1. **データ収集層** (`src/fetch_*.py`)
   - ClinicalTrials.govとPubMed APIからデータを取得
   - Claude Codeの外部アクセス制限内で動作するようキャッシュを実装
   - 取得したデータはすべて`data/raw/`に不変のJSONファイルとして保存

2. **処理層** (`src/ingest/`)
   - 生データを分析可能な形式に変換
   - モンテカルロシミュレーション用のパラメータを推定
   - `data/processed/`に出力

3. **シミュレーションコア** (`src/sim/`)
   - モンテカルロシミュレーションエンジン
   - フェーズ遷移を含む医薬品開発タイムラインをモデル化
   - 不確実性の伝播を処理

4. **出力層** (`src/viz/` と `src/reporting/`)
   - 異なる対象者向けの可視化を生成
   - 複数の形式（技術者向け、患者向け、一般向け）で自動レポートを作成

## 実装上の重要な考慮事項

1. **外部APIアクセス**: Claude Codeの限定的な外部アクセスで動作するよう設計：
   - すべてのAPIレスポンスを`data/raw/`にローカルキャッシュ
   - 再ダウンロードを避けるため増分取得を使用
   - オフライン分析用に処理済みデータを保存

2. **Pythonバージョン**: SYSTEM.mdで指定されているPython 3.11を使用

3. **データの不変性**: `data/raw/`内のファイルは決して変更しない - これにより再現性を確保

4. **モンテカルロパラメータ**: 主要なシミュレーションパラメータは設定ファイルに保存し、バージョン管理する

5. **テスト戦略**: すべてのデータ処理とシミュレーションロジックには対応するテストが必要

6. **Web検索（重要）**: 最新情報を検索する際は、必ず以下の優先順位で使用すること：
   - **第1優先**: gemini-searchコマンドが利用可能な場合
     ```bash
     gemini --prompt "WebSearch: <検索クエリ>"
     ```
   - **第2優先**: gemini-searchが利用できない場合のみ、ビルトインのWebSearchツールを使用
   - **用途**: 最新の臨床試験情報、論文情報、規制承認状況の取得に使用

7. **GitHub Actions YAMLファイルの検証（必須）**: `.github/workflows/`内のYAMLファイルを作成・修正する際は、**必ず**`act`コマンドで構文チェックを行うこと：
   ```bash
   # YAMLファイル作成・修正後に必ず実行
   act --list
   ```
   - エラーが出た場合は修正してから再度チェック
   - 構文が正しければワークフロー一覧が表示される
   - `act`がインストールされていない場合は `brew install act` で導入

## プロジェクト固有のコンテキスト

- 主な対象者：研究者、RP患者、一般市民
- 再現性と透明性を重視
- 結果はGitHub Pages経由で公開
- すべての可視化でアクセシビリティを考慮（色覚異常対応のパレット）
- レポートは異なる対象者向けに複数の形式で生成

## 開発ワークフロー

**重要: すべての変更は必ずPull Request（PR）を通して適用すること**

1. **ブランチ戦略**:
   - `develop`ブランチに直接コミット・プッシュしない
   - 機能追加・修正は必ず新しいブランチを作成: `feature/xxx`, `fix/xxx`, `docs/xxx`
   - 変更完了後はPRを作成し、レビュー後に`develop`にマージ

2. **PR作成の手順**:
   ```bash
   # 1. developブランチから最新を取得
   git checkout develop && git pull

   # 2. 新しいブランチを作成
   git checkout -b fix/issue-number-description

   # 3. 変更を実装・コミット
   git add . && git commit -m "fix: description"

   # 4. リモートにプッシュ
   git push -u origin fix/issue-number-description

   # 5. PRを作成
   gh pr create --base develop --title "fix: description" --body "..."
   ```

3. 実装順序はTASK_LIST.jsonのタスクリストに従う
4. すべてのデータ変換をコード化（手動ステップなし）
5. 外部依存関係やAPIキーが必要な場合は文書化
6. 変更をコミットする前にテストを実行

## 重要なファイル

- `TASK_LIST.json`: 詳細な実装ロードマップ（完了済み）
- `README.md`: 包括的なプロジェクト仕様と方法論
- `SYSTEM.md`: Claude Code操作手順
- `docs/public/index.html`: ランディングページ（手動編集）
- `docs/public/report.html`: 自動生成されるシミュレーションレポート（build_report.pyで生成）
- `docs/content/`: Markdownソースファイル
- `docs/development/`: 開発ドキュメント
- `.github/workflows/ci.yml`: GitHub Actions CI/CD設定
- `scripts/update_latest_info.py`: 最新情報自動更新スクリプト
- `.claude/commands/update_rp_info.md`: Claude Code用カスタムコマンド /update_rp_info
- `data/knowledge_base/`: 構造化された治療プログラム情報の知識ベース

## docsディレクトリ構造（2025年7月24日更新）

```
docs/
├── public/          # GitHub Pages公開用
│   ├── *.html      # 公開用HTMLファイル
│   └── images/     # 図表（CDF.png等）
├── content/         # Markdownソース
│   ├── main/       # メインコンテンツ
│   ├── medical/    # 医療従事者向け
│   └── regional/   # 地域別情報
├── development/     # 開発ドキュメント
│   ├── planning/   # 計画・提案書
│   └── technical/  # 技術仕様書
└── checklists/      # チェックリスト類
```

## 完了したタスク（2025年6月25日時点）

1. ✅ 初期ディレクトリ構造の構築
2. ✅ 臨床試験データ取得機能（ClinicalTrials.gov API v2対応）
3. ✅ PubMed文献データ取得機能
4. ✅ 治験パラメータ推定（成功率・期間）
5. ✅ モンテカルロシミュレーション（10,000回/プログラム）
6. ✅ 感度分析とトルネード図生成
7. ✅ 自動レポート生成（Markdown/HTML）
8. ✅ 開発ボトルネック分析ドキュメント
9. ✅ GitHub Actions CI/CDパイプライン

## 主な分析結果

- **最速承認予測（米国FDA）**:
  - **MCO-010（Nanoscope社）**: 2026年（BLA rolling submission進行中、Priority Review対象）
  - **OCU400（Ocugen社）**: 2027年（Phase 3 liMeliGhT、2026年H1 BLA開始予定）
  - Beacon AGTC-501: 2029年（VISTA試験登録完了、2026年H2トップラインデータ）
  - PYC VP-001: 2030年（Phase 2/3 registrational study FDA alignment完了）
- **日本承認予測**:
  - MCO-010: 2029年（先駆け指定により遅延約2年に短縮）[90%信頼区間: 2028-2029年]
  - OCU400: 2032年（FDA承認の5年後）[90%信頼区間: 2031-2033年]
  - VP-001: 2035年（FDA承認の5年後）[90%信頼区間: 2034-2036年]
- **全体中央値**: 2035年（FDA承認）
- **Phase別成功率**: Phase 1: 86.7%, Phase 2: 78.4%, Phase 3: 71.4%（※限定的データに基づく）
- **アクティブな試験数**: 55件（重要な完了試験含む）

## 最近の更新履歴

### 2026年3月9日（自動更新）
- **Web検索による最新情報更新（/update_rp_info full実行）**

## 網膜色素変性症治療法 最新情報更新サマリー
更新日時: 2026年3月9日

## 📊 更新チェック結果サマリー

- 新規プログラム: 1件（SPVN20）
- 更新されたプログラム: 3件
- 変更なし: 15件
- 重要な更新: 2件

### 🚨 重要な更新（重要度70以上）
- **OCU400（Ocugen）**: Phase 3 liMeliGhT試験登録完了 - 重要度: 95
  * 2026年3月2日: 登録完了を発表（140名、2:1ランダム化）
  * RHOアームとgene-agnosticアームを含む、小児（3歳以上）も対象
  * BLA rolling submission Q3 2026予定（以前はH1 2026）
  * トップラインデータQ1 2027予定（以前はQ4 2026）
  * 3年間Phase 1/2データ: 88%(7/8)改善/維持、約2ライン改善
  * 2027年承認・商用化を目指す

- **MCO-010（Nanoscope）**: スターガルト病Phase 3計画 - 重要度: 70
  * STARLIGHT Phase 2試験で陽性データ
  * 2026年にスターガルト病Phase 3 registrational試験開始予定
  * RP向けBLA rolling submission継続中

### 🆕 新規プログラム
- **SPVN20（SparingVision）**: 休眠錐体細胞再活性化遺伝子治療
  * NYRVANA Phase 1/2試験で初患者投与（2025年10月）
  * 進行したRP患者の休眠錐体を再活性化し、視力と色覚を回復
  * ベルギーで開始、フランス・アイルランドに拡大、2026年に米国申請予定
  * SparingVisionの2番目の治療プログラム（SPVN06に加え）

### 🔄 更新されたプログラム詳細
1. **OCU400（Ocugen）**: 登録完了（140名）、BLA Q3 2026、トップラインQ1 2027に更新
2. **MCO-010（Nanoscope）**: スターガルトPhase 3計画追加
3. **OpCT-001（BlueRock）**: Phase 2登録人数更新（最大30名×2コホート）

### ✅ 変更なし（既知の情報）
- VP-001, AGTC-501, NPI-001, SPVN06, Ultevursen, Botaretigene sparoparvovec, VG901, ZM-02, jCells, DSP-3077, Keio_Optogenetics, GS030, 4D-125, CTx-PDE6b, AAV-mVChR1

### 📈 シミュレーション結果
- アクティブ試験数: 55件
- **最速承認予測（FDA）**: MCO-010 2026年（BLA priority review）
- **日本最速承認予測**: MCO-010 2029年（先駆け指定）
- **OCU400**: FDA 2027年（liMeliGhT登録完了）、日本 2032年
- **全体中央値**: 2035年（FDA承認）
- **Phase別成功率**: Phase 1: 86.7%, Phase 2: 78.4%, Phase 3: 71.4%

### 2026年2月27日（自動更新）
- **Web検索による最新情報更新（/update_rp_info full実行）**

## 網膜色素変性症治療法 最新情報更新サマリー
更新日時: 2026年2月27日

## 📊 更新チェック結果サマリー

- 新規プログラム: 1件（DSP-3077）
- 更新されたプログラム: 10件
- 変更なし: 4件
- 重要な更新: 6件
- 削除: 1件（重複Botaretigeneエントリ）

### 🚨 重要な更新（重要度70以上）
- **MCO-010（Nanoscope）**: 日本MHLW先駆け指定＋オーファン指定取得（2026年1月） - 重要度: 95
  * 網膜遺伝子治療として世界初の先駆け＋オーファン同時指定
  * 先駆け指定により日本での審査期間が6ヶ月目標に短縮
  * 日本承認予測: 2029年（従来2031年から大幅前倒し）
  * 2026 Macula Society Annual Meeting（2月25-28日）でpost-hoc分析発表

- **SPVN06（SparingVision）**: PRODYGY試験投与完了 - 重要度: 90
  * 2026年2月9日: Phase 1/2 PRODYGY試験の全患者投与完了
  * 33名登録（SPVN06投与27名 + 対照群6名）
  * 初回データ読出し: 2027年予定
  * 2026年中に規制当局とデータ共有開始、2027年ピボタル試験開始目標

- **NPI-001（Nacuity）**: FDA Breakthrough Therapy指定・Phase 1/2陽性データ - 重要度: 85
  * FDA Breakthrough Therapy指定取得（Fast Track + Orphanに加え3つ目の指定）
  * Phase 1/2試験（49名、2年間）: 視覚機能喪失を約30%遅延
  * Usher症候群関連RPで光受容体喪失を50%以上抑制
  * 2026年に確認的試験開始予定
  * Phase更新: Pre-clinical → Phase 1/2

- **OpCT-001（BlueRock/Bayer）**: FDA Orphan Drug指定取得 - 重要度: 80
  * 2026年1月22日: FDA Orphan Drug Designation取得
  * Fast Track + Orphan Drugの二重指定に
  * CLARICO Phase 1/2a試験進行中（54名登録予定）

- **ZM-02（Zhongmou）**: MOON試験詳細結果 - 重要度: 75
  * 36週時点で83%の患者にBCVA ≥0.3 LogMAR改善
  * 平均0.59 LogMAR改善、52週で持続性確認
  * 色覚回復、低照度ナビゲーション能力回復も確認
  * SAE/DLTなし

- **jCells（jCyte）**: 中間結果予定 - 重要度: 70
  * JC02-88 Phase 2試験: 2026年Q1に中間結果予定
  * 主要評価項目: ETDRS 15文字以上の視力改善

### 🆕 新規プログラム
- **DSP-3077（住友ファーマ）**: 他家iPS細胞由来網膜シート
  * 米国Phase 1/2 IND承認（2024年11月）
  * Massachusetts Eye and Earで実施予定
  * 神戸アイセンター病院での臨床研究で2年間の生着・安全性確認済み
  * 新鮮（非凍結）3Dオルガノイド使用

### 🔄 更新されたプログラム詳細
1. **MCO-010（Nanoscope）**: 日本先駆け指定追加、BLA状況更新
2. **OCU400（Ocugen）**: BLA submission H1 2026予定確認
3. **VP-001（PYC）**: FDA alignment meeting（2025年12月）追加
4. **AGTC-501（Beacon）**: LANDSCAPE試験開始、SKYLINE 36ヶ月データ追加、laru-zova正式名称化
5. **OpCT-001（BlueRock）**: Orphan Drug指定追加
6. **NPI-001（Nacuity）**: Breakthrough Therapy指定、Phase 1/2データ追加
7. **SPVN06（SparingVision）**: PRODYGY試験投与完了、RdCVF/RdCVFL詳細追加
8. **ZM-02（Zhongmou）**: MOON試験定量的結果追加
9. **jCells（jCyte）**: 中間結果時期追加
10. **VG901（ViGeneron）**: EMA CTA承認追加

### ✅ 変更なし（既知の情報）
- Keio_Optogenetics, GS030, 4D-125, CTx-PDE6b

### 📈 シミュレーション結果
- アクティブ試験数: 55件
- **最速承認予測（FDA）**: MCO-010 2026年（BLA priority review）
- **日本最速承認予測**: MCO-010 2029年（先駆け指定により大幅短縮）
- **全体中央値**: 2035年（FDA承認）
- **Phase別成功率**: Phase 1: 86.7%, Phase 2: 78.4%, Phase 3: 71.4%

### 2026年1月3日（自動更新）
- **Gemini検索による最新情報更新（/update_rp_info full実行）**
- **build_report.pyの出力先をreport.htmlに変更**（ランディングページindex.htmlとの分離）
- **CSSテンプレート展開バグを修正**

## 網膜色素変性症治療法 最新情報更新サマリー
更新日時: 2026年1月3日

## 📊 更新チェック結果サマリー

- 新規プログラム: 2件（ZM-02、jCells）
- 更新されたプログラム: 7件
- 変更なし: 8件
- 重要な更新: 4件

### 🆕 新規プログラム
- **ZM-02（Zhongmou Therapeutics）**: 遺伝子非特異的光遺伝学療法
  * 2024年10月: FDA Orphan Drug Designation取得
  * 2025年11月: FDA IND承認、米国・中国での多国籍Phase 1/2 PRISM試験開始
  * 中国MOON試験で視覚、移動能力、色覚に改善を確認
- **jCells（jCyte）**: 細胞治療（ファムゼレトセル）
  * 2025年8月: 新Phase 2試験（JC2-088）開始
  * より高用量（880万細胞）を評価
  * FDA RMAT指定取得済み

### 🚨 重要な更新（重要度70以上）
- **AGTC-501（Beacon）**: VISTA試験登録完了、LANDSCAPE試験開始 - 重要度: 90
  * 2025年7月: Phase 2/3 VISTA試験登録完了
  * 2025年12月: Phase 2 LANDSCAPE試験開始（両眼投与安全性評価）
  * EURETINA 2025: DAWN 9+ヶ月、SKYLINE 36ヶ月データで持続的改善確認
  * 12ヶ月トップラインデータ: 2026年下半期予定

- **OCU400（Ocugen）**: Phase 3 liMeliGhT試験登録完了間近 - 重要度: 85
  * 米国約150名、カナダ最大50名登録
  * 2026年上半期: Rolling BLA申請開始予定
  * 2026年Q4: トップラインデータ予定
  * 2027年: 商用化予定

- **VG901（ViGeneron）**: RPDD指定・用量漸増承認 - 重要度: 75
  * 2025年1月: FDA RPDD指定取得、DSMB用量漸増承認
  * Phase 1b試験進行中（ドイツ・テュービンゲン大学、6名登録）
  * NCT06291935として登録

- **Ultevursen（Sepul Bio）**: LUNA試験進行中 - 重要度: 70
  * NCT06627179として登録
  * 2025年11月26日: ClinicalTrials.gov更新
  * 2年間試験、81名登録予定（8歳以上）
  * 米国、英国、オランダで実施

### 🔄 更新されたプログラム詳細
1. **MCO-010（Nanoscope）**: BLA申請進行中、2026年初頭完了予定
2. **OCU400（Ocugen）**: ステータス更新「登録完了間近」、BLA申請タイムライン明確化
3. **VP-001（PYC）**: DINGO延長研究進行中、自然史研究2026年2月完了予定
4. **AGTC-501（Beacon）**: LANDSCAPE試験追加、ステータス「登録完了」に更新
5. **OpCT-001（BlueRock）**: 試験デザイン詳細追加（Phase 1: 12-24名、Phase 2: 最大15名）
6. **VG901（ViGeneron）**: Trial ID追加、RPDD指定・用量漸増情報追加
7. **Ultevursen（Sepul Bio）**: Trial ID追加（NCT06627179）

### ✅ 変更なし（既知の情報）
- MCO-010（BLA進行中）, Keio_Optogenetics, GS030, 4D-125, CTx-PDE6b, AAV-mVChR1, SPVN06, NPI-001, Botaretigene sparoparvovec

### 📈 シミュレーション結果
- アクティブ試験数: 55件
- **最速承認予測（FDA）**: OCU400 2027年（2試験進行中）
- **全体中央値**: 2035年（FDA承認）
- **Phase別成功率**: Phase 1: 86.7%, Phase 2: 78.4%, Phase 3: 71.4%

### 2025年11月17日
- **古いHTML/Markdownファイルの整理（Issue #41対応）**
  - 陳腐なHTMLファイル9個を削除
  - build_report.pyの出力ファイル名をindex_old.htmlからindex.htmlに変更（後にreport.htmlに再変更）
  - プロジェクトの保守性向上とファイル構造の明確化

### 2025年11月7日（自動更新）
- **Web検索による最新情報更新（/update_rp_info full実行）**

## 網膜色素変性症治療法 最新情報更新サマリー
更新日時: 2025年11月7日

## 📊 更新チェック結果サマリー

- 新規プログラム: 0件
- 更新されたプログラム: 5件
- 変更なし: 9件
- 重要な更新: 5件

### 🚨 重要な更新（重要度70以上）
- **MCO-010**: 5年間安全性データと3年間有効性データ発表 - 重要度: 85
  * 持続的な視覚改善を確認
  * BLA提出は2026年初頭に完了予定
  * Priority Review対象
  * ワンタイム・オフィス内注射

- **OCU400**: Phase 3 liMeliGhT試験（NCT06388200）進行中 - 重要度: 90
  * Trial ID更新: NCT05203939 → NCT06388200
  * 登録完了間近
  * 2026年Q4にトップラインデータ予定
  * 2027年に商用化予定

- **VP-001**: Phase 1/2完了、Phase 2/3開始予定 - 重要度: 80
  * Phase 1/2試験（PLATYPUS、WALLABY）完了
  * 安全性良好、視力改善確認
  * 2025年後半にPhase 2/3開始予定
  * FDA Fast Track、RPD指定取得

- **AGTC-501**: VISTA試験グローバル登録中 - 重要度: 85
  * ステータス更新: "Enrollment completed" → "Enrolling globally"
  * 追加規制承認: FDA Fast Track、UK ILAP、EU PRIME
  * Phase 2 DAWN試験で良好な中間結果（2025年5月）

- **OpCT-001**: FDA Fast Track指定、初患者投与完了 - 重要度: 75
  * 2025年2月27日にFDA Fast Track指定取得
  * 2025年7月8日に初患者投与
  * Phase 1/2a CLARICO試験（NCT06789445）進行中
  * 54名登録予定

- **Ultevursen**: Phase 2b LUNA試験進行中 - 重要度: 70
  * 2年間試験、81名登録予定（8歳以上）
  * 米国、英国、オランダで試験実施中
  * 2025年10月2日にClinicalTrials.gov更新

### 🔄 更新されたプログラム詳細
1. **MCO-010（Nanoscope）**:
   - 5年間安全性データと3年間有効性データ追加
   - BLA完了予定を2026年初頭に明記

2. **OCU400（Ocugen）**:
   - Trial ID: NCT05203939 → NCT06388200
   - 2026年Q4トップラインデータ予定追加
   - 2027年商用化予定追加

3. **VP-001（PYC Therapeutics）**:
   - Phase 1/2試験完了情報を詳細化
   - Phase 2/3開始時期を2025年後半と明記

4. **AGTC-501（Beacon）**:
   - ステータス: "Enrollment completed" → "Enrolling globally"
   - Trial IDs拡充: VISTA, SKYLINE, HORIZON, DAWN
   - 規制承認追加: FDA Fast Track, UK ILAP, EU PRIME

5. **OpCT-001（BlueRock）**:
   - FDA Fast Track指定日を明記（2025年2月27日）
   - 初患者投与日を明記（2025年7月8日）
   - Trial ID追加: NCT06789445

6. **Ultevursen（Sepul Bio/Théa）**:
   - 試験詳細追加（2年間、81名、8歳以上）
   - 試験地域情報追加（米国、英国、オランダ）

### ✅ 変更なし（既知の情報）
- NPI-001, Keio_Optogenetics, GS030, 4D-125, CTx-PDE6b, AAV-mVChR1, SPVN06, Botaretigene sparoparvovec, VG901

### 📈 シミュレーション結果
- アクティブ試験数: 55件
- **最速承認予測（FDA）**: OCU400 2027年（2つのトライアル: NCT05203939とNCT06388200）
- **全体中央値**: 2034年（FDA承認）
- **Phase別成功率**: Phase 1: 86.7%, Phase 2: 78.4%, Phase 3: 71.4%

### 2025年10月25日（自動更新）
- **update_latest_info.pyによる自動更新**

## 網膜色素変性症治療法 最新情報更新サマリー
更新日時: 2025年10月25日

## 📊 更新チェック結果サマリー

- 新規プログラム: 0件
- 更新されたプログラム: 4件
- 変更なし: 3件
- 重要な更新: 4件

### 🚨 重要な更新（重要度70以上）
- **MCO-010**: REMAIN試験3年データ発表（2025-10-22）- 重要度: 75
  * 持続的な視覚改善と良好な安全性プロファイルを確認
  * BLA申請の根拠をさらに強化
- **OCU400**: 拡大アクセスプログラム承認・カナダ拡大 - 重要度: 80
  * FDA拡大アクセスプログラム承認（最大75名）
  * カナダ試験拡大承認（最大50名）
  * ClinicalTrials.gov更新: 2025-10-16
- **VP-001**: RPD指定・FDAミーティング完了 - 重要度: 85
  * FDA Rare Pediatric Disease（RPD）指定取得（2025-01）
  * PRVバウチャー取得可能性（$100M+価値）
  * FDAポジティブミーティング（2025-06）
- **AGTC-501**: VISTA試験登録完了・RMAT指定 - 重要度: 90
  * Phase 2/3 VISTA試験登録完了（2025-08）
  * FDA RMAT指定取得（2025-01）
  * 12ヶ月トップラインデータ: 2026-H2予定
  * DAWN試験6ヶ月中間データ良好（2025-05）

### 🔄 更新されたプログラム詳細
1. **MCO-010（Nanoscope）**:
   - 追加: REMAIN試験3年データ（持続的視覚改善）

2. **OCU400（Ocugen）**:
   - 追加: FDA拡大アクセスプログラム（75名）
   - 追加: カナダ試験拡大（50名）
   - 追加: 2025-10-16時点で積極的登録中

3. **VP-001（PYC）**:
   - 追加: FDA RPD指定（2025-01）
   - 追加: FDAミーティング完了（2025-06）
   - 追加: PRVバウチャー対象情報

4. **AGTC-501（Beacon）**:
   - 更新: ステータス "Enrolling" → "Enrollment completed"
   - 追加: 登録完了日（2025-08）
   - 追加: FDA RMAT指定（2025-01）
   - 追加: DAWN試験6ヶ月データ良好（2025-05）
   - 追加: 12ヶ月データ予定（2026-H2）

5. **OpCT-001（BlueRock）**:
   - 追加: 初患者投与完了（2025-07）
   - 追加: 世界初iPSC由来細胞治療

### ✅ 変更なし（既知の情報）
- Ultevursen, Keio_Optogenetics, Botaretigene sparoparvovec

### 📈 シミュレーション結果の変更
- アクティブ試験数: 55件（変更なし）
- 最速承認予測（FDA）: OCU400 2027年（変更なし）
- 全体中央値: 2034年（従来2037年から改善）
- Phase別成功率: Phase 1: 86.7%, Phase 2: 78.4%, Phase 3: 71.4%

### 2025年10月06日（自動更新）
- **update_latest_info.pyによる自動更新**

## 網膜色素変性症治療法 最新情報更新サマリー
更新日時: 2025年10月06日

## 📊 更新チェック結果サマリー

- 新規プログラム: 0件
- 更新されたプログラム: 1件
- 変更なし: 5件
- 重要な更新: 1件

### 🚨 重要な更新
- VP-001: Phase更新 Phase 1/2 → Phase 1 (重要度: 50/100)

### 🔄 更新されたプログラム
- VP-001: Phase 1/2 → Phase 1

### ✅ 変更なし（既知の情報）
- MCO-010, OCU400, AGTC-501, OpCT-001, Botaretigene


### 2025年09月12日（自動更新）
- **update_latest_info.pyによる自動更新**

## 網膜色素変性症治療法 最新情報更新サマリー
更新日時: 2025年09月12日

## 📊 更新チェック結果サマリー

- 新規プログラム: 0件
- 更新されたプログラム: 1件
- 変更なし: 5件
- 重要な更新: 1件

### 🚨 重要な更新
- VP-001: Phase更新 Phase 1/2 → Phase 1 (重要度: 50/100)

### 🔄 更新されたプログラム
- VP-001: Phase 1/2 → Phase 1

### ✅ 変更なし（既知の情報）
- MCO-010, OCU400, AGTC-501, OpCT-001, Botaretigene


### 2025年08月18日（自動更新）
- **update_latest_info.pyによる自動更新**

## 網膜色素変性症治療法 最新情報更新サマリー
更新日時: 2025年08月18日

## 📊 更新チェック結果サマリー

- 新規プログラム: 0件
- 更新されたプログラム: 1件
- 変更なし: 5件
- 重要な更新: 1件

### 🚨 重要な更新
- VP-001: Phase更新 Phase 1/2 → Phase 1 (重要度: 50/100)

### 🔄 更新されたプログラム
- VP-001: Phase 1/2 → Phase 1

### ✅ 変更なし（既知の情報）
- MCO-010, OCU400, AGTC-501, OpCT-001, Botaretigene


### 2025年07月25日（自動更新）
- **update_latest_info.pyによる自動更新**

## 網膜色素変性症治療法 最新情報更新サマリー
更新日時: 2025年07月25日

## 📊 更新チェック結果サマリー

- 新規プログラム: 0件
- 更新されたプログラム: 1件
- 変更なし: 5件
- 重要な更新: 1件

### 🚨 重要な更新
- VP-001: Phase更新 Phase 1/2 → Phase 1 (重要度: 50/100)

### 🔄 更新されたプログラム
- VP-001: Phase 1/2 → Phase 1

### ✅ 変更なし（既知の情報）
- MCO-010, OCU400, AGTC-501, OpCT-001, Botaretigene


### 2025年07月24日（自動更新）
- **update_latest_info.pyによる自動更新**

## 網膜色素変性症治療法 最新情報更新サマリー
更新日時: 2025年07月24日

## 📊 更新チェック結果サマリー

- 新規プログラム: 1件
- 更新されたプログラム: 1件
- 変更なし: 4件
- 重要な更新: 1件

### 🚨 重要な更新
- VP-001: Phase更新 Phase 1/2 → Phase 1 (重要度: 50/100)

### 🆕 新規プログラム
- Botaretigene

### 🔄 更新されたプログラム
- VP-001: Phase 1/2 → Phase 1

### ✅ 変更なし（既知の情報）
- MCO-010, OCU400, AGTC-501, OpCT-001


### 2025年7月24日
- **Gemini Searchを使用した最新情報更新（/update_rp_info full実行）**
  - **新規プログラムの追加（知識ベース12→14プログラムに増加）**:
    - **SPVN06（SparingVision）**: USH2A遺伝子変異向けRNA治療、Phase 1/2試験中
    - **Ultevursen（Sepul Bio/Théa）**: USH2Aエクソン13変異向けアンチセンスオリゴ、Phase 2試験中
  - **既存プログラムの情報更新**:
    - **慶應大学プログラム**: RV-001/レストアビジョン（Restore Vision社）との共同開発情報を追加
  - **シミュレーション結果**:
    - 53件のアクティブな試験を分析
    - OCU400が最速2027年FDA承認見込み（日本は2032年）
    - 全体の中央値は2034年（FDA承認）

### 2025年7月20日
- **最新情報自動更新システムの構築と改善**
  - `scripts/update_latest_info.py`: Web検索、API取得、データ更新を自動化するスクリプトを作成
  - Claude Code用カスタムコマンド `/update_rp_info` を実装（`.claude/commands/`に配置）
  - 3つのモードを実装：`full`（完全更新）、`quick`（レポートのみ）、`check`（確認のみ）
  - YAML front-matterと動的機能（シェルコマンド実行、引数対応）を追加
- **知識ベースシステムの導入**
  - `data/knowledge_base/`: 構造化された治療プログラム情報を保存
  - 既存データとの自動比較機能を実装（重複チェック）
  - 新規・更新・変更なしを自動分類
  - 重要度スコアリング（0-100）で更新の優先度を判定
- **データ比較ユーティリティ**
  - `scripts/utils/data_comparison.py`: Web検索結果と既存データの比較機能
  - 自動的な情報抽出（治療名、Phase、規制承認など）
  - 比較レポートの自動生成
- **更新プロセスの標準化**
  - 週次：`/update_rp_info check` → 新情報の確認のみ
  - 月次：`/update_rp_info check` → 重要な更新があれば `full`
  - 四半期：`/update_rp_info full` → 包括的な更新
  - 臨時：重要ニュース発生時の即時対応

### 2025年6月26日（第5回更新）
- **gemini-searchを使用した2025年最新情報の包括的な更新**
  - **MCO-010（Nanoscope社）**:
    - 2025年6月にFDA段階的BLA申請開始予定（以前の予測より具体的）
    - RESTORE試験の成功と統計的有意性達成を再確認
    - スターガルト病への適応拡大可能性を確認
  - **OCU400（Ocugen社）**:
    - Phase 1/2の2年データで100%（9/9）の患者が改善/維持（2025年1月発表）
    - liMeliGhT Phase 3試験が順調に進行、2025年前半に登録完了予定
    - 2026年中頃にBLA/MAA申請予定（スケジュール通り）
    - EMAからATMP分類と中央審査手続き承認取得（2025年5月）
  - **その他の有望な治療法**:
    - PYC VP-001: 2025年後半にPhase 2/3開始予定
    - Beacon AGTC-501: Phase 2/3 VISTA試験で患者登録中
    - BlueRock OpCT-001: Phase 1/2a実施中、FDA Fast Track指定取得
  - **新規参入**:
    - Nacuity NPI-001（経口薬）がFDA Fast Track指定取得
    - Théa/Sepul Bio ultevursen（RNA治療）がPhase 2b試験中

### 2025年6月26日（第4回更新）
- **MCO-010の最新情報確認（gemini-search使用）**
  - RESTORE試験（NCT04945772）の成功裏の完了を再確認
  - 2025年Q1のFDA BLA申請予定を確認
  - スターガルト病への適応拡大の可能性も判明
  - 遺伝子非依存型（gene-agnostic）アプローチの利点を強調

### 2025年6月27日
- **シミュレーションに日本承認遅延を反映**
  - timeline_sim.pyに日本承認予測機能を追加
  - Luxturna実績（5.5年遅延）に基づく三角分布（3-7年）で遅延をモデル化
  - 全ての治療プログラムで日本承認時期を個別に計算
- **レポート生成コードの更新**
  - 日本承認予測列を追加（中央値と90%信頼区間）
  - 上位5プログラムの詳細な日本承認予測表を生成
  - CDFプロットをFDA承認と日本承認の2つに分割
- **地域差の明確化**
  - 全ドキュメントでFDA承認基準であることを明記
  - 日本での承認は通常3-7年後と強調
  - regional_approval_timeline.htmlで詳細な地域別予測を提供

### 2025年6月26日（第3回更新）
- サイト構成の大幅な見直し
  - 事実（現状）とAI予測を明確に分離
  - `current_status_facts.md` - 確認可能な事実のみ
  - `ai_predictions.md` - AI予測と不確実性を明記
  - 全ページにナビゲーションメニューを追加
- 公開に向けた準備
  - `publication_disclaimer.md` - 包括的な免責事項
  - `publication_checklist.md` - 公開前チェックリスト
  - 医学的助言ではないことを全ページで強調
- HTMLナビゲーションの改善
  - 全8ページ相互リンク実装
  - アクセシビリティ対応維持
  - OGPタグを全ページに追加

### 2025年6月26日（第2回更新）
- **gemini-searchを使用した最新情報の反映**
  - MCO-010: RESTORE試験で統計的有意性達成、2025年Q1にBLA申請予定を確認
  - OCU400: 2年データで100%改善/維持、2026年BLA/MAA申請予定
  - Janssen社 Botaretigene: Phase 3で主要評価項目未達成（2025年5月発表）
  - Biogen BIIB112: 開発中断を確認
- シミュレーションパラメータの更新
  - Janssen社試験の成功率20%に低下
  - MCO-010、OCU400に「high confidence」フラグ追加
- OGPタグをHTML生成コードに追加（SNSシェア対応）

### 2025年6月26日（第1回更新）
- **最新の臨床試験情報を反映した大規模アップデート**
  - MCO-010（Nanoscope社）が2025年初頭にFDA申請、最速2025-2026年承認見込み
  - OCU400（Ocugen社）が2024年Phase 3開始、2026-2027年承認見込み
  - シミュレーションコードに特別処理を追加（Fast Track指定の反映）
- 「現実的なアクション」ドキュメントを最新情報で更新
  - 承認時期予測を2025-2026年に前倒し
  - 変異非依存型治療の進展を強調

### 2025年6月25日
- 「現実的なアクション」ドキュメント（docs/reality_and_actions.md）を大幅改訂
  - 具体的な手順、URL、費用、検索キーワードを追加
  - 各アクションを実行可能なステップに分解
  - 実際の病院名、サービス名を明記
- ChatGPT o3の検証結果に基づいて修正
  - 遺伝子検査費用を10-12万円に更新（パネル検査）
  - タイムラインを2029年以降に調整（より現実的に）
  - 神戸アイセンター病院を追加
- 遺伝子検査費用の負担軽減方法を追加
  - 保険適用、研究参加、段階的アプローチなど5つの方法
  - 予算別の現実的な選択肢を提示
  - 無料検査可能な研究機関をリストアップ
- モンテカルロシミュレーションの改善
  - Phase 3期間を3-5年から4-7年に修正（遺伝子治療に適合）
  - 長期実施中試験の処理ロジックを改善
  - 遺伝子治療固有のリスクを反映