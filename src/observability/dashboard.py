"""Gera um dashboard HTML estatico consolidando a saude do pipeline.

Le `reports/observability_summary.json` (produzido por
`src/observability/metrics.py`) e `reports/alerts.json`, e renderiza um
unico arquivo HTML autocontido (sem dependencias externas de JS/CSS) em
`reports/observability_dashboard.html`.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from src.observability.logging_config import setup_logging
from src.observability.metrics import ALERTS_PATH, SUMMARY_PATH

logger = setup_logging(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_PATH = PROJECT_ROOT / "reports" / "observability_dashboard.html"

_STATUS_LABELS = {"ok": "OK", "missing": "NAO EXECUTADO"}


def _escape(value: Any) -> str:
    return html.escape(str(value))


def _render_stage_cards(stages: dict[str, dict]) -> str:
    cards = []
    for stage_name, stage_data in stages.items():
        status = stage_data.get("status", "missing")
        css_class = "ok" if status == "ok" else "missing"
        label = _STATUS_LABELS.get(status, status)

        details = "".join(
            f"<li><strong>{_escape(key)}:</strong> {_escape(value)}</li>"
            for key, value in stage_data.items()
            if key != "status"
        )

        cards.append(
            f'<div class="card {css_class}">'
            f"<h3>{_escape(stage_name)}</h3>"
            f'<span class="badge {css_class}">{_escape(label)}</span>'
            f"<ul>{details}</ul>"
            "</div>"
        )
    return "".join(cards)


def _render_model_metrics_table(model_metrics: dict[str, dict]) -> str:
    if not model_metrics:
        return "<p>Nenhuma metrica de modelo disponivel.</p>"

    metric_names = sorted({name for metrics in model_metrics.values() for name in metrics})
    header = "".join(f"<th>{_escape(name)}</th>" for name in metric_names)

    rows = []
    for model_name, metrics in model_metrics.items():
        cells = "".join(
            f"<td>{metrics[name]:.4f}</td>" if name in metrics else "<td>-</td>"
            for name in metric_names
        )
        rows.append(f"<tr><td>{_escape(model_name)}</td>{cells}</tr>")

    return (
        "<table><thead><tr><th>Modelo</th>"
        f"{header}</tr></thead><tbody>{''.join(rows)}</tbody></table>"
    )


def _render_alerts_table(alerts: list[dict]) -> str:
    if not alerts:
        return "<p>Nenhum alerta registrado.</p>"

    rows = []
    for alert in alerts:
        rows.append(
            "<tr>"
            f"<td>{_escape(alert.get('timestamp', '-'))}</td>"
            f"<td>{_escape(alert.get('type', '-'))}</td>"
            f"<td>{_escape(alert.get('severity', '-'))}</td>"
            f"<td>{_escape(alert.get('column') or alert.get('batch') or '-')}</td>"
            "</tr>"
        )

    return (
        "<table><thead><tr><th>Timestamp</th><th>Tipo</th><th>Severidade</th>"
        f"<th>Origem</th></tr></thead><tbody>{''.join(rows)}</tbody></table>"
    )


def build_dashboard_html(summary: dict[str, Any], alerts: list[dict[str, Any]]) -> str:
    """Monta o HTML completo do dashboard a partir do resumo e dos alertas."""
    drift_stage = summary.get("pipeline_stages", {}).get("drift_detection", {})
    drifted_columns = ", ".join(drift_stage.get("columns_above_threshold", []) or []) or "nenhuma"

    log_counts = summary.get("log_counts", {})
    alerts_summary = summary.get("alerts", {})

    return f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<title>Observabilidade — Credit Scoring</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, sans-serif; margin: 2rem; background: #0f172a; color: #e2e8f0; }}
  h1 {{ font-size: 1.5rem; }}
  h2 {{ margin-top: 2rem; border-bottom: 1px solid #334155; padding-bottom: 0.25rem; }}
  .meta {{ color: #94a3b8; font-size: 0.9rem; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-top: 1rem; }}
  .card {{ background: #1e293b; border-radius: 8px; padding: 1rem; border: 1px solid #334155; }}
  .card h3 {{ margin: 0 0 0.5rem 0; text-transform: capitalize; }}
  .card ul {{ list-style: none; padding: 0; margin: 0.5rem 0 0 0; font-size: 0.85rem; color: #cbd5e1; }}
  .badge {{ display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }}
  .badge.ok {{ background: #14532d; color: #86efac; }}
  .badge.missing {{ background: #450a0a; color: #fca5a5; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 0.5rem; }}
  th, td {{ border: 1px solid #334155; padding: 0.4rem 0.6rem; text-align: left; font-size: 0.85rem; }}
  th {{ background: #1e293b; }}
  .stat-row {{ display: flex; gap: 1.5rem; margin-top: 0.5rem; }}
  .stat {{ background: #1e293b; border-radius: 8px; padding: 0.75rem 1rem; border: 1px solid #334155; }}
  .stat strong {{ display: block; font-size: 1.4rem; }}
</style>
</head>
<body>
  <h1>Observabilidade — Credit Scoring</h1>
  <p class="meta">Gerado em: {_escape(summary.get("generated_at_utc", "-"))}</p>

  <h2>Saude do pipeline</h2>
  <div class="grid">{_render_stage_cards(summary.get("pipeline_stages", {}))}</div>

  <h2>Logs estruturados</h2>
  <div class="stat-row">
    <div class="stat">INFO<strong>{log_counts.get("INFO", 0)}</strong></div>
    <div class="stat">WARNING<strong>{log_counts.get("WARNING", 0)}</strong></div>
    <div class="stat">ERROR<strong>{log_counts.get("ERROR", 0)}</strong></div>
  </div>

  <h2>Metricas dos modelos (conjunto de teste)</h2>
  {_render_model_metrics_table(summary.get("model_metrics", {}))}

  <h2>Drift detectado</h2>
  <p>Colunas acima do limiar: <strong>{_escape(drifted_columns)}</strong></p>

  <h2>Alertas ({alerts_summary.get("total", 0)} no total)</h2>
  {_render_alerts_table(alerts)}
</body>
</html>
"""


def main() -> None:
    logger.info("Gerando dashboard de observabilidade", extra={"event": "dashboard_started"})

    if not SUMMARY_PATH.exists():
        raise FileNotFoundError(
            f"{SUMMARY_PATH} nao existe. Rode 'python -m src.observability.metrics' antes."
        )

    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    alerts = json.loads(ALERTS_PATH.read_text(encoding="utf-8")) if ALERTS_PATH.exists() else []

    dashboard_html = build_dashboard_html(summary, alerts)

    DASHBOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    DASHBOARD_PATH.write_text(dashboard_html, encoding="utf-8")

    print(f"Dashboard salvo em: {DASHBOARD_PATH}")

    logger.info(
        "Dashboard de observabilidade gerado",
        extra={"event": "dashboard_completed", "data": {"path": str(DASHBOARD_PATH)}},
    )


if __name__ == "__main__":
    main()
