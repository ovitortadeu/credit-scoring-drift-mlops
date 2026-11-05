"""Regras de alerta para drift critico e bloqueio do contrato de dados.

Os alertas nao disparam notificacoes externas: eles sao registrados no log
estruturado (via `src.observability.logging_config`) e acumulados em
`reports/alerts.json`, que o agregador de metricas (`src/observability/metrics.py`)
consome para compor a visao de saude do pipeline.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.observability.logging_config import setup_logging

logger = setup_logging(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ALERTS_PATH = PROJECT_ROOT / "reports" / "alerts.json"

# Tipo de metrica do Evidently que compara uma coluna entre referencia e
# producao (ver `evidently.presets.DataDriftPreset`).
DRIFT_VALUE_METRIC_TYPE = "evidently:metric_v2:ValueDrift"


def check_drift_alerts(drift_report: dict[str, Any]) -> list[dict[str, Any]]:
    """Varre o relatorio JSON do Evidently e gera um alerta por coluna acima do limiar."""
    alerts = []

    for metric in drift_report.get("metrics", []):
        config = metric.get("config", {})
        if config.get("type") != DRIFT_VALUE_METRIC_TYPE:
            continue

        column = config.get("column")
        threshold = config.get("threshold")
        value = metric.get("value")

        if value is None or threshold is None or value <= threshold:
            continue

        alert = {
            "timestamp": datetime.now(UTC).isoformat(),
            "type": "drift",
            "severity": "critical",
            "column": column,
            "value": value,
            "threshold": threshold,
            "method": config.get("method"),
        }
        alerts.append(alert)

        logger.warning(
            "Drift critico detectado em %s (valor=%.4f, limiar=%.2f)",
            column,
            value,
            threshold,
            extra={"event": "drift_alert", "data": alert},
        )

    return alerts


def check_contract_alert(batch_name: str, violation_count: int) -> dict[str, Any] | None:
    """Gera um alerta quando um lote e bloqueado pelo contrato de dados."""
    if violation_count <= 0:
        return None

    alert = {
        "timestamp": datetime.now(UTC).isoformat(),
        "type": "contract_violation",
        "severity": "error",
        "batch": batch_name,
        "violation_count": violation_count,
    }

    logger.error(
        "Lote %s bloqueado pelo contrato (%d violacoes)",
        batch_name,
        violation_count,
        extra={"event": "contract_alert", "data": alert},
    )

    return alert


def save_alerts(alerts: list[dict[str, Any]]) -> None:
    """Acrescenta os alertas gerados nesta execucao a reports/alerts.json."""
    if not alerts:
        return

    ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)

    existing: list[dict[str, Any]] = []
    if ALERTS_PATH.exists():
        existing = json.loads(ALERTS_PATH.read_text(encoding="utf-8"))

    existing.extend(alerts)
    ALERTS_PATH.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
