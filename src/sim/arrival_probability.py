"""知識ベースのプログラム単位で、少なくとも1つ届く確率を計算する。

tracker/forecast.py の共通乱数・潜在正規相関・期間モデルを移植。
試験データは読まない。同じプログラムに何本の試験があっても1回だけ数える。
"""
from __future__ import annotations

import calendar
from datetime import date
import json
import math
from pathlib import Path
import random

import yaml

ROOT = Path(__file__).resolve().parents[2]
STAGES = ("P1", "P2", "P3", "filed")
SCENARIOS = ("general", "rp_history")
YEARS = list(range(2026, 2046))


def decimal_year(day: date) -> float:
    start = date(day.year, 1, 1)
    return day.year + (day - start).days / (366 if calendar.isleap(day.year) else 365)


def month_end(value: str | None) -> date | None:
    if value is None:
        return None
    year, month = map(int, value.split("-"))
    return date(year, month, calendar.monthrange(year, month)[1])


def is_gene_therapy(program: dict) -> bool:
    text = program.get("modality", "").lower()
    return any(word in text for word in ("gene", "aav", "optogenetic"))


def program_config(name: str, config: dict) -> dict:
    return next((value for key, value in config.get("programs", {}).items()
                 if key == name or value.get("program_name") == name), {})


def stage_probabilities(forecast: dict, config: dict, *, scenario: str = "general",
                        gene_therapy: bool = False, override_rate: float | None = None,
                        slow: bool | None = None) -> dict[str, float]:
    """共通の段階ゲート。申請済みは審査だけ、既存薬は最終試験まで。"""
    stage = forecast["stage"]
    generic = forecast.get("generic", False)
    if generic and stage == "filed":
        raise ValueError("既存薬の到達点は最終試験の陽性です")
    stages = STAGES[STAGES.index(stage):3 if generic else 4]
    rates = {p: float(config["phase_historical_success_rates"][f"PHASE{i}"]["success_rate"])
             for i, p in enumerate(STAGES[:3], 1)}
    rates["filed"] = float(config["regulatory_approval_success_rate"])
    thresholds = {p: rates[p] for p in stages}
    if stage != "filed" and override_rate is not None:
        # 個別設定は残る臨床・申請準備リスクのまとめ。審査ゲートは別に掛ける。
        thresholds = {stage: min(float(override_rate), config["success_rate_policy"]["display_cap"])}
        if not generic:
            thresholds["filed"] = rates["filed"]
        return thresholds
    if "P3" in thresholds:
        p3 = rates["P3"]
        if forecast.get("skipped_controlled_phase2"):
            p3 *= rates["P2"]
        if scenario == "rp_history" and (forecast.get("group") == "slow" if slow is None else slow):
            p3 = min(p3, float(config["success_rate_scenarios"][scenario]["slow_phase3_success_rate"]))
        if gene_therapy:
            p3 *= 0.9  # 既存の遺伝子治療リスク調整（仮定）
        thresholds["P3"] = p3
    return thresholds


def summarize(draws: list[float]) -> dict:
    arrived = sorted(v for v in draws if math.isfinite(v))
    if not arrived:
        return {"median": None, "p10": None, "p90": None}
    def quantile(q):
        idx = (len(arrived) - 1) * q
        lo, hi = math.floor(idx), math.ceil(idx)
        return round(arrived[lo] + (arrived[hi] - arrived[lo]) * (idx - lo), 4)
    return {key: quantile(q) for key, q in (("median", .5), ("p10", .1), ("p90", .9))}


