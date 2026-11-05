import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import evaluate  # noqa: E402


def alert(ts, rule, container="victim"):
    return evaluate.Alert(
        time=ts,
        rule=rule,
        priority="WARNING",
        output=f"{rule} fired",
        container=container,
        namespace="lab",
        raw={},
    )


def test_parse_timestamp_handles_nanoseconds():
    ts = evaluate.parse_timestamp("2026-11-05T03:04:05.123456789Z")
    assert ts == evaluate.parse_timestamp("2026-11-05T03:04:05.123456Z")


def test_parse_timestamp_rejects_garbage():
    with pytest.raises(ValueError):
        evaluate.parse_timestamp("not-a-date")


def test_parse_alerts_ignores_non_json(tmp_path):
    path = tmp_path / "alerts.jsonl"
    lines = [
        "Falco started",
        json.dumps({"time": "2026-11-05T03:00:00.000000000Z", "rule": "A", "output": "x"}),
        "{broken",
        json.dumps({"no_rule": True}),
        json.dumps(
            {
                "time": "2026-11-05T03:00:01.000000000Z",
                "rule": "B",
                "output": "y",
                "output_fields": {"container.name": "victim", "k8s.ns.name": "lab"},
            }
        ),
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    alerts = evaluate.parse_alerts(path)
    assert [a.rule for a in alerts] == ["A", "B"]
    assert alerts[1].container == "victim"


def test_parse_alerts_missing_file(tmp_path):
    assert evaluate.parse_alerts(tmp_path / "nope.jsonl") == []


def test_evaluate_v1_v2_and_window_grace():
    expected = {
        "window_grace_seconds": 5,
        "scenarios": [
            {"id": "S1", "title": "one", "attack": "T1", "expected_any": ["Default Rule"]},
            {"id": "S2", "title": "two", "attack": "T2", "expected_any": ["Custom Rule"]},
            {"id": "S3", "title": "three", "attack": "T3", "expected_any": ["Never Fires"]},
        ],
    }
    windows = {"S1": (100.0, 110.0), "S2": (200.0, 210.0), "S3": (300.0, 310.0)}
    alerts = [
        alert(105, "Default Rule"),
        alert(114, "Default Rule"),  # inside grace
        alert(116, "Default Rule"),  # outside grace
        alert(205, "Custom Rule"),
        alert(209, "Unrelated"),
    ]
    metrics = evaluate.evaluate(expected, windows, alerts, {"Custom Rule"}, grace=5)
    rows = {row["id"]: row for row in metrics["per_scenario"]}
    assert rows["S1"]["detected_v1"] is True
    assert rows["S1"]["alerts"] == 2
    assert rows["S2"]["detected_v1"] is False
    assert rows["S2"]["detected_v2"] is True
    assert rows["S3"]["status"] == "missed"
    assert metrics["v1_detected"] == 1
    assert metrics["v2_detected"] == 2


def test_evaluate_marks_scenario_that_did_not_run():
    expected = {
        "scenarios": [{"id": "S9", "title": "missing", "attack": "", "expected_any": ["X"]}]
    }
    metrics = evaluate.evaluate(expected, {}, [], set())
    assert metrics["per_scenario"][0]["status"] == "scenario did not run"
    assert metrics["v2_detected"] == 0


def test_benign_rate_is_measured(monkeypatch, tmp_path):
    monkeypatch.setattr(evaluate, "RESULTS", tmp_path)
    (tmp_path / "benign_window.tsv").write_text("1000\t1900\n", encoding="utf-8")
    expected = {"scenarios": []}
    alerts = [alert(1100, "Noise"), alert(1200, "Noise"), alert(5000, "Outside")]
    metrics = evaluate.evaluate(expected, {}, alerts, set())
    assert metrics["benign_minutes"] == 15.0
    assert metrics["benign_alerts"] == 2
    assert metrics["benign_alerts_per_hour"] == 8.0


def test_write_outputs_creates_all_files(monkeypatch, tmp_path):
    monkeypatch.setattr(evaluate, "RESULTS", tmp_path)
    metrics = {
        "generated_at": "2026-11-05T00:00:00+00:00",
        "scenarios_total": 1,
        "v1_detected": 0,
        "v2_detected": 1,
        "v1_rate": 0.0,
        "v2_rate": 1.0,
        "custom_rules": ["C"],
        "benign_minutes": 1.0,
        "benign_alerts": 0,
        "benign_alerts_per_hour": 0.0,
        "benign_details": [],
        "alerts_total": 1,
        "per_scenario": [
            {
                "id": "S1",
                "title": "t",
                "attack": "T1",
                "detected_v1": False,
                "detected_v2": True,
                "alerts": 1,
                "matched_rules": ["C"],
                "status": "detected",
            }
        ],
        "per_rule": {"C": 1},
        "matrix": {"C": {"S1": 1}},
    }
    evaluate.write_outputs(metrics)
    for name in ("metrics.json", "RESULTS.md", "scenario_rule_matrix.csv", "per_rule.csv"):
        assert (tmp_path / name).exists()
    assert "1/1" in (tmp_path / "RESULTS.md").read_text(encoding="utf-8")


def test_custom_rule_names_reads_yaml():
    names = evaluate.custom_rule_names(ROOT / "rules" / "custom_rules.yaml")
    assert len(names) == 5
    assert "Service Account Token Read in Container" in names
