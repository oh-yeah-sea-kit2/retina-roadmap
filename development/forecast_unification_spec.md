# 予測の一本化と現実寄りへの修正 — 実装仕様（2026-10-02）

対象リポジトリ: `/Users/kyohei/workspace/retina-roadmap`（ここ以外は読むだけ。書き込み禁止）。
実行は `.venv/bin/python`、`PYTHONPATH=.`。HTML は手で編集せず生成元（`src/reporting/*.py`、`docs/content/**/*.md`）を直して再生成する。
git の commit / push / ブランチ操作はしない。`.github/` は触らない。`data/raw/` は変更しない。

## 背景（なぜ直すか）

今の成功確率（Phase 1: 86% / Phase 2: 78% / Phase 3: 71%）は、ClinicalTrials.gov 上で「中止されずに完了した試験の割合」が元で、「効果が確認されて次の段階へ進んだ割合」ではない。そのため承認確率が高く出すぎている。
別に作った手元の台帳（`/Users/kyohei/workspace/rp-research/tracker/`。`forecast.py` と `watchlist.json` を参考に読んでよい）では、次の前提で計算していた。これをサイトに取り込み、サイトを唯一の正とする。

- 段階ごとの通過確率: BIO「Clinical Development Success Rates 2011–2020」眼科領域（Phase 1→2: 71.6% / Phase 2→3: 35.5% / Phase 3→申請: 51.2% / 申請→承認: 91.1%）。出典 https://go.bio.org/rs/490-EHZ-999/images/ClinicalDevelopmentSuccessRates2011_2020.pdf
- 網膜色素変性の過去の成績: 日本眼科学会「網膜色素変性診療ガイドライン2026」CQ1 に挙がる、進行抑制を狙った比較試験7系統（ビタミンA、ルテイン/DHA/ビタミンE、カルシウム拮抗薬、分岐鎖アミノ酸、ウノプロストン、CNTF、バルプロ酸）で明確な成功は0。ラプラスの継起則で (0+1)/(7+2)=11.1%。出典 https://www.nichigan.or.jp/Portals/0/resources/member/guideline/nggz-2025-063.pdf
- 偽薬と比べる中間段階の試験を経ずに最終段階へ進んだ薬（NAC）は、Phase 3 の通過確率に Phase 2 の通過確率も掛ける（0.355×0.512≒18%）
- 進行を遅らせる治療どうしは当たり外れが連動する（相関 0.5。値は仮定）

## 1. 成功確率を2本立てにする（config と sim）

`config/simulation_params.yaml`
- `phase_historical_success_rates` を BIO 眼科の値に置き換える（PHASE1 0.716 / PHASE2 0.355 / PHASE3 0.512）。`success_rate_policy` の `source_label` / `source_url` / `note` も BIO 出典に合わせて書き直す。「完了率」は参考値として残してよいが「成功率」と呼ばない。
- 新設 `regulatory_approval_success_rate: 0.911`（申請→承認）。まだ承認されていない全プログラムに最後のゲートとして掛ける。
- 新設 `success_rate_scenarios`:
  - `general`（眼科の薬の平均並み）: 上記そのまま
  - `rp_history`（網膜色素変性の過去の成績並み）: 進行を遅らせる治療（知識ベースの `message_design.axis` が "A" のプログラムに属する試験）の PHASE3 だけ 0.111 に置き換える。それ以外は general と同じ
- 新設 `slow_progression_correlation: 0.5`（コメントで「仮定値」と明記）
- `display_cap: 0.85` は廃止せず 0.911 に上げる（申請済みで残りが審査だけのプログラムの上限）。
- `programs` の個別設定:
  - MCO-010: 申請受理済みなので成功確率は `regulatory_approval_success_rate` だけ（Phase のゲートを掛けない）。`success_rate: 0.911`
  - AGTC-501: 最終試験成功・申請前。`success_rate: 0.85` のまま（コメントはそのまま）
  - Botaretigene: `success_rate: 0.5` のまま
  - 新設 `NAC Attack`（`match_fields.nct_ids: ["NCT05537220"]`）: `skipped_controlled_phase2: true`。general では PHASE2×PHASE3、rp_history では min(0.111, その値)。既存薬なので申請・承認ゲートは掛けず、「最終試験で効果が確認された時点」を到達とする（`generic: true`）。日本の遅れは 0
