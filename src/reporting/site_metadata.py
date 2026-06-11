#!/usr/bin/env python3
"""サイト全体で共有するビルド日時とデータ取得日のメタデータ。"""

from __future__ import annotations

import json
import re
import csv
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METADATA_PATH = PROJECT_ROOT / "data" / "knowledge_base" / "site_metadata.json"
LAST_CHECK_PATH = PROJECT_ROOT / "data" / "knowledge_base" / "last_check.json"
DEFAULT_SUCCESS_RATE_CAP = 0.85


def _format_date_jp(dt: datetime) -> str:
    return f"{dt.year}年{dt.month}月{dt.day}日"


def _format_datetime_jp(dt: datetime) -> str:
    return f"{dt.year}年{dt.month:02d}月{dt.day:02d}日 {dt.hour:02d}:{dt.minute:02d}"


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _latest_snapshot_date(kind: str) -> str | None:
    if kind == "clinical_trials":
        files = (PROJECT_ROOT / "data" / "raw" / "clinical_trials").glob("*.json")
        names = [path.stem for path in files if re.fullmatch(r"\d{8}", path.stem)]
    else:
        files = (PROJECT_ROOT / "data" / "raw" / "literature").glob("pubmed_*.json")
        names = [path.stem.replace("pubmed_", "") for path in files
                 if re.fullmatch(r"pubmed_\d{8}", path.stem)]

    if not names:
        return None
    latest = max(names)
    return f"{latest[:4]}-{latest[4:6]}-{latest[6:8]}"


def _load_last_check() -> dict[str, Any]:
    if not LAST_CHECK_PATH.exists():
        return {}
    return json.loads(LAST_CHECK_PATH.read_text(encoding="utf-8"))


def create_build_metadata(now: datetime | None = None) -> dict[str, Any]:
    """ビルド時刻をSSOTとして保存する。"""
    build_dt = (now or datetime.now()).astimezone()
    last_check = _load_last_check()

    metadata = {
        "build_datetime": build_dt.isoformat(timespec="seconds"),
        "site_last_updated": _format_date_jp(build_dt),
        "site_last_updated_datetime": _format_datetime_jp(build_dt),
        "data_check_datetime": last_check.get("last_check_date"),
        "data_check_date": None,
        "clinical_trials_snapshot_date": _latest_snapshot_date("clinical_trials"),
        "pubmed_snapshot_date": _latest_snapshot_date("literature"),
    }

    check_dt = _parse_datetime(metadata["data_check_datetime"])
    if check_dt is not None:
        metadata["data_check_date"] = _format_date_jp(check_dt)

    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    METADATA_PATH.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return metadata


def load_build_metadata(create_if_missing: bool = True) -> dict[str, Any]:
    """保存済みメタデータを読み込む。なければ必要に応じて作る。"""
    if METADATA_PATH.exists():
        return json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    if create_if_missing:
        return create_build_metadata()
    return {}


def render_metadata_placeholders(text: str, metadata: dict[str, Any] | None = None) -> str:
    """Markdown中のメタデータプレースホルダを置換する。"""
    metadata = metadata or load_build_metadata()
    clinical_snapshot = metadata.get("clinical_trials_snapshot_date") or ""
    pubmed_snapshot = metadata.get("pubmed_snapshot_date") or clinical_snapshot

    replacements = {
        "{{ site_last_updated }}": metadata.get("site_last_updated", ""),
        "{{ site_last_updated_datetime }}": metadata.get("site_last_updated_datetime", ""),
        "{{ data_check_date }}": metadata.get("data_check_date", ""),
        "{{ clinical_trials_snapshot_date }}": clinical_snapshot,
        "{{ pubmed_snapshot_date }}": pubmed_snapshot,
    }
    for key, value in replacements.items():
        text = text.replace(key, value)
    return text


def update_readme_badge(metadata: dict[str, Any] | None = None) -> None:
    """READMEのLast Updatedバッジをビルド日で更新する。"""
    metadata = metadata or load_build_metadata()
    readme_path = PROJECT_ROOT / "README.md"
    if not readme_path.exists():
        return

    build_dt = _parse_datetime(metadata.get("build_datetime"))
    if build_dt is None:
        return

    badge_date = f"{build_dt.year:04d}--{build_dt.month:02d}--{build_dt.day:02d}"
    content = readme_path.read_text(encoding="utf-8")
    new_content = re.sub(
        r"Last%20Updated-[0-9]{4}--[0-9]{2}--[0-9]{2}-blue",
        f"Last%20Updated-{badge_date}-blue",
        content,
    )
    if new_content != content:
        readme_path.write_text(new_content, encoding="utf-8")


