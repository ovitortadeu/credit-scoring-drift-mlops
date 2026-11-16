# Validação de reprodutibilidade (Pessoa 5)

## Ambiente

| Campo | Valor |
|---|---|
| Data (UTC) | 2026-11-16 |
| SO | Linux WSL2 (`6.18.58.1-microsoft-standard-WSL2`) |
| Python | 3.12.2 (`.python-version` / `uv`) |
| Gerenciador | `uv` + `uv.lock` (`uv sync --locked --extra dev`) |
| Repo | `credit-scoring-drift-mlops` |

## Procedimento

Execução completa dos passos **0–6** do README, a partir de CSVs/modelos
ausentes localmente (apenas `data/raw/manifest.json` versionado no início).

1. `uv sync --locked --extra dev`
2. download → inspect → split
3. train → evaluate
4. simulate → validate drifted → detect → impact
5. invalid_batch → validate (espera falha)
6. metrics → dashboard
7. `pytest`

## Resultados observados

| Gate | Resultado |
|---|---|
| Download UCI | OK — SHA-256 confere com o manifesto |
| Split | reference 17999 / test 6000 / production_base 6001 |
| Métricas logística (teste) | accuracy 0.8175 · precision 0.6652 · recall 0.3519 · F1 0.4603 · ROC AUC 0.7531 |
| Lote drifted no contrato | OK (exit 0) |
| Drift crítico | 6 alertas: `pay_0`, `pay_2`, `pay_3`, `pay_4`, `pay_5`, `pay_6` |
| Impacto (acurácia base → drift) | 0.8247 → 0.7047 |
| Lote inválido | **bloqueado** — 14 violações, exit code `1` |
| Dashboard | `reports/observability_dashboard.html` gerado |
| Resumo obs. | `reports/observability_summary.json` com 7 alertas (6 drift + 1 contrato) |
| Testes | **54 passed** em ~5,5 s — nenhum skip |

## Conclusão

O pipeline é **reproduzível do zero** nesta máquina com os comandos do README.
Artefatos HTML, modelos `.joblib`, CSVs e `mlruns/` permanecem fora do Git e
foram regenerados com sucesso.

## Observações para o vídeo

- O passo de treino + MLflow pode levar alguns minutos na primeira execução.
- Para a gravação, preferir ambiente já aquecido e focar nos gates visuais
  (bloqueio do contrato, alertas, dashboard).
