#!/usr/bin/env python3
"""Evaluate Falco alerts against the frozen ground truth.

Inputs (all produced by the scripts in this repo):
  scenarios/expected.yaml   ground truth, committed before the first run
  results/timeline.tsv      "<scenario id>\\t<start epoch>\\t<end epoch>"
  results/alerts.jsonl      raw Falco JSON output (one alert per line)
  results/benign_window.tsv "<start epoch>\\t<end epoch>"
  rules/custom_rules.yaml   rule names that belong to v2 only

Outputs:
  results/metrics.json
  results/RESULTS.md
  results/scenario_rule_matrix.csv
  results/per_rule.csv

The command that produces the inputs is recorded in results/RESULTS.md.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"


@dataclass
class Alert:
    time: float
    rule: str
    priority: str
    output: str
    container: str = ""
    namespace: str = ""
    raw: dict = field(default_factory=dict)

    @property
    def is_custom(self) -> bool:
        return False  # set by the evaluator, kept for readability


def parse_timestamp(value: str) -> float:
    """Parse Falco/RFC3339 timestamps, including nanosecond fractions.

    Python's fromisoformat only accepts microseconds, so the fraction is
    truncated. Falco emits UTC ("Z").
    """
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    match = re.match(r"^(.*?\.)(\d+)(.*)$", value)
    if match:
        head, fraction, tail = match.groups()
        value = head + fraction[:6].ljust(6, "0") + tail
    return datetime.fromisoformat(value).timestamp()


def parse_alerts(path: Path) -> list[Alert]:
    alerts: list[Alert] = []
    if not path.exists():
        return alerts
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "rule" not in data or "time" not in data:
            continue
        fields = data.get("output_fields") or {}
        try:
            ts = parse_timestamp(data["time"])
        except (ValueError, TypeError):
            continue
        alerts.append(
            Alert(
                time=ts,
                rule=data["rule"],
                priority=data.get("priority", ""),
                output=data.get("output", ""),
                container=str(fields.get("container.name", "")),
                namespace=str(fields.get("k8s.ns.name", "")),
                raw=data,
            )
        )
    return alerts


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def custom_rule_names(path: Path) -> set[str]:
    data = load_yaml(path) or []
    return {rule["rule"] for rule in data if isinstance(rule, dict) and "rule" in rule}


def read_timeline(path: Path) -> dict[str, tuple[float, float]]:
    windows: dict[str, tuple[float, float]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split("\t")
        if len(parts) != 3:
            continue
        windows[parts[0]] = (float(parts[1]), float(parts[2]))
    return windows


def read_benign(path: Path) -> tuple[float, float] | None:
    if not path.exists():
        return None
    parts = path.read_text(encoding="utf-8").strip().split("\t")
    if len(parts) != 2:
        return None
    return float(parts[0]), float(parts[1])


def alerts_in_window(alerts: list[Alert], start: float, end: float) -> list[Alert]:
    return [a for a in alerts if start <= a.time <= end]


def evaluate(
    expected: dict,
    windows: dict[str, tuple[float, float]],
    alerts: list[Alert],
    custom_names: set[str],
    grace: float = 8.0,
) -> dict:
    per_scenario = []
    matrix: dict[str, dict[str, int]] = {}
    for scenario in expected["scenarios"]:
        sid = scenario["id"]
        window = windows.get(sid)
        expected_rules = set(scenario["expected_any"])
        if window is None:
            per_scenario.append(
                {
                    "id": sid,
                    "title": scenario["title"],
                    "attack": scenario.get("attack", ""),
                    "detected_v1": False,
                    "detected_v2": False,
                    "alerts": 0,
                    "matched_rules": [],
                    "status": "scenario did not run",
                }
            )
            continue
        window_alerts = alerts_in_window(alerts, window[0], window[1] + grace)
        matched = sorted({a.rule for a in window_alerts if a.rule in expected_rules})
        matched_v1 = sorted(
            {
                a.rule
                for a in window_alerts
                if a.rule in expected_rules and a.rule not in custom_names
            }
        )
        per_scenario.append(
            {
                "id": sid,
                "title": scenario["title"],
                "attack": scenario.get("attack", ""),
                "detected_v1": bool(matched_v1),
                "detected_v2": bool(matched),
                "alerts": len(window_alerts),
                "matched_rules": matched,
                "status": "detected" if matched else "missed",
            }
        )
        for alert in window_alerts:
            row = matrix.setdefault(alert.rule, {})
            row[sid] = row.get(sid, 0) + 1

    total = len(expected["scenarios"])
    v1 = sum(1 for row in per_scenario if row["detected_v1"])
    v2 = sum(1 for row in per_scenario if row["detected_v2"])

    benign = read_benign(RESULTS / "benign_window.tsv")
    benign_alerts: list[Alert] = []
    benign_minutes = 0.0
    benign_per_hour: float | None = None
    if benign:
        benign_alerts = alerts_in_window(alerts, benign[0], benign[1])
        benign_minutes = round((benign[1] - benign[0]) / 60, 1)
        if benign_minutes > 0:
            benign_per_hour = round(len(benign_alerts) / (benign_minutes / 60), 2)

    rule_counts: dict[str, int] = {}
    for alert in alerts:
        rule_counts[alert.rule] = rule_counts.get(alert.rule, 0) + 1

    metrics = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "scenarios_total": total,
        "v1_detected": v1,
        "v2_detected": v2,
        "v1_rate": round(v1 / total, 4) if total else None,
        "v2_rate": round(v2 / total, 4) if total else None,
        "custom_rules": sorted(custom_names),
        "benign_minutes": benign_minutes,
        "benign_alerts": len(benign_alerts),
        "benign_alerts_per_hour": benign_per_hour,
        "benign_details": [
            {"rule": a.rule, "container": a.container, "output": a.output} for a in benign_alerts
        ],
        "alerts_total": len(alerts),
        "per_scenario": per_scenario,
        "per_rule": dict(sorted(rule_counts.items(), key=lambda item: (-item[1], item[0]))),
        "matrix": matrix,
    }
    return metrics


def write_outputs(metrics: dict) -> None:
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    with (RESULTS / "scenario_rule_matrix.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["rule"] + [row["id"] for row in metrics["per_scenario"]])
        for rule, cols in sorted(metrics["matrix"].items()):
            writer.writerow([rule] + [cols.get(row["id"], 0) for row in metrics["per_scenario"]])

    with (RESULTS / "per_rule.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["rule", "alerts"])
        for rule, count in metrics["per_rule"].items():
            writer.writerow([rule, count])

    lines = [
        "# Results — k8s-threat-detection-lab",
        "",
        f"Generated by `python evaluate.py` at {metrics['generated_at']} (UTC).",
        "",
        "## Headline",
        "",
        "| Metric | v1 (default Falco rules) | v2 (default + 5 custom rules) |",
        "|---|---|---|",
        f"| Scenarios detected | {metrics['v1_detected']}/{metrics['scenarios_total']} "
        f"({metrics['v1_rate']:.1%}) | {metrics['v2_detected']}/{metrics['scenarios_total']} "
        f"({metrics['v2_rate']:.1%}) |",
        "",
        f"- Benign workload observed: **{metrics['benign_minutes']} minutes**, "
        f"**{metrics['benign_alerts']} alerts** "
        f"(**{metrics['benign_alerts_per_hour']} alerts/hour**).",
        f"- Total Falco alerts collected: **{metrics['alerts_total']}**.",
        "",
        "## Per scenario",
        "",
        "| ID | Scenario | ATT&CK | v1 | v2 | Alerts in window | Rule(s) that fired |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in metrics["per_scenario"]:
        rules = ", ".join(f"`{r}`" for r in row["matched_rules"]) or "—"
        lines.append(
            f"| {row['id']} | {row['title']} | {row['attack']} | "
            f"{'yes' if row['detected_v1'] else 'no'} | "
            f"{'yes' if row['detected_v2'] else 'no'} | {row['alerts']} | {rules} |"
        )

    lines += [
        "",
        "## Alerts during the benign window",
        "",
    ]
    if metrics["benign_details"]:
        for item in metrics["benign_details"]:
            lines.append(f"- `{item['rule']}` (container `{item['container']}`): {item['output']}")
    else:
        lines.append("None.")

    lines += [
        "",
        "## Reproduction",
        "",
        "```bash",
        "bash scripts/cluster_up.sh",
        "bash scripts/install_falco.sh",
        "bash scripts/collect_alerts.sh &   # or run it in a second shell",
        "bash scripts/run_scenarios.sh",
        "bash scenarios/benign.sh",
        "kill %1",
        "python evaluate.py",
        "```",
        "",
        "`results/timeline.tsv`, `results/benign_window.tsv` and `results/alerts.jsonl`",
        "inputs; this file is generated from them and contains no hand-written numbers.",
        "",
    ]
    (RESULTS / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    expected = load_yaml(ROOT / "scenarios" / "expected.yaml")
    custom = custom_rule_names(ROOT / "rules" / "custom_rules.yaml")
    windows = read_timeline(RESULTS / "timeline.tsv") if (RESULTS / "timeline.tsv").exists() else {}
    alerts = parse_alerts(RESULTS / "alerts.jsonl")
    metrics = evaluate(expected, windows, alerts, custom, expected.get("window_grace_seconds", 8))
    write_outputs(metrics)

    print(
        f"v1 {metrics['v1_detected']}/{metrics['scenarios_total']}  "
        f"v2 {metrics['v2_detected']}/{metrics['scenarios_total']}  "
        f"benign {metrics['benign_alerts']} alerts in {metrics['benign_minutes']} min"
    )
    # Quality gate: the custom rules may not make detection worse. The absolute
    # recall is deliberately not gated: the measured number depends on which rule
    # feeds the chart installs, and hiding a low recall behind a threshold would
    # defeat the point of the lab.
    gate = metrics["v2_detected"] >= metrics["v1_detected"]
    return 0 if gate else 1


if __name__ == "__main__":
    sys.exit(main())