def update_public_html_metadata(public_dir: Path,
                                metadata: dict[str, Any] | None = None) -> None:
    """生成済みHTML内の更新日ラベルをSSOTに揃える。"""
    metadata = metadata or load_build_metadata()
    site_date = metadata.get("site_last_updated", "")
    site_datetime = metadata.get("site_last_updated_datetime", "")
    clinical_snapshot = metadata.get("clinical_trials_snapshot_date", "")

    replacements = [
        (r"最終更新: \d{4}年\d{1,2}月\d{1,2}日", f"最終更新: {site_date}"),
        (r"最終更新日：\d{4}年\d{1,2}月\d{1,2}日", f"最終更新日：{site_date}"),
        (r"最終更新：\d{4}年\d{1,2}月\d{1,2}日", f"最終更新：{site_date}"),
        (r"生成日時: \d{4}年\d{1,2}月\d{1,2}日 \d{2}:\d{2}",
         f"生成日時: {site_datetime}"),
        (r"生成日時: \d{4}年\d{2}月\d{2}日 \d{2}:\d{2}",
         f"生成日時: {site_datetime}"),
        (r"データ取得日: \d{4}年\d{1,2}月\d{1,2}日",
         f"データ取得日: {clinical_snapshot}"),
        (r"データ取得日</strong>: \d{4}年\d{1,2}月\d{1,2}日",
         f"データ取得日</strong>: {clinical_snapshot}"),
        (r"取得日</strong>: \d{4}年\d{1,2}月\d{1,2}日",
         f"取得日</strong>: {clinical_snapshot}"),
        (r"ClinicalTrials\.gov（\d{4}年\d{1,2}月\d{1,2}日時点）",
         f"ClinicalTrials.gov（{clinical_snapshot}時点）"),
        (r"https://jrct\.niph\.go\.jp/?", "https://jrct.mhlw.go.jp/"),
    ]

    for html_file in public_dir.glob("*.html"):
        content = html_file.read_text(encoding="utf-8")
        new_content = content
        for pattern, replacement in replacements:
            new_content = re.sub(pattern, replacement, new_content)

        if html_file.name == "index.html" and "データ取得:" not in new_content:
            new_content = new_content.replace(
                "データソース: ClinicalTrials.gov, PubMed |",
                f"データソース: ClinicalTrials.gov, PubMed | データ取得: {clinical_snapshot} |",
            )

        if html_file.name == "detailed_analysis.html":
            new_content = sync_detailed_analysis_forecast_table(new_content)
            new_content = new_content.replace(
                "色の濃さは成功確率を示す。",
                "色の濃さは累積承認確率を示す。",
            )

        new_content = remove_stale_mco_010_timeline_claims(new_content)
        new_content = align_sprint3_message_design(new_content)

        if new_content != content:
            html_file.write_text(new_content, encoding="utf-8")


def remove_stale_mco_010_timeline_claims(html_content: str) -> str:
    """MCO-010の旧い2025-2026承認表現を暫定的に外す。"""
    stale_range = "2025" + "-2026"
    stale_late = "2025" + "年後半"
    stale_q1 = "2025" + "年第1四半期"
    replacements = {
        "質問1：本当に" + "2025" + "年に治療法が出るのですか？":
            "質問1：本当に近いうちに治療法が出るのですか？",
        "MCO-010は" + stale_q1 + "（1月から3月）にFDAに申請予定です。順調にいけば最も早い候補前半に承認される可能性があります。ただし、予期せぬ問題で遅れる可能性もあります。":
            "MCO-010は有力候補の一つですが、承認時期は申請・審査状況で変わります。最新の予測年は詳細レポートの再シミュレーション結果を確認してください。",
        "最速" + stale_range + "年の承認見込み": "最新の再シミュレーション結果を掲載",
        "最速で2025年後半から2026年に最初の治療法が承認される可能性があります":
            "最も早い候補でも承認時期は不確実で、最新の再シミュレーション結果を確認する必要があります",
        stale_late + "から" + "2026" + "年": "最も早い候補",
        stale_q1 + "（1月から3月）にFDAに申請予定です。順調にいけば" + stale_late + "から" + "2026" + "年前半に承認される可能性があります。ただし、予期せぬ問題で遅れる可能性もあります。":
            "有力候補の一つですが、承認時期は申請・審査状況で変わります。最新の予測年は詳細レポートの再シミュレーション結果を確認してください。",
        "最速" + stale_range + "年の承認が現実的に！（最新情報）":
            "最も早い候補でも、承認時期は再シミュレーション結果で幅を持って見る",
        stale_q1 + "にFDA申請、最速" + stale_late + "〜" + "2026" + "年承認見込み":
            "有力候補の一つ。承認時期は申請・審査状況で変わるため、最新の予測年は詳細レポートを参照",
        "MCO-010の" + stale_range + "年承認予測は現実的か？":
            "MCO-010の最新再シミュレーション結果と前提は現実的か？",
        "承認予測：" + stale_late + "～" + "2026" + "年":
            "承認予測：最新の再シミュレーション結果を参照",
        "根拠：RESTORE試験で統計的有意性達成、2025年Q1 BLA申請予定":
            "根拠：RESTORE試験で統計的有意性達成。申請・審査状況により時期は変動",
        "現在の予測（最速2027年）が、AI活用により<strong class=\"highlight\">2025-2026年に前倒し</strong>される可能性があります。":
            "現在の予測（最速2027年）は、AI活用で前倒しされる可能性がありますが、具体年は再シミュレーション結果を優先します。",
        "OCU400: 2027年 → <strong>2025年後半</strong>":
            "OCU400: 2027年 → <strong>前倒しの可能性</strong>",
    }
    for old, new in replacements.items():
        html_content = html_content.replace(old, new)
    return html_content


