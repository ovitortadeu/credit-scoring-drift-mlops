"""Testes para as regras de alerta de drift critico e bloqueio de contrato."""

from __future__ import annotations

import json

from src.observability import alerts


def _value_drift_metric(column: str, value: float, threshold: float = 0.1) -> dict:
    return {
        "metric_name": f"ValueDrift(column={column})",
        "config": {
            "type": alerts.DRIFT_VALUE_METRIC_TYPE,
            "column": column,
            "method": "Wasserstein distance (normed)",
            "threshold": threshold,
        },
        "value": value,
    }


def test_check_drift_alerts_flags_columns_above_threshold():
    drift_report = {
        "metrics": [
            _value_drift_metric("limit_bal", 0.0198),
            _value_drift_metric("pay_0", 0.7231),
            _value_drift_metric("pay_2", 0.6858),
        ]
    }

    result = alerts.check_drift_alerts(drift_report)

    columns = {alert["column"] for alert in result}
    assert columns == {"pay_0", "pay_2"}
    assert all(alert["type"] == "drift" for alert in result)
    assert all(alert["severity"] == "critical" for alert in result)


def test_check_drift_alerts_ignores_value_equal_to_threshold():
    drift_report = {"metrics": [_value_drift_metric("age", 0.1, threshold=0.1)]}

    assert alerts.check_drift_alerts(drift_report) == []


def test_check_drift_alerts_ignores_non_value_drift_metrics():
    drift_report = {
        "metrics": [
            {
                "metric_name": "DriftedColumnsCount(drift_share=0.5)",
                "config": {"type": "evidently:metric_v2:DriftedColumnsCount"},
                "value": {"count": 6.0, "share": 0.26},
            }
        ]
    }

    assert alerts.check_drift_alerts(drift_report) == []


def test_check_drift_alerts_handles_empty_report():
    assert alerts.check_drift_alerts({}) == []
    assert alerts.check_drift_alerts({"metrics": []}) == []


def test_check_contract_alert_returns_none_when_no_violations():
    assert alerts.check_contract_alert("reference.csv", 0) is None


def test_check_contract_alert_builds_error_alert():
    alert = alerts.check_contract_alert("invalid_batch.csv", 14)

    assert alert["type"] == "contract_violation"
    assert alert["severity"] == "error"
    assert alert["batch"] == "invalid_batch.csv"
    assert alert["violation_count"] == 14
    assert "timestamp" in alert


def test_save_alerts_appends_to_existing_file(tmp_path, monkeypatch):
    alerts_path = tmp_path / "alerts.json"
    monkeypatch.setattr(alerts, "ALERTS_PATH", alerts_path)

    first_batch = [alerts.check_contract_alert("batch_a.csv", 3)]
    alerts.save_alerts(first_batch)

    second_batch = [alerts.check_contract_alert("batch_b.csv", 1)]
    alerts.save_alerts(second_batch)

    saved = json.loads(alerts_path.read_text(encoding="utf-8"))
    assert len(saved) == 2
    assert saved[0]["batch"] == "batch_a.csv"
    assert saved[1]["batch"] == "batch_b.csv"


def test_save_alerts_skips_write_when_no_alerts(tmp_path, monkeypatch):
    alerts_path = tmp_path / "alerts.json"
    monkeypatch.setattr(alerts, "ALERTS_PATH", alerts_path)

    alerts.save_alerts([])

    assert not alerts_path.exists()
