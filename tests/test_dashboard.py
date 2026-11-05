"""Testes para a geracao do dashboard HTML de observabilidade."""

from __future__ import annotations

import json

import pytest

from src.observability import dashboard


@pytest.fixture
def sample_summary() -> dict:
    return {
        "generated_at_utc": "2026-01-01T00:00:00+00:00",
        "pipeline_stages": {
            "train": {"status": "ok", "trained_at_utc": "2026-01-01T00:00:00+00:00"},
            "evaluate": {"status": "missing"},
            "drift_detection": {
                "status": "ok",
                "drifted_columns_count": 2,
                "drifted_columns_share": 0.1,
                "columns_above_threshold": ["pay_0", "pay_2"],
            },
        },
        "log_counts": {"INFO": 10, "WARNING": 2, "ERROR": 1},
        "model_metrics": {
            "logistic_regression": {"accuracy": 0.8175, "f1": 0.4603},
            "dummy": {"accuracy": 0.7788, "f1": 0.0},
        },
        "alerts": {"total": 2, "by_type": {"drift": 2}},
    }


@pytest.fixture
def sample_alerts() -> list[dict]:
    return [
        {
            "timestamp": "2026-01-01T00:00:01+00:00",
            "type": "drift",
            "severity": "critical",
            "column": "pay_0",
        },
        {
            "timestamp": "2026-01-01T00:00:02+00:00",
            "type": "contract_violation",
            "severity": "error",
            "batch": "invalid_batch.csv",
        },
    ]


def test_build_dashboard_html_includes_stage_status(sample_summary, sample_alerts):
    output = dashboard.build_dashboard_html(sample_summary, sample_alerts)

    assert "<html" in output
    assert "train" in output
    assert "OK" in output
    assert "NAO EXECUTADO" in output


def test_build_dashboard_html_includes_model_metrics_table(sample_summary, sample_alerts):
    output = dashboard.build_dashboard_html(sample_summary, sample_alerts)

    assert "logistic_regression" in output
    assert "0.8175" in output


def test_build_dashboard_html_includes_drifted_columns(sample_summary, sample_alerts):
    output = dashboard.build_dashboard_html(sample_summary, sample_alerts)

    assert "pay_0, pay_2" in output


def test_build_dashboard_html_includes_alerts_table(sample_summary, sample_alerts):
    output = dashboard.build_dashboard_html(sample_summary, sample_alerts)

    assert "invalid_batch.csv" in output
    assert "contract_violation" in output


def test_build_dashboard_html_handles_no_alerts(sample_summary):
    output = dashboard.build_dashboard_html(sample_summary, [])

    assert "Nenhum alerta registrado." in output


def test_build_dashboard_html_handles_no_model_metrics(sample_summary, sample_alerts):
    sample_summary["model_metrics"] = {}

    output = dashboard.build_dashboard_html(sample_summary, sample_alerts)

    assert "Nenhuma metrica de modelo disponivel." in output


def test_build_dashboard_html_escapes_html_in_values(sample_alerts):
    summary = {
        "generated_at_utc": "2026-01-01T00:00:00+00:00",
        "pipeline_stages": {
            "train": {"status": "ok", "note": "<script>alert('x')</script>"},
        },
        "log_counts": {},
        "model_metrics": {},
        "alerts": {"total": 0, "by_type": {}},
    }

    output = dashboard.build_dashboard_html(summary, [])

    assert "<script>alert" not in output
    assert "&lt;script&gt;" in output


def test_main_writes_dashboard_file(tmp_path, monkeypatch, sample_summary, sample_alerts):
    summary_path = tmp_path / "observability_summary.json"
    alerts_path = tmp_path / "alerts.json"
    dashboard_path = tmp_path / "observability_dashboard.html"

    summary_path.write_text(json.dumps(sample_summary), encoding="utf-8")
    alerts_path.write_text(json.dumps(sample_alerts), encoding="utf-8")

    monkeypatch.setattr(dashboard, "SUMMARY_PATH", summary_path)
    monkeypatch.setattr(dashboard, "ALERTS_PATH", alerts_path)
    monkeypatch.setattr(dashboard, "DASHBOARD_PATH", dashboard_path)

    dashboard.main()

    assert dashboard_path.exists()
    assert "<html" in dashboard_path.read_text(encoding="utf-8")


def test_main_raises_when_summary_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(dashboard, "SUMMARY_PATH", tmp_path / "missing.json")

    with pytest.raises(FileNotFoundError):
        dashboard.main()