def align_sprint3_message_design(html_content: str) -> str:
    """静的統合ページの古い単一年・100%表現をSprint 3の2軸表現に寄せる。"""
    replacements = {
        "最も期待される治療法TOP5": "主な治療法の読み方",
        "2025年7月時点で最も承認に近い治療プログラムです：":
            "治療は「進行を遅らせる」「視覚再建・根治を目指す」「中間」に分けて読みます：",
        "最有力候補": "A/B中間",
        "最も早い治療法は2027年頃に米国で、2032年頃に日本で</strong>承認される見込みです。これはOCU400という遺伝子治療薬の予測です。ただし、これは予測であり、早まることも遅れることもあります。":
            "「進行を遅らせる」治療なら数年内に選択肢が出る可能性があります。一方、「視力を取り戻す・根治を目指す」治療は10〜20年の長期目標です。</strong> 原因遺伝子と病期によって現実的な候補が変わります。",
        "Phase 3実施中、2年データで100%改善/維持":
            "Phase 3組入れ完了、トップラインは2027年Q1予定",
        "対象</strong>: RPGRとRHO以外の遺伝子変異を持つ患者":
            "対象</strong>: RHOアームと広範RPアーム。最終的な対象は承認ラベルで決定",
        "承認予測</strong>: 米国2026年、日本2031年":
            "承認予測</strong>: 最新の再シミュレーション結果を詳細レポートで確認",
        "現状</strong>: 2025年6月FDA申請開始、Fast Track指定":
            "現状</strong>: BLA rolling submission進行中、Fast Track指定",
        "現状</strong>: 2025年後半Phase 2/3開始予定":
            "現状</strong>: 将来試験を計画中",
        "最速承認予測：2026年（MCO-010、米国FDA基準）":
            "早い候補の中央値：詳細レポートの再シミュレーション結果を参照",
        "Phase別成功率：Phase 1: 86.2%、Phase 2: 78.4%、Phase 3: 71.4%":
            "Phase別ヒストリカル成功率：Phase 1: 85%、Phase 2: 78%、Phase 3: 71%",
        "現在アクティブな試験：54件（2025年7月時点）":
            "現在アクティブな試験：最新レポートの再集計値を参照",
        "2026年（95% CI: 2025-2027）":
            "2027年（再シミュレーション中央値）",
        "2027年（95% CI: 2026-2029）":
            "2027年（再シミュレーション中央値）",
        "2年間データで100%改善/維持（n=9）、RMAT指定取得":
            "Phase 3組入れ完了、RMAT指定取得。EAPは新規アクセス可否を要確認",
        "OCU400</strong>：2年データで100%改善/維持を確認":
            "OCU400</strong>：Phase 3組入れ完了、トップラインは2027年Q1予定",
        "Janssen Botaretigene</strong>：Phase 3で主要評価項目未達成":
            "Botaretigene/bota-vec</strong>：MeiraGTxが取得し、申請準備中（主要評価未達の不確実性あり）",
        "Nacuity NPI-001がFast Track指定取得":
            "Nacuity NPI-001がFDA Breakthrough Therapy指定取得",
        "<td>MCO-010</td>\n                            <td>2026年</td>\n                            <td><strong>2031年</strong></td>\n                            <td>+5年</td>":
            "<td>MCO-010</td>\n                            <td>2027年</td>\n                            <td><strong>2029年</strong></td>\n                            <td>+2年程度</td>",
        "OCU400: 2027年 → <strong>2026年前半</strong>":
            "OCU400: 2027年 → <strong>前倒しの可能性</strong>",
    }
    for old, new in replacements.items():
        html_content = html_content.replace(old, new)
    return html_content


