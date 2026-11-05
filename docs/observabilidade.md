# Observabilidade e Automação

## Objetivo e escopo

Este documento descreve a frente de **Observabilidade de Pipelines e Modelos**: a padronização de logs estruturados, o tracking de experimentos com MLflow, a consolidação de métricas de saúde do pipeline, as regras de alerta para drift crítico e bloqueio de contrato, o dashboard HTML gerado a partir desses dados e a automação de testes/verificações via GitHub Actions.

Esta frente consome o trabalho das demais: o modelo baseline (Pessoa 1), o contrato de dados (Pessoa 2) e a simulação/detecção de drift (Pessoa 3). Não cobre o treino do modelo, as regras de validação em si, nem a documentação de governança/LGPD, que pertencem às outras frentes.

---

## Onde está o código

- `src/observability/logging_config.py` — configuração central de logging estruturado (console + JSON Lines).
- `src/observability/alerts.py` — regras de alerta para drift crítico e bloqueio de contrato.
- `src/observability/metrics.py` — agregador de métricas de observabilidade.
- `src/observability/tracking.py` — configuração central do MLflow (tracking store local via SQLite).
- `src/observability/dashboard.py` — gerador do dashboard HTML estático.
- `tests/test_logging_config.py`, `tests/test_alerts.py`, `tests/test_metrics.py`, `tests/test_dashboard.py` — testes unitários de cada módulo.
- `reports/alerts.json` — alertas acumulados, gerados em runtime.
- `reports/observability_summary.json` — resumo consolidado de saúde do pipeline.
- `reports/observability_dashboard.html` — dashboard visual (gerado em runtime, não versionado).
- `.github/workflows/ci.yml` — workflow de lint, testes e verificação do contrato de dados.

---

## Logging estruturado

Cada etapa do pipeline (`src.models.train`, `src.models.evaluate`, `src.validation.cli`, `src.validation.invalid_batch`, `src.drift.simulate`, `src.drift.detect`, `src.drift.impact`) chama `setup_logging(__name__)` para obter um logger que escreve simultaneamente:

- no console, em texto legível, para acompanhamento humano durante a execução;
- em `logs/pipeline.log` (fora do Git, como os demais artefatos de runtime), uma linha JSON por evento, com `timestamp`, `level`, `logger`, `module`, `message` e campos extras específicos do evento (`event`, `data`).

O formato JSON Lines foi escolhido por ser trivialmente parseável (uma linha = um registro) tanto por ferramentas de linha de comando (`jq`, `grep`) quanto pelo agregador de métricas, sem exigir um backend de logging externo.

### Eventos registrados

| Evento | Onde | Nível |
|---|---|---|
| `train_started` / `train_completed` | `src.models.train` | INFO |
| `model_train_started` / `model_train_completed` | `src.models.train` | INFO |
| `data_contract_passed` | `src.models.train`, `src.models.evaluate` | INFO |
| `evaluation_started` / `evaluation_completed` | `src.models.evaluate` | INFO |
| `model_evaluated` | `src.models.evaluate` | INFO |
| `validation_passed` | `src.validation.cli` | INFO |
| `validation_blocked` | `src.validation.cli` | ERROR |
| `invalid_batch_generated` | `src.validation.invalid_batch` | INFO |
| `drift_simulation_started` / `drift_simulation_completed` | `src.drift.simulate` | INFO |
| `drift_detection_started` / `drift_detection_completed` | `src.drift.detect` | INFO |
| `drift_impact_started` / `drift_impact_completed` | `src.drift.impact` | INFO |
| `drift_alert` | `src.observability.alerts` | WARNING |
| `contract_alert` | `src.observability.alerts` | ERROR |

---

## Regras de alerta

Os alertas não disparam notificações externas (e-mail, Slack etc.): eles são registrados no log estruturado e acumulados em `reports/alerts.json`, que serve de evidência auditável e de insumo para o agregador de métricas e o dashboard.

Duas regras estão implementadas:

1. **Drift crítico** (`check_drift_alerts`): varre o relatório JSON do Evidently e gera um alerta de severidade `critical` para cada coluna cujo valor do teste estatístico (Wasserstein normalizada ou Jensen-Shannon) ultrapassa o limiar de `0.10` definido pela Pessoa 3 em `docs/drift.md`. No cenário de crise macroeconômica simulado, isso produz 6 alertas (`pay_0` a `pay_6`).
2. **Bloqueio de contrato** (`check_contract_alert`): gera um alerta de severidade `error` sempre que `src.validation.cli` encontra violações do contrato Pandera em um lote.

Essas regras reutilizam diretamente a saída das Pessoas 2 e 3 (o relatório Evidently e o `SchemaErrors.failure_cases`), sem recalcular nada.

---

## Tracking de experimentos com MLflow

`src/observability/tracking.py` centraliza a configuração do MLflow, apontando para um tracking store SQLite local (`mlruns/mlflow.db`) — o backend de arquivo puro está em modo de manutenção a partir do MLflow 3.x e não recebe mais atualizações.

Dois experimentos são usados:

- **`credit-scoring-baseline`**: um run pai `train` com um run aninhado por modelo (parâmetros, `training_seconds`, artefato do modelo via `mlflow.sklearn.log_model`), e um run pai `evaluate` com um run aninhado por modelo (métricas de acurácia, precisão, recall, F1 e ROC AUC).
- **`credit-scoring-drift`**: um run `drift-detection` (contagem/percentual de colunas com drift, alertas gerados, artefatos HTML/JSON do Evidently) e um run `drift-impact` (métricas de base vs. produção com drift, artefato do resumo).

`mlruns/` fica fora do Git (gerado em runtime, como `logs/` e `models/`).

### Como visualizar

```bash
uv run mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db
```

---

## Agregador de métricas

`src/observability/metrics.py` lê os relatórios JSON de cada etapa (`training_summary.json`, `baseline_metrics.json`, `drift_simulation.json`, `data_drift_report.json`, `drift_impact_summary.json`) e `reports/alerts.json`, e produz `reports/observability_summary.json` com:

- `pipeline_stages`: status (`ok`/`missing`) e campos-chave de cada etapa;
- `log_counts`: contagem de linhas de log por nível, a partir de `logs/pipeline.log`;
- `model_metrics`: métricas de avaliação por modelo;
- `alerts`: total de alertas e contagem por tipo.

Esse JSON é a única fonte de dados consultada pelo dashboard — qualquer etapa ausente (por exemplo, se o drift ainda não foi detectado) aparece como `{"status": "missing"}`, sem quebrar a agregação.

---

## Dashboard HTML

`src/observability/dashboard.py` renderiza `reports/observability_summary.json` e `reports/alerts.json` em um único arquivo HTML autocontido (sem dependências externas de JS/CSS), com cartões de status por etapa, contagem de logs por nível, tabela de métricas dos modelos, colunas com drift e tabela de alertas.

O HTML gerado não é versionado (`reports/*.html` está no `.gitignore`, mesmo padrão do relatório do Evidently), mas é reprodutível a qualquer momento a partir dos JSONs commitados.

---

## Automação de testes e verificações (CI/CD)

`.github/workflows/ci.yml` roda em todo push e pull request, com dois jobs:

1. **lint-and-test**: `ruff check`, `ruff format --check` e `pytest` via `uv`.
2. **data-contract-check**: gera o lote inválido (`src.validation.invalid_batch`) e confirma que `src.validation.cli` o bloqueia com exit code 1 — demonstrando em CI o mesmo gate de qualidade de dados documentado em `docs/contratos.md`, sem depender do dataset real da UCI (que não está versionado).

---

## Como reproduzir

Executar o fluxo completo no terminal, após rodar o pipeline de dados, treino e drift (ver `docs/baseline.md`, `docs/contratos.md` e `docs/drift.md`):

```bash
# 1. Gerar alertas a partir da validacao e da deteccao de drift
uv run python -m src.validation.cli data/production/invalid_batch.csv
uv run python -m src.drift.detect

# 2. Consolidar metricas de observabilidade
uv run python -m src.observability.metrics

# 3. Gerar o dashboard HTML
uv run python -m src.observability.dashboard

# 4. Rodar a suite de testes da frente de observabilidade
uv run pytest tests/test_logging_config.py tests/test_alerts.py tests/test_metrics.py tests/test_dashboard.py
```
