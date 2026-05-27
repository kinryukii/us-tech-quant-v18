from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import csv
import json

from qutumn.common.paths import ROOT, CONFIGS_V16, STATE_V16, OUTPUTS_V16, ensure_dir
from qutumn.common.config_io import load_yaml_like


@dataclass
class StrategyRecord:
    strategy_name: str
    version: str
    config_status: str
    registry_status: str
    config_file: str
    universes: list[str]
    tickers: list[str]
    entry_style: str
    event_gate_mode: str
    allow_leveraged_etf: bool
    max_single_position_pct: float | None
    current_stage: str
    approval_status: str
    reason: str


def _as_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value]
    return [str(value)]


def _as_float_or_none(value: object) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def load_universe_map() -> dict[str, dict]:
    universe_dir = CONFIGS_V16 / "universe"
    result: dict[str, dict] = {}

    for path in sorted(universe_dir.glob("*.yaml")):
        cfg = load_yaml_like(path)
        name = str(cfg.get("universe_name", path.stem))
        cfg["_config_file"] = str(path.relative_to(ROOT))
        result[name] = cfg

    return result


def load_strategy_registry() -> dict[str, str]:
    path = STATE_V16 / "strategy_registry.yaml"
    if not path.exists():
        return {}

    cfg = load_yaml_like(path)
    strategies = cfg.get("strategies")

    out: dict[str, str] = {}

    if isinstance(strategies, dict):
        for name, meta in strategies.items():
            if isinstance(meta, dict):
                out[str(name)] = str(meta.get("status", "UNKNOWN"))
            else:
                out[str(name)] = str(meta)
        return out

    return out


def determine_approval_status(
    config_status: str,
    registry_status: str,
    universe_names: list[str],
    tickers: list[str],
    allow_leveraged_etf: bool,
    event_gate_mode: str,
) -> tuple[str, str, str]:
    normalized_status = (registry_status or config_status or "UNKNOWN").upper()

    if not universe_names:
        return "CONFIG_ERROR", "REJECTED", "No universe is defined."

    if not tickers:
        return "CONFIG_INCOMPLETE", "WATCH", "Universe exists but has no tickers."

    if allow_leveraged_etf and event_gate_mode != "strict":
        return "RISK_CONFIG_ERROR", "REJECTED", "Leveraged strategy must use strict event gate."

    if normalized_status in {"RETIRED", "REJECTED"}:
        return normalized_status, "REJECTED", "Strategy registry is not active."

    return "RESEARCH", "BACKTEST_READY", "Strategy config is structurally ready for future backtest."


def collect_strategy_records() -> list[StrategyRecord]:
    universe_map = load_universe_map()
    registry = load_strategy_registry()
    records: list[StrategyRecord] = []

    strategies_dir = CONFIGS_V16 / "strategies"

    for path in sorted(strategies_dir.glob("strategy_*.yaml")):
        cfg = load_yaml_like(path)

        strategy_name = str(cfg.get("strategy_name", path.stem.replace("strategy_", "")))
        version = str(cfg.get("version", "unknown"))
        config_status = str(cfg.get("status", "unknown"))

        universe_names = _as_list(cfg.get("universe"))

        tickers: list[str] = []
        for universe_name in universe_names:
            universe_cfg = universe_map.get(universe_name, {})
            tickers.extend(_as_list(universe_cfg.get("tickers")))

        tickers = list(dict.fromkeys(tickers))

        risk = cfg.get("risk", {})
        if not isinstance(risk, dict):
            risk = {}

        entry_style = str(cfg.get("entry_style", "unknown"))
        event_gate_mode = str(risk.get("event_gate_mode", "unknown"))
        allow_leveraged_etf = bool(risk.get("allow_leveraged_etf", False))
        max_single_position_pct = _as_float_or_none(risk.get("max_single_position_pct"))

        registry_status = registry.get(strategy_name, "UNKNOWN")

        current_stage, approval_status, reason = determine_approval_status(
            config_status=config_status,
            registry_status=registry_status,
            universe_names=universe_names,
            tickers=tickers,
            allow_leveraged_etf=allow_leveraged_etf,
            event_gate_mode=event_gate_mode,
        )

        records.append(
            StrategyRecord(
                strategy_name=strategy_name,
                version=version,
                config_status=config_status,
                registry_status=registry_status,
                config_file=str(path.relative_to(ROOT)),
                universes=universe_names,
                tickers=tickers,
                entry_style=entry_style,
                event_gate_mode=event_gate_mode,
                allow_leveraged_etf=allow_leveraged_etf,
                max_single_position_pct=max_single_position_pct,
                current_stage=current_stage,
                approval_status=approval_status,
                reason=reason,
            )
        )

    return records


