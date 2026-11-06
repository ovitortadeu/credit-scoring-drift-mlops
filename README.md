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

## Como rodar o projeto do zero

Execute os comandos na raiz do repositório. Ambiente utilizado: Python 3.12.2 (dependências em `uv.lock`).

```bash
# 0. Instalar dependencias
uv sync --locked --extra dev

# 1. Obter e preparar os dados (baixa o dataset da UCI)
uv run python -m src.data.download
uv run python -m src.data.inspect_data
uv run python -m src.data.split

# 2. Treinar e avaliar o modelo baseline
uv run python -m src.models.train
uv run python -m src.models.evaluate

# 3. Simular e detectar drift, e avaliar o impacto no modelo
uv run python -m src.drift.simulate
uv run python -m src.validation.cli data/production/production_drifted.csv
uv run python -m src.drift.detect
uv run python -m src.drift.impact

# 4. Demonstrar o bloqueio do contrato de dados
uv run python -m src.validation.invalid_batch
uv run python -m src.validation.cli data/production/invalid_batch.csv

# 5. Consolidar metricas de observabilidade e gerar o dashboard
uv run python -m src.observability.metrics
uv run python -m src.observability.dashboard

# 6. Rodar a suite de testes completa
uv run pytest
```

Ao final, abra `reports/observability_dashboard.html` no navegador para ver o status consolidado do pipeline, ou rode `uv run mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db` para ver os experimentos rastreados. Detalhes de cada etapa estão nos documentos linkados acima.

## Observabilidade e CI/CD

- Logs estruturados (console + JSON Lines) em todas as etapas do pipeline.
- Tracking de experimentos com MLflow (treino, avaliação, detecção e impacto de drift).
- Alertas de drift crítico e de bloqueio de contrato, consolidados em `reports/alerts.json`.
- Agregador de métricas (`src/observability/metrics.py`) e dashboard HTML estático gerado a partir dele.
- GitHub Actions (`.github/workflows/ci.yml`) roda em todo push/PR: lint (`ruff`), testes (`pytest`) e uma verificação automática de que o contrato de dados bloqueia um lote inválido.

Detalhes e comandos de reprodução em [`docs/observabilidade.md`](docs/observabilidade.md).