def make_forecast(knowledge_base: dict, config: dict, *, today: date | None = None,
                  simulations: int | None = None, seed: int | None = None) -> dict:
    today = today or date.today()
    simulations = config["arrival_simulations"] if simulations is None else simulations
    seed = config["arrival_random_seed"] if seed is None else seed
    if simulations <= 0:
        raise ValueError("試行回数は1以上にしてください")
    rho = float(config["slow_progression_correlation"])
    if not 0 <= rho <= 1:
        raise ValueError("相関は0〜1にしてください")
    rng = random.Random(seed)
    now = decimal_year(today)
    years = config["stage_duration_years_bio"]
    common_z = [rng.gauss(0, 1) for _ in range(simulations)]
    def empty_draws():
        return {scenario: {place: [math.inf] * simulations for place in ("us", "japan")}
                for scenario in SCENARIOS}
    groups = {group: empty_draws() for group in ("slow_any", "restore_any")}
    programs, excluded, null_fields = {}, {}, {}
    for name, program in knowledge_base["programs"].items():
        forecast = program.get("forecast")
        if forecast is None:
            continue
        missing = [key for key, value in forecast.items() if value is None]
        if missing:
            null_fields[name] = missing
        if forecast["stage"] is None:
            excluded[name] = "臨床段階が不明のため計算対象外"
            continue
        phase = forecast["stage"]
        stages = STAGES[STAGES.index(phase):3 if forecast["generic"] else 4]
        readout = month_end(forecast["readout"])
        known_end = decimal_year(readout) if readout and readout >= today else None
        slow = forecast["group"] == "slow"
        cfg = program_config(name, config)
        thresholds = {scenario: stage_probabilities(forecast, config, scenario=scenario,
                      gene_therapy=is_gene_therapy(program), override_rate=cfg.get("success_rate"))
                      for scenario in SCENARIOS}
        draws = empty_draws()
        lag_kind = forecast["japan_lag"]
        if lag_kind not in ("none", "default", "sakigake"):
            raise ValueError(f"日本の遅れを指定してください: {name}")
        lag_cfg = config["japan_delay_years_sakigake" if lag_kind == "sakigake" else "japan_delay_years"]
        for index in range(simulations):
            # 成否にかかわらず、両シナリオに同じ乱数と到達時期を使う。
            first = years[phase] * rng.uniform(.3, 1.)
            delayed = years[phase] * rng.lognormvariate(0, .3)
            passes = {}
            for stage in stages:
                if slow and stage in ("P2", "P3"):
                    z = math.sqrt(rho) * common_z[index] + math.sqrt(1-rho) * rng.gauss(0, 1)
                    passes[stage] = .5 * (1 + math.erf(z / math.sqrt(2)))
                else:
                    passes[stage] = rng.random()
            if forecast["not_started"]:
                end = max(known_end or now, now + delayed)
            else:
                end = known_end if known_end is not None else now + first
            for stage in stages[1:]:
                end += years[stage] * rng.lognormvariate(0, .3)
            lag = 0 if forecast["generic"] or lag_kind == "none" else rng.triangular(lag_cfg["min"], lag_cfg["max"], lag_cfg["median"])
            for scenario in SCENARIOS:
                if all(passes[stage] < threshold for stage, threshold in thresholds[scenario].items()):
                    draws[scenario]["us"][index] = end
                    draws[scenario]["japan"][index] = end + lag
        programs[name] = {scenario: {
            "probability": sum(math.isfinite(v) for v in draws[scenario]["us"]) / simulations,
            "us": summarize(draws[scenario]["us"]), "japan": summarize(draws[scenario]["japan"]),
        } for scenario in SCENARIOS}
        scope = program.get("message_design", {}).get("genotype_scope_key")
        group = "slow_any" if slow and scope == "agnostic" else ("restore_any" if forecast["group"] == "restore" else None)
        if group:
            for scenario in SCENARIOS:
                for place in ("us", "japan"):
                    groups[group][scenario][place] = [min(a, b) for a, b in zip(groups[group][scenario][place], draws[scenario][place])]
    probabilities = {group: {scenario: {place: [
        sum(v <= decimal_year(date(year, 12, 31)) for v in values) / simulations for year in YEARS]
        for place, values in places.items()} for scenario, places in scenarios.items()}
        for group, scenarios in groups.items()}
    return {"as_of": today.isoformat(), "seed": seed, "simulations": simulations,
            "years": YEARS, "groups": probabilities, "programs": programs,
            "null_fields": null_fields, "excluded_programs": excluded,
            "timing_note": "年の分位点は到達した試行のみ。主要評価完了日が不明・過去ならBIO期間で推定。米国は既存薬の場合、試験陽性の到達を指す。",
            "slow_progression_correlation": rho}


def run(*, today: date | None = None) -> dict:
    kb = json.loads((ROOT / "data/knowledge_base/clinical_programs.json").read_text())
    config = yaml.safe_load((ROOT / "config/simulation_params.yaml").read_text())
    result = make_forecast(kb, config, today=today)
    output = ROOT / "results/arrival_probability.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


if __name__ == "__main__":
    run()