- 遺伝子治療の Phase 3 ×0.9 の既存ルールは残す。

`src/ingest/parameters.py` / `src/sim/timeline_sim.py`
- 上の設定を読み、`results/forecasts.csv` は `general` シナリオで従来どおり出す（列は増やしてよいが既存列名は変えない）。新しい列 `rp_history_cumulative_approval_probability` を追加。
- 乱数 seed 固定の再現性は保つ。

## 2. 「少なくとも1つ届く確率」を出す（新規 `src/sim/arrival_probability.py`）

知識ベース `data/knowledge_base/clinical_programs.json` を唯一の入力にする（試験単位ではなくプログラム単位。同じ薬の複数試験を二重に数えない）。

- 各プログラムに構造化ブロック `forecast` を追加する（臨床段階のプログラムだけ。前臨床は付けない）:
  `{"stage": "P1"|"P2"|"P3"|"filed", "readout": "YYYY-MM"|null, "generic": bool, "japan_lag": "none"|"default"|"sakigake", "skipped_controlled_phase2": bool, "not_started": bool, "group": "slow"|"restore"|"gene"}`
  - 初期値は `/Users/kyohei/workspace/rp-research/tracker/watchlist.json` の同じ薬から写す（名前の対応: nac→NAC Attack, ocu400→OCU400, npi001→NPI-001, spvn06→SPVN06, pitava→SENTAN-PVS-NP, jcell→jCells, mco010→MCO-010, rv001→RV-001, dsp3077→DSP-3077, opct001→OpCT-001, rpgr_bota→Botaretigene sparoparvovec, rpgr_agtc→AGTC-501, ush2a_ulte→Ultevursen, prpf31_vp001→VP-001）。watchlist に無い臨床段階のプログラム（SPVN20, VG901, ZM-02, RTx-015, GS030, 4D-125, CTx-PDE6b など）は、知識ベースの `current_phase`・`trial_ids` と `data/` 内の取得済み試験データ（主要評価の完了予定日）から埋める。埋められない項目は null にし、何を null にしたか報告する。
  - `group` は `message_design.axis`（A=slow、B寄り/中間の視覚再建・細胞=restore、型特異=gene）と `genotype_scope_key` から決める。OCU400 は slow（型不問）として扱う。
  - watchlist にあるミノサイクリン第3相（中国、NCT07082855）は知識ベースに無い。新規プログラムとして追加する（`message_design` は NAC Attack を手本に、軸A・型不問・「中国のみ・募集開始前・薬そのものは日本にある」）。
- 計算は tracker の `forecast.py` と同じ（20000回・seed 固定・2シナリオ・`not_started` は後ろ倒し・slow どうしは相関 `slow_progression_correlation` で連動・`generic` は最終試験の陽性で到達・日本の遅れは `japan_lag` に応じて 0 / `japan_delay_years` / `japan_delay_years_sakigake`）。通過確率と所要年数は config から読む（所要年数は BIO 眼科: P1 2.1年 / P2 2.9年 / P3 3.4年 / 審査 1.3年 を `config` に `stage_duration_years_bio` として追加）。
- 出力 `results/arrival_probability.json`: 2026〜2045年の各年末について、`slow_any`（group=slow かつ型不問）と `restore_any`（group=restore）× 2シナリオ × 米国/日本 の「その年までに少なくとも1つ届いている確率」。プログラムごとの到達確率と到達年の中央値・10〜90%幅も。
- `scripts/` の月次チェックから呼ばれる必要はない。`src/sim/timeline_sim.py` の `main()` の最後で呼ぶ。

## 3. サイトへの表示

