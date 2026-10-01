"""到達確率JSONから日米・2シナリオの帯を持つインラインSVGを生成する。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BIO_URL = "https://go.bio.org/rs/490-EHZ-999/images/ClinicalDevelopmentSuccessRates2011_2020.pdf"


def render_arrival_probability(result=None):
    if result is None:
        result = json.loads((ROOT / "results/arrival_probability.json").read_text())
    years = result["years"]
    idx = years.index(2030)
    low, high = sorted(round(result["groups"]["slow_any"][s]["japan"][idx] * 100)
                       for s in ("rp_history", "general"))
    heading = f"型を問わず進行を遅らせる治療が2030年までに日本で使える確率は {low}〜{high}%"
    svg = ['<svg class="arrival-chart" viewBox="0 0 820 610" role="img" aria-label="進行抑制と視覚再建の到達確率。横軸は年、縦軸は確率。帯は2シナリオの間、日本は太線、米国は細い破線。">']
    rows = []
    for panel, (group, label, color) in enumerate((
        ("slow_any", "進行を遅らせる治療（原因の遺伝子を問わないもの）", "var(--primary-color)"),
        ("restore_any", "見え方を取り戻す治療（重い視力低下のある人向け）", "var(--warning-color)"))):
        top = 40 + panel * 295
        def x(year): return 70 + (year - years[0]) / (years[-1] - years[0]) * 720
        def y(value): return top + 210 - value * 200
        svg.append(f'<text x="70" y="{top-14}" fill="var(--text-primary)" font-size="18">{label}</text>')
        for value in (0, .25, .5, .75, 1):
            yy = y(value)
            svg.append(f'<path d="M70,{yy} H790" stroke="var(--border-color)"/><text x="60" y="{yy+5}" text-anchor="end" fill="var(--text-primary)" font-size="15">{value:.0%}</text>')
        for year in (2026, 2030, 2035, 2040, 2045):
            svg.append(f'<text x="{x(year):.1f}" y="{top+236}" text-anchor="middle" fill="var(--text-primary)" font-size="15">{year}</text>')
        for place in ("us", "japan"):
            curves = result["groups"][group]
            def points(scenario): return [(x(year), y(value)) for year, value in zip(years, curves[scenario][place])]
            lower, upper = points("rp_history"), points("general")
            polygon = " ".join(f"{xx:.2f},{yy:.2f}" for xx, yy in upper + list(reversed(lower)))
            svg.append(f'<polygon points="{polygon}" fill="{color}" opacity="0.13"/>')
            for scenario in ("rp_history", "general"):
                coords = " ".join(f"{xx:.2f},{yy:.2f}" for xx, yy in points(scenario))
                dash = ' stroke-dasharray="6 5"' if place == "us" else ""
                svg.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="{1.5 if place == "us" else 3.5}"{dash}/>')
        for i, year in enumerate(years):
            values = [result["groups"][group][scenario][place][i] * 100
                      for place in ("us", "japan") for scenario in ("rp_history", "general")]
            cells = ''.join(f'<td data-label="{col}">{v:.2f}%</td>' for col, v in zip(
                ("米国・RP過去", "米国・眼科平均", "日本・RP過去", "日本・眼科平均"), values))
            rows.append(f'<tr><th scope="row">{label}・{year}年</th>{cells}</tr>')
    svg.append('</svg>')
    # Markdownの中にも挿入するため、ブロック内に空行を入れない。
    return f'''<section class="arrival-probability content-wrapper" aria-label="少なくとも1つ届く確率">
<h2>{heading}</h2>
<p>小さいほうは網膜色素変性の過去の成績、大きいほうは眼科の薬全体の平均を当てはめた場合です。既存の薬（NAC など）は、最終試験で効果が確認された時点を「使える」と数えています。</p>
<p>帯は2シナリオの幅、太い実線は日本、細い破線は米国です。各年末までに少なくとも1つ届く確率を示します。</p>
<p>下のグラフが高いのは、重い視力低下のある人向けの治療（MCO-010）が日米で承認審査中だからです。物の位置や形が分かるようになることを目指す治療で、失った視力が元どおりになるという意味ではありません。進行を止めたい段階の人に関係するのは上のグラフです。</p>
<div style="overflow-x:auto">{''.join(svg)}</div>
<details><summary>グラフと同じ数字を表で読む（全20年・両シナリオ・日米）</summary>
<div style="overflow-x:auto"><table class="card-layout" aria-label="年末までの到達確率"><thead><tr><th scope="col">治療と年</th><th scope="col">米国・RP過去</th><th scope="col">米国・眼科平均</th><th scope="col">日本・RP過去</th><th scope="col">日本・眼科平均</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></details>
<p>出典: <a href="{BIO_URL}">BIO 眼科領域の段階通過率</a>、<a href="https://www.nichigan.or.jp/Portals/0/resources/member/guideline/nggz-2025-063.pdf">網膜色素変性診療ガイドライン2026 CQ1</a>。相関0.5は仮定値です。日本の遅れはルクスターナ1件を参考にしています。</p>
</section>'''


def arrival_chart_css():
    return ".arrival-chart { display:block; width:100%; min-width:560px; height:auto; } .arrival-probability summary { cursor:pointer; }"
