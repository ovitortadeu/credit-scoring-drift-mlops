# credit-scoring-drift-mlops

Tech Challenge Fase 4 — POS TECH.

Projeto de credit scoring com foco em detecção de drift, qualidade de dados e governança.

## Setup

```bash
uv sync
```

## Stack inicial

sklearn/XGBoost, Pandera pra data contracts, Evidently pra drift, MLflow pra tracking de experimentos.

Estrutura e divisão de papéis a definir com o time.

## Documentação

- [`docs/baseline.md`](docs/baseline.md) — modelo baseline e métricas de avaliação.
- [`docs/contratos.md`](docs/contratos.md) — contrato de dados (Pandera) e validação de lotes.
- [`docs/drift.md`](docs/drift.md) — simulação e detecção de data drift (Evidently).
- [`docs/observabilidade.md`](docs/observabilidade.md) — logs estruturados, MLflow, alertas, dashboard e CI/CD.

## Observabilidade e CI/CD

- Logs estruturados (console + JSON Lines) em todas as etapas do pipeline.
- Tracking de experimentos com MLflow (treino, avaliação, detecção e impacto de drift).
- Alertas de drift crítico e de bloqueio de contrato, consolidados em `reports/alerts.json`.
- Agregador de métricas (`src/observability/metrics.py`) e dashboard HTML estático gerado a partir dele.
- GitHub Actions (`.github/workflows/ci.yml`) roda em todo push/PR: lint (`ruff`), testes (`pytest`) e uma verificação automática de que o contrato de dados bloqueia um lote inválido.

Detalhes e comandos de reprodução em [`docs/observabilidade.md`](docs/observabilidade.md).