- ランディングページ（`src/reporting/build_landing_page.py`）とレポート（`build_report.py`）の予測の冒頭に、帯グラフ（横軸 年、縦軸 確率。2シナリオの間を帯で塗る。日本=太線、米国=細い破線）を1枚追加する。画像ではなくインライン SVG で出し、色は CSS 変数、ライト/ダーク両対応、`aria-label` と、同じ数字の表（スクリーンリーダー用、`<details>` に畳んでよい）を付ける。
  - 見出し文: 「型を問わず進行を遅らせる治療が2030年までに日本で使える確率は X〜Y%」（X,Y は arrival_probability.json の値を整数に丸める）。
  - その下に1〜2文で、小さいほうは網膜色素変性の過去の成績、大きいほうは眼科の薬全体の平均を当てはめた場合であること、既存の薬（NAC など）は最終試験で効果が確認された時点を「使える」と数えていることを書く。
- 既存の「予測年の読み方」「プログラム別予測表」は残すが、成功確率の列は新しい値になる。表の注記に出典（BIO）を書く。
- `docs/content/main/reality_and_actions.md` の次の記述は誤りなので書き直す:
  「Phase 3成功率71.4%は、一般的な医薬品（50%）より高い」「これはRP試験127件の実データから算出」「これは遺伝子治療技術の成熟と、希少疾患への規制緩和が要因」
  → 「これまでの71%は『試験が中止されずに完了した割合』で、効果が確認された割合ではなかった。2026年10月から、眼科の薬の実績（最終試験の通過率は約51%）と、網膜色素変性の過去の成績（進行を遅らせる比較試験は7系統で成功0）の2本立てに改めた」という趣旨で。見出し（その箇条書きの親）も実態に合わせる。
- `docs/content/medical/for_doctor_checklist.md` の「Phase 3成功率71.4%は妥当か？」も新しい前提に合わせて書き直す。
- シミュレーション方法のページ（`build_simulation_methodology_html.py` とその元）に、前提の変更（何を・なぜ・出典）と、モデルの限界（前例が少ない、相関0.5は仮定、日本の遅れの前例は1件）を書く。
- 同じページに「NAC の最終試験はどの大きさの効果なら見逃さないか」の小節を追加する。数字は `/Users/kyohei/workspace/rp-research/simulator/README.md` の M3 の結果を写す（本当の効果が進行30%抑制以上なら成功判定の確率は95%以上、最悪条件でも69%。20%抑制だと36〜86%。10%抑制はほぼ見逃す）。仮定（進行速度の個人差は USH2A 論文の較正値、脱落15%、1人1眼の単純な検定）も書く。計算スクリプトは `/Users/kyohei/workspace/rp-research/simulator/scripts/m3_nac_attack_power.py` を `scripts/analysis/nac_attack_power.py` として写す（依存は numpy と scipy。requirements.txt に無ければ追加）。
- 更新履歴（`data/knowledge_base/update_history.json`）に 2026-10-02 付で「予測の前提を変更」の項目を1件追加する。

## 4. テスト

- 既存テストのうち、古い成功率の値を固定しているものは新しい値に直す。
- 追加: (a) arrival_probability が seed 固定で再現する (b) 年について単調非減少 (c) rp_history ≤ general (d) 相関を 0→0.9 にすると slow_any の最終確率が下がる (e) 同じ薬の複数試験を二重に数えない（OCU400 の試験が2本あっても1プログラム） (f) `skipped_controlled_phase2` で確率が下がる (g) 生成されたランディングページに見出し文と SVG が入っている。
- `docs/public` の全 HTML が `check-contrast` に合格するテスト（既にあるはず）を壊さない。

## 5. 再生成と完了条件

1. `.venv/bin/python src/ingest/parameters.py` → `src/sim/timeline_sim.py` → `src/reporting/build_report.py` → `src/reporting/build_updates_page.py`（＋方法ページなど個別の生成スクリプト）を実行して全ページを再生成
2. `.venv/bin/python -m pytest tests/ -q` 全件成功
3. `check-contrast docs/public/<page>.html` が全ページ合格
4. CLAUDE.md（リポジトリ内）のアーキテクチャ説明に新しいモジュールと前提を追記
5. 報告: 変更ファイル一覧／新旧の成功確率／見出しの X〜Y の値／slow_any・restore_any の 2030・2035・2045 年の値（両シナリオ・日米）／主要プログラム（MCO-010, OCU400, AGTC-501, NAC Attack）の新旧の承認確率と中央値年／null にした項目／通せなかった工程
