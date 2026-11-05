"""Testes para o agregador de metricas de observabilidade."""

from __future__ import annotations

import json

from src.observability import metrics


def test_stage_status_missing_when_report_absent():
    assert metrics._stage_status(None, {"a": "a"}) == {"status": "missing"}


def test_stage_status_copies_requested_fields():
    data = {"trained_at_utc": "2026-01-01T00:00:00+00:00", "training_rows": 100, "extra": "x"}

    status = metrics._stage_status(
        data, {"trained_at_utc": "trained_at_utc", "training_rows": "training_rows"}
    )

    assert status == {
        "status": "ok",
        "trained_at_utc": "2026-01-01T00:00:00+00:00",
        "training_rows": 100,
    }


def test_summarize_log_counts_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(metrics, "LOG_FILE_PATH", tmp_path / "does_not_exist.log")

    assert metrics.summarize_log_counts() == {"INFO": 0, "WARNING": 0, "ERROR": 0}


def test_summarize_log_counts_counts_by_level(tmp_path, monkeypatch):
    log_path = tmp_path / "pipeline.log"
    lines = [
        json.dumps({"level": "INFO", "message": "a"}),
        json.dumps({"level": "INFO", "message": "b"}),
        json.dumps({"level": "WARNING", "message": "c"}),
        json.dumps({"level": "ERROR", "message": "d"}),
        "linha invalida que nao e json",
        "",
    ]
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    monkeypatch.setattr(metrics, "LOG_FILE_PATH", log_path)

    assert metrics.summarize_log_counts() == {"INFO": 2, "WARNING": 1, "ERROR": 1}


def test_summarize_drift_missing_report():
    assert metrics.summarize_drift(None) == {"status": "missing"}


def test_summarize_drift_extracts_columns_above_threshold():
    drift_report = {
        "metrics": [
            {
                "config": {"type": metrics.DRIFTED_COLUMNS_COUNT_METRIC_TYPE},
                "value": {"count": 2.0, "share": 0.5},
            },
            {
                "config": {
                    "type": metrics.DRIFT_VALUE_METRIC_TYPE,
                    "column": "pay_0",
                    "threshold": 0.1,
                },
                "value": 0.72,
            },
            {
                "config": {
                    "type": metrics.DRIFT_VALUE_METRIC_TYPE,
                    "column": "age",
                    "threshold": 0.1,
                },
                "value": 0.01,
            },
        ]
    }

    result = metrics.summarize_drift(drift_report)

    assert result["status"] == "ok"
    assert result["drifted_columns_count"] == 2.0
    assert result["drifted_columns_share"] == 0.5
    assert result["columns_above_threshold"] == ["pay_0"]


def test_summarize_alerts_empty():
    assert metrics.summarize_alerts(None) == {"total": 0, "by_type": {}}
    assert metrics.summarize_alerts([]) == {"total": 0, "by_type": {}}


def test_summarize_alerts_groups_by_type():
    alerts = [
        {"type": "drift"},
        {"type": "drift"},
        {"type": "contract_violation"},
    ]

    result = metrics.summarize_alerts(alerts)

    assert result == {"total": 3, "by_type": {"drift": 2, "contract_violation": 1}}


def test_build_summary_handles_all_reports_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(metrics, "TRAINING_SUMMARY_PATH", tmp_path / "missing.json")
    monkeypatch.setattr(metrics, "BASELINE_METRICS_PATH", tmp_path / "missing.json")
    monkeypatch.setattr(metrics, "DRIFT_SIMULATION_PATH", tmp_path / "missing.json")
    monkeypatch.setattr(metrics, "DRIFT_REPORT_PATH", tmp_path / "missing.json")
    monkeypatch.setattr(metrics, "DRIFT_IMPACT_PATH", tmp_path / "missing.json")
    monkeypatch.setattr(metrics, "ALERTS_PATH", tmp_path / "missing.json")
    monkeypatch.setattr(metrics, "LOG_FILE_PATH", tmp_path / "missing.log")

    summary = metrics.build_summary()

    assert summary["pipeline_stages"]["train"] == {"status": "missing"}
    assert summary["pipeline_stages"]["drift_detection"] == {"status": "missing"}
    assert summary["model_metrics"] == {}
    assert summary["alerts"] == {"total": 0, "by_type": {}}


def test_main_writes_summary_file(tmp_path, monkeypatch):
    monkeypatch.setattr(metrics, "TRAINING_SUMMARY_PATH", tmp_path / "missing.json")
    monkeypatch.setattr(metrics, "BASELINE_METRICS_PATH", tmp_path / "missing.json")
    monkeypatch.setattr(metrics, "DRIFT_SIMULATION_PATH", tmp_path / "missing.json")
    monkeypatch.setattr(metrics, "DRIFT_REPORT_PATH", tmp_path / "missing.json")
    monkeypatch.setattr(metrics, "DRIFT_IMPACT_PATH", tmp_path / "missing.json")
    monkeypatch.setattr(metrics, "ALERTS_PATH", tmp_path / "missing.json")
    monkeypatch.setattr(metrics, "LOG_FILE_PATH", tmp_path / "missing.log")

    summary_path = tmp_path / "observability_summary.json"
    monkeypatch.setattr(metrics, "SUMMARY_PATH", summary_path)

    metrics.main()

    assert summary_path.exists()
    saved = json.loads(summary_path.read_text(encoding="utf-8"))
    assert "generated_at_utc" in saved