def write_strategy_scoreboard(records: list[StrategyRecord]) -> tuple[Path, Path, Path]:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    out_dir = ensure_dir(OUTPUTS_V16 / "backtest")

    csv_path = out_dir / "V16_STRATEGY_SCOREBOARD.csv"
    md_path = out_dir / "V16_STRATEGY_SCOREBOARD.md"
    json_path = out_dir / "V16_STRATEGY_SCOREBOARD.json"

    fieldnames = [
        "strategy_name",
        "version",
        "config_status",
        "registry_status",
        "current_stage",
        "approval_status",
        "entry_style",
        "event_gate_mode",
        "allow_leveraged_etf",
        "max_single_position_pct",
        "universe_count",
        "ticker_count",
        "universes",
        "tickers",
        "config_file",
        "reason",
    ]

    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for record in records:
            writer.writerow(
                {
                    "strategy_name": record.strategy_name,
                    "version": record.version,
                    "config_status": record.config_status,
                    "registry_status": record.registry_status,
                    "current_stage": record.current_stage,
                    "approval_status": record.approval_status,
                    "entry_style": record.entry_style,
                    "event_gate_mode": record.event_gate_mode,
                    "allow_leveraged_etf": record.allow_leveraged_etf,
                    "max_single_position_pct": record.max_single_position_pct,
                    "universe_count": len(record.universes),
                    "ticker_count": len(record.tickers),
                    "universes": ";".join(record.universes),
                    "tickers": ";".join(record.tickers),
                    "config_file": record.config_file,
                    "reason": record.reason,
                }
            )

    lines: list[str] = []
    lines.append("# V16 Strategy Scoreboard")
    lines.append("")
    lines.append(f"生成时间：`{generated_at}`")
    lines.append("")
    lines.append("## 1. 当前结论")
    lines.append("")
    lines.append("V16.2 Strategy Lab 骨架已建立。")
    lines.append("")
    lines.append("当前阶段只做结构检查：读取 strategy yaml、读取 universe yaml、读取 strategy registry，并标记哪些策略可以进入未来回测。")
    lines.append("")
    lines.append("重要限制：V16.2 还不产生真实交易建议，也不代表策略已经通过历史回测。")
    lines.append("")
    lines.append("## 2. 策略总表")
    lines.append("")
    lines.append("| 策略 | 阶段 | 结构状态 | 风险门 | 杠杆ETF | 股票数 | 结论 |")
    lines.append("|---|---|---|---|---:|---:|---|")

    for record in records:
        lines.append(
            f"| `{record.strategy_name}` | `{record.current_stage}` | `{record.approval_status}` | "
            f"`{record.event_gate_mode}` | `{record.allow_leveraged_etf}` | `{len(record.tickers)}` | {record.reason} |"
        )

    lines.append("")
    lines.append("## 3. 策略明细")
    lines.append("")

    for record in records:
        lines.append(f"### {record.strategy_name}")
        lines.append("")
        lines.append(f"- config：`{record.config_file}`")
        lines.append(f"- version：`{record.version}`")
        lines.append(f"- config_status：`{record.config_status}`")
        lines.append(f"- registry_status：`{record.registry_status}`")
        lines.append(f"- entry_style：`{record.entry_style}`")
        lines.append(f"- event_gate_mode：`{record.event_gate_mode}`")
        lines.append(f"- allow_leveraged_etf：`{record.allow_leveraged_etf}`")
        lines.append(f"- max_single_position_pct：`{record.max_single_position_pct}`")
        lines.append(f"- universes：`{', '.join(record.universes)}`")
        lines.append(f"- tickers：`{', '.join(record.tickers)}`")
        lines.append(f"- current_stage：`{record.current_stage}`")
        lines.append(f"- approval_status：`{record.approval_status}`")
        lines.append(f"- reason：{record.reason}")
        lines.append("")

    lines.append("## 4. 下一步")
    lines.append("")
    lines.append("进入 V16.2B：建立 backtest runner 骨架，接入历史价格数据，对每个策略生成基础回测指标。")
    lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")

    payload = {
        "generated_at": generated_at,
        "strategy_count": len(records),
        "records": [
            {
                "strategy_name": record.strategy_name,
                "version": record.version,
                "config_status": record.config_status,
                "registry_status": record.registry_status,
                "current_stage": record.current_stage,
                "approval_status": record.approval_status,
                "entry_style": record.entry_style,
                "event_gate_mode": record.event_gate_mode,
                "allow_leveraged_etf": record.allow_leveraged_etf,
                "max_single_position_pct": record.max_single_position_pct,
                "universes": record.universes,
                "tickers": record.tickers,
                "config_file": record.config_file,
                "reason": record.reason,
            }
            for record in records
        ],
    }

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    return md_path, csv_path, json_path


def run_strategy_lab() -> int:
    records = collect_strategy_records()
    md_path, csv_path, json_path = write_strategy_scoreboard(records)

    print("")
    print("V16 Strategy Lab completed.")
    print(f"- strategy_count: {len(records)}")
    print(f"- markdown: {md_path}")
    print(f"- csv: {csv_path}")
    print(f"- json: {json_path}")

    return 0
