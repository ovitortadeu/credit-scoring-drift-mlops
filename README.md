# credit-scoring-drift-mlops

Tech Challenge Fase 4 — POS TECH.

Pipeline de **credit scoring** com contratos de dados, detecção de drift,
observabilidade e governança (LGPD / model card). Projeto acadêmico —
**não** é motor de decisão de crédito em produção.

## Papéis do time

| Pessoa | Liderança | Documentação |
|---|---|---|
| 1 | Dados e modelo baseline | [`docs/baseline.md`](docs/baseline.md) |
| 2 | Qualidade e contratos | [`docs/contratos.md`](docs/contratos.md) |
| 3 | Drift | [`docs/drift.md`](docs/drift.md) |
| 4 | Observabilidade e CI/CD | [`docs/observabilidade.md`](docs/observabilidade.md) |
| 5 | Governança e integração | [`docs/lgpd.md`](docs/lgpd.md), [`docs/model_card.md`](docs/model_card.md), [`docs/checklist.md`](docs/checklist.md) |

Roteiro de integração: [`docs/roteiro_integracao.md`](docs/roteiro_integracao.md).

## Stack

- **Modelagem:** scikit-learn (baseline `LogisticRegression` + `DummyClassifier`)
- **Contratos:** Pandera
- **Drift:** Evidently
- **Tracking / obs.:** MLflow, logs JSON Lines, dashboard HTML estático
- **Automação:** GitHub Actions (`ruff`, `pytest`, gate do contrato)
- **Ambiente:** Python ≥ 3.11, gerenciado com `uv` (`uv.lock`)

> `xgboost` aparece em `pyproject.toml` como dependência do ecossistema do
> desafio; o baseline entregue e avaliado é sklearn.

## Setup

```bash
uv sync --locked --extra dev
```

## Como rodar o projeto do zero

Execute na raiz do repositório. Ambiente de referência da validação P5:
Python 3.12 + dependências travadas em `uv.lock`.

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

**Critérios de sucesso rápidos**

| Etapa | Esperado |
|---|---|
| Passo 2 | `reports/baseline_metrics.json` com ROC AUC ≈ 0,75 na logística |
| Passo 3 | Drift crítico em `pay_0`…`pay_6` |
| Passo 4 | CLI com exit code ≠ 0 no lote inválido |
| Passo 5 | Abrir `reports/observability_dashboard.html` |
| Passo 6 | `pytest` verde (skips só se faltarem CSVs de produção) |

Opcional: `uv run mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db`

Registro da validação P5: [`docs/reproducibilidade.md`](docs/reproducibilidade.md).

## Documentação

### Técnicas (P1–P4)

- [`docs/baseline.md`](docs/baseline.md) — dados, split, treino e métricas
- [`docs/contratos.md`](docs/contratos.md) — contrato Pandera e validação de lotes
- [`docs/drift.md`](docs/drift.md) — simulação e detecção de data drift
- [`docs/observabilidade.md`](docs/observabilidade.md) — logs, MLflow, alertas, dashboard, CI

### Governança e integração (P5)

- [`docs/lgpd.md`](docs/lgpd.md) — privacidade e finalidade
- [`docs/retencao.md`](docs/retencao.md) — ciclo de vida dos artefatos
- [`docs/vieses.md`](docs/vieses.md) — riscos de viés e o que não foi medido
- [`docs/model_card.md`](docs/model_card.md) — model card do baseline
- [`docs/checklist.md`](docs/checklist.md) — checklist final da entrega
- [`docs/revisao_observabilidade.md`](docs/revisao_observabilidade.md) — cross-review da P4

## Observabilidade e CI/CD

- Logs estruturados (console + JSON Lines) em todas as etapas do pipeline
- Tracking com MLflow (treino, avaliação, detecção e impacto de drift)
- Alertas de drift crítico e bloqueio de contrato em `reports/alerts.json`
- Dashboard HTML gerado por `src.observability.dashboard`
- GitHub Actions (`.github/workflows/ci.yml`): lint, testes e verificação de que o contrato bloqueia lote inválido

## Limitações (leitura obrigatória)

- Dataset histórico (Taiwan); não representa o mercado brasileiro atual
- Atributos demográficos entram no modelo; **não há métricas de equidade por grupo**
- Recall da logística é baixo (~0,35); acurácia sozinha engana
- Sem validação temporal
- Drift de produção é **simulado**
- Uso real de crédito exigiria nova análise jurídica, fairness e monitoramento contínuo

Detalhes: [`docs/vieses.md`](docs/vieses.md), [`docs/lgpd.md`](docs/lgpd.md), [`docs/model_card.md`](docs/model_card.md).

## Dataset

- **Default of Credit Card Clients** — UCI 350, DOI [10.24432/C55S3H](https://doi.org/10.24432/C55S3H), licença CC BY 4.0
- Procedência e hash: `data/raw/manifest.json`