def _load_forecast_rows() -> dict[str, dict[str, str]]:
    forecast_path = PROJECT_ROOT / "results" / "forecasts.csv"
    if not forecast_path.exists():
        return {}

    rows: dict[str, dict[str, str]] = {}
    with forecast_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows[row.get("NCTId", "")] = row
    return rows


def _load_forecast_probabilities() -> dict[str, float]:
    probabilities: dict[str, float] = {}
    for nct_id, row in _load_forecast_rows().items():
        if not nct_id:
            continue
        try:
            probabilities[nct_id] = float(
                row.get("cumulative_approval_probability")
                or row.get("success_rate")
                or 0.0
            )
        except (TypeError, ValueError):
            continue
    return probabilities


def sync_detailed_analysis_forecast_table(html_content: str) -> str:
    """古い詳細分析ページの予測表を最新CSVに同期する。"""
    from bs4 import BeautifulSoup

    rows = _load_forecast_rows()
    soup = BeautifulSoup(html_content, "html.parser")

    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        if "NCT番号" not in headers:
            continue

        def idx(name: str) -> int | None:
            try:
                return headers.index(name)
            except ValueError:
                return None

        nct_index = idx("NCT番号")
        probability_index = idx("成功確率")
        if probability_index is not None:
            table.find_all("th")[probability_index].string = "累積承認確率（残フェーズ）"
        elif "累積承認確率（残フェーズ）" in headers:
            probability_index = idx("累積承認確率（残フェーズ）")
        fda_index = idx("FDA承認予測")
        japan_index = idx("日本承認予測")
        ci_index = idx("95% CI")

        for table_row in table.find_all("tr")[1:]:
            cells = table_row.find_all(["td", "th"])
            if nct_index is None or len(cells) <= nct_index:
                continue
            nct_id = cells[nct_index].get_text(strip=True)
            forecast = rows.get(nct_id)
            if not forecast:
                continue

            if probability_index is not None and len(cells) > probability_index:
                try:
                    prob = float(
                        forecast.get("cumulative_approval_probability")
                        or forecast.get("success_rate")
                        or 0.0
                    )
                    cells[probability_index].string = f"{prob:.1%}"
                except ValueError:
                    pass
            if fda_index is not None and len(cells) > fda_index:
                try:
                    cells[fda_index].string = f"{float(forecast['median_approval_year']):.0f}年"
                except (KeyError, ValueError):
                    pass
            if japan_index is not None and len(cells) > japan_index:
                try:
                    cells[japan_index].string = f"{float(forecast['japan_median_approval_year']):.0f}年"
                except (KeyError, ValueError):
                    pass
            if ci_index is not None and len(cells) > ci_index:
                try:
                    lo = float(forecast["pct10_approval_year"])
                    hi = float(forecast["pct90_approval_year"])
                    cells[ci_index].string = f"{lo:.0f}-{hi:.0f}"
                except (KeyError, ValueError):
                    pass

    return str(soup)


def sync_detailed_analysis_probabilities(html_content: str) -> str:
    """古い詳細分析ページの成功確率セルを最新CSVに同期する。"""
    from bs4 import BeautifulSoup

    probabilities = _load_forecast_probabilities()
    soup = BeautifulSoup(html_content, "html.parser")

    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        if "成功確率" not in headers:
            continue

        probability_index = headers.index("成功確率")
        headers[probability_index] = "累積承認確率（残フェーズ）"
        table.find_all("th")[probability_index].string = headers[probability_index]

        for row in table.find_all("tr")[1:]:
            cells = row.find_all(["td", "th"])
            if len(cells) <= probability_index:
                continue

            nct_id = None
            for cell in cells:
                match = re.search(r"NCT\d{8}", cell.get_text(" ", strip=True))
                if match:
                    nct_id = match.group(0)
                    break

            if nct_id in probabilities:
                probability = probabilities[nct_id]
            else:
                current_text = cells[probability_index].get_text(strip=True)
                match = re.search(r"(\d+(?:\.\d+)?)%", current_text)
                if not match:
                    continue
                probability = float(match.group(1)) / 100

            probability = min(DEFAULT_SUCCESS_RATE_CAP, max(0.0, probability))
            cells[probability_index].string = f"{probability:.1%}"

    return str(soup)
