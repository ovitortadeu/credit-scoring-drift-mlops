# Avaliacao inicial dos modelos

Conjunto: teste. Registros: 6000.

Classe positiva: 1 (inadimplencia).
Previsoes obtidas com predict, sem ajuste de limiar no teste.
Precision sem previsoes positivas e registrada como zero por convencao.

| Modelo | Acuracia | Precision | Recall | F1 | ROC AUC |
|---|---:|---:|---:|---:|---:|
| logistic_regression | 0.8175 | 0.6652 | 0.3519 | 0.4603 | 0.7531 |
| dummy | 0.7788 | 0.0000 | 0.0000 | 0.0000 | 0.5000 |

## Matriz de confusao de logistic_regression

| Classe real | Previsto 0 | Previsto 1 |
|---|---:|---:|
| Real 0 | 4438 | 235 |
| Real 1 | 860 | 467 |

## Matriz de confusao de dummy

| Classe real | Previsto 0 | Previsto 1 |
|---|---:|---:|
| Real 0 | 4673 | 0 |
| Real 1 | 1327 | 0 |

## Limites da avaliacao

Esta avaliacao usa dados historicos separados por grupos de perfis.
Nao representa validacao temporal nem autorizacao para uso real.
O conjunto de producao simulada nao foi utilizado.
