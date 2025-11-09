---
title: "【修正】JRPSの「無料」表記の誤解を防ぐ"
labels: documentation, high-priority
---

## 📋 問題の概要

`docs/content/accessibility/accessible_summary.md`（音声読み上げ対応版）で、JRPSとMy Retina Trackerが連続して記載されており、「無料」がMy Retina Trackerのみを指していることが不明瞭です。

患者・ご家族からのフィードバックで、JRPSは年会費5,000円がかかるにも関わらず、「無料」と誤解される可能性があるとの指摘を受けました。

## 🎯 修正内容

### 修正対象ファイル
- `docs/content/accessibility/accessible_summary.md`

### 修正案

**現在の記載（109行目付近）:**
```markdown
**日本の登録先**：
1. JRPS（日本網膜色素変性症協会）
   - ウェブサイト：jrps.org
   - 年会費：5,000円
   - 電話：03-5753-5156

**海外の登録先**：
1. My Retina Tracker（マイ レティナ トラッカー）
   - ウェブサイト：myretinatracker.org
   - 費用：無料
   - 日本語非対応（英語のみ）
```

**修正後:**
```markdown
**日本の登録先**：
1. JRPS（日本網膜色素変性症協会）
   - ウェブサイト：jrps.org
   - 年会費：5,000円（※有料会員制）
   - 電話：03-5753-5156
   - メリット：治験情報、医療講演会、患者交流会

**海外の登録先（無料）**：
1. My Retina Tracker（マイ レティナ トラッカー）
   - ウェブサイト：myretinatracker.org
   - 費用：無料
   - 日本語非対応（英語のみ）
```

## ✅ チェックリスト

- [ ] `accessible_summary.md`を修正
- [ ] HTMLを再生成（`python src/reporting/build_report.py`）
- [ ] 生成されたHTMLで表示を確認
- [ ] コミット & プッシュ

## 📌 優先度

**高**: 患者・ご家族の誤解を防ぐため、早急な修正が必要

## 🔗 関連情報

患者・ご家族からのLINEフィードバックに基づく改善
