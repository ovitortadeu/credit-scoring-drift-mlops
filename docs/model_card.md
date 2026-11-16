# Model Card — Credit Scoring Baseline

Modelo de referência do Tech Challenge Fase 4 (POS TECH).
Estrutura inspirada em Mitchell et al. (2019), Model Cards for Model Reporting.

## 1. Detalhes do modelo

| Campo | Valor |
|---|---|
| Nome | `logistic_regression` (pipeline sklearn) |
| Versão do projeto | `0.1.0` |
| Tipo | Classificação binária (inadimplência no mês seguinte) |
| Framework | scikit-learn (`Pipeline` com pré-processamento + `LogisticRegression`) |
| Baseline de comparação | `DummyClassifier` (estratégia de classe majoritária) |
| Artefato | `models/logistic_regression.joblib` (gerado em runtime) |
| Owners acadêmicos | Time do repositório; governança consolidada pela Pessoa 5 |
| Licença do código | MIT (`pyproject.toml`) |
| Licença dos dados | CC BY 4.0 (UCI) |

## 2. Intenção de uso

**Uso pretendido**

- Demonstrar um pipeline MLOps: dados → treino → contrato → drift →
  observabilidade → governança.
- Servir de baseline para medir impacto de data drift simulado.

**Uso fora de escopo**

- Decisão automatizada de concessão de crédito a pessoas reais.
- Scoring em mercados distintos do contexto histórico da base.
- Substituição de análise de crédito humana ou de modelos regulados.

## 3. Dados de treinamento

| Campo | Valor |
|---|---|
| Dataset | Default of Credit Card Clients (UCI 350) |
| DOI | https://doi.org/10.24432/C55S3H |
| Citação | Yeh, I. (2009). Default of Credit Card Clients [Dataset]. UCI Machine Learning Repository. |
| Linhas totais | 30.000 |
| Treino/referência | 17.999 (`StratifiedGroupKFold`, seed 42) |
| Teste | 6.000 |
| Produção base (simulação) | ~6.001 |
| Alvo | `default_next_month` (1 = inadimplência) |
| Procedência | `data/raw/manifest.json` (SHA-256 do CSV registrado) |

Detalhes de preparação: [`docs/baseline.md`](baseline.md).

## 4. Métricas (conjunto de teste)

Fonte: `reports/baseline_metrics.json` / `reports/baseline_report.md`.

| Modelo | Accuracy | Precision | Recall | F1 | ROC AUC |
|---|---:|---:|---:|---:|---:|
| logistic_regression | 0.8175 | 0.6652 | 0.3519 | 0.4603 | 0.7531 |
| dummy | 0.7788 | 0.0000 | 0.0000 | 0.0000 | 0.5000 |

Regra de predição: `pipeline.predict` sem ajuste de limiar no teste.

## 5. Fatores éticos e limitações

- Inclui atributos demográficos; **não há avaliação de equidade por grupo**.
- Recall baixo: muitos inadimplentes não são detectados.
- Sem validação temporal.
- Dados históricos de outro país/época.
- Drift de produção é **simulado** (cenário de crise), não telemetria real.

Ver [`docs/vieses.md`](vieses.md) e [`docs/lgpd.md`](lgpd.md).

## 6. Monitoramento associado

| Sinal | Onde |
|---|---|
| Contrato de dados | Pandera + `src.validation.cli` |
| Data drift | Evidently (`pay_0`…`pay_6` acima do limiar 0,10 no cenário demo) |
| Alertas | `reports/alerts.json` (6 drift + 1 contrato no cenário esperado) |
| Dashboard | `reports/observability_dashboard.html` |
| Experimentos | MLflow (`credit-scoring-baseline`, `credit-scoring-drift`) |

## 7. Como reproduzir o artefato

Seguir o README (passos 0–2) ou:

```bash
uv sync --locked --extra dev
uv run python -m src.data.download
uv run python -m src.data.inspect_data
uv run python -m src.data.split
uv run python -m src.models.train
uv run python -m src.models.evaluate
```

Validação registrada em [`docs/reproducibilidade.md`](reproducibilidade.md).
