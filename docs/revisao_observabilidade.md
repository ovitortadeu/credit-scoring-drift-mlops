# Revisão cruzada — observabilidade (Pessoa 5 → Pessoa 4)

Conforme o guia técnico: a Pessoa 5 deve testar a observabilidade
**do zero**. Esta nota registra o que foi exercitado em 2026-11-16.

## Procedimento

Após regenerar dados/modelo/drift (passos 1–4 do README):

```bash
uv run python -m src.observability.metrics
uv run python -m src.observability.dashboard
uv run pytest tests/test_logging_config.py tests/test_alerts.py \
  tests/test_metrics.py tests/test_dashboard.py
# opcional
uv run mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db
```

Também foi exercitado o caminho completo documentado em
[`docs/observabilidade.md`](observabilidade.md) (detect → invalid CLI →
metrics → dashboard), integrado ao pipeline 0–6.

## Resultado

| Item | Status | Evidência |
|---|---|---|
| Logs JSON Lines | OK | `logs/pipeline.log` gerado com eventos tipados |
| Alertas de drift | OK | 6 críticos em `pay_0`…`pay_6` |
| Alerta de contrato | OK | `invalid_batch.csv` bloqueado + alerta `error` |
| Agregador | OK | `reports/observability_summary.json` |
| Dashboard HTML | OK | `reports/observability_dashboard.html` abre localmente |
| MLflow tracking | OK | runs em `credit-scoring-baseline` e `credit-scoring-drift` |
| Testes P4 | OK | suite completa: **54 passed** (inclui os 4 módulos de obs.) |
| CI | OK (remoto) | workflow `ci.yml` (lint + pytest + gate do contrato) |

Detalhe da reprodutibilidade ponta a ponta:
[`docs/reproducibilidade.md`](reproducibilidade.md).

## Achados / cuidados para o vídeo

1. **`reports/alerts.json` acumula** entre execuções (`append_alerts`).
   Antes de gravar, zerar o arquivo (`echo '[]' > reports/alerts.json`) e
   rerodar `detect` + CLI do lote inválido para obter o cenário limpo
   (6 drift + 1 contrato).
2. O CI **não** baixa a UCI nem treina o modelo: cobre lint/testes e o
   gate do contrato. A demonstração visual do dashboard/MLflow é local.
3. HTML do dashboard e DB do MLflow ficam fora do Git (esperável); as
   screenshots em `docs/images/` servem de fallback na gravação.
4. Documentação da P4 está clara o suficiente para reproduzir sem
   adivinhar paths — sem bloqueadores para a entrega.

## Veredito

Observabilidade da Pessoa 4 **aprovada na revisão cruzada** da Pessoa 5
para fins do Tech Challenge. Nenhum defeito bloqueante encontrado;
único ponto operacional relevante é o acúmulo de alertas entre runs.
