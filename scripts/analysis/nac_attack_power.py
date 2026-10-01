"""M3: NAC Attack(第III相)の設計は、どの大きさの効果なら検出できるか。

問い: 「NACが本当に進行を X% 遅らせるとして、この試験が"効いた"と言える確率は?」
→ 試験が陰性だったとき「効かない」のか「設計が弱くて見えなかった」のかを読む物差し。

設計は登録情報(NCT05537220)とプロトコル要旨のとおり:
  483人 / NAC:偽薬 = 2:1 / 45か月 / EZ幅を9か月ごとに測定 / EZ幅 1500〜8000µm
  主要評価項目 = EZ幅の累積喪失(曲線の上の面積)

ここで置いた仮定(登録情報に無い。感度分析で振る):
  - 進行速度と個人差: USH2A論文に合わせた既定値(median k=0.063/年, CV 0.54)と、その半分の遅い集団
  - 脱落率 15%
  - OCTの測定誤差 SD 0 / 100 / 200 µm
  - 解析は1人1眼・2標本Welch検定(実際の解析はより高性能な可能性が高い=ここの検出力は控えめ側)

スコープ厳守: 出るのは「設計の検出力」。NACが効くかどうかは一切分からない。

実行: PYTHONPATH=. .venv/bin/python scripts/analysis/nac_attack_power.py
"""

from __future__ import annotations

import numpy as np
from scipy import stats

N_TOTAL = 483
RATIO_TRT = 2 / 3
DROPOUT = 0.15
VISITS = np.arange(0, 45 + 1, 9) / 12.0  # 年
W_MIN, W_MAX = 1500.0, 8000.0
MEDIAN_W0, CV_W0 = 3000.0, 0.45
CV_K = 0.54
ALPHA = 0.05
N_TRIALS = 2000


def _ln(median: float, cv: float) -> tuple[float, float]:
    return float(np.log(median)), float(np.sqrt(np.log(1 + cv * cv)))


def sample_w0(rng: np.random.Generator, n: int) -> np.ndarray:
    """選択基準(1500〜8000µm)に入る人だけを集める。"""
    mu, sig = _ln(MEDIAN_W0, CV_W0)
    out = np.empty(0)
    while out.size < n:
        w = rng.lognormal(mu, sig, size=n * 2)
        out = np.concatenate([out, w[(w >= W_MIN) & (w < W_MAX)]])
    return out[:n]


def cumulative_loss(
    rng: np.random.Generator, n: int, median_k: float, effect: float, noise: float
) -> np.ndarray:
    """1人ごとの累積喪失(µm・年)。W0 - W(t) を台形則で積分。"""
    w0 = sample_w0(rng, n)
    mu, sig = _ln(median_k, CV_K)
    k = rng.lognormal(mu, sig, size=n) * (1.0 - effect)
    w = w0[:, None] * np.exp(-k[:, None] * VISITS[None, :])
    if noise > 0:
        w = w + rng.normal(0, noise, size=w.shape)
    loss = w[:, :1] - w
    return np.trapz(loss, VISITS, axis=1)


def power(median_k: float, effect: float, noise: float, seed: int = 20261002) -> float:
    rng = np.random.default_rng(seed)
    n_eval = int(round(N_TOTAL * (1 - DROPOUT)))
    n_trt = int(round(n_eval * RATIO_TRT))
    n_ctl = n_eval - n_trt
    hits = 0
    for _ in range(N_TRIALS):
        trt = cumulative_loss(rng, n_trt, median_k, effect, noise)
        ctl = cumulative_loss(rng, n_ctl, median_k, 0.0, noise)
        t, p = stats.ttest_ind(ctl, trt, equal_var=False)
        if p < ALPHA and t > 0:  # 偽薬のほうが喪失が大きい方向だけを「成功」とする
            hits += 1
    return hits / N_TRIALS


def main() -> None:
    effects = [0.0, 0.10, 0.20, 0.30, 0.40, 0.50]
    print(f"設計: {N_TOTAL}人 2:1 / 45か月 / 測定{len(VISITS)}回 / 脱落{DROPOUT:.0%}")
    print("表の数字 = その効果が本当にあるとき、試験が成功と判定する確率\n")
    for label, mk in [("標準の進行(年6.3%)", 0.063), ("遅い進行(年3.2%)", 0.0315)]:
        for noise in [0.0, 100.0, 200.0]:
            row = [power(mk, e, noise) for e in effects]
            cells = "  ".join(f"{e:>4.0%}:{p:>5.1%}" for e, p in zip(effects, row))
            print(f"{label} 測定誤差{noise:>3.0f}µm | {cells}")
        print()


if __name__ == "__main__":
    main()
