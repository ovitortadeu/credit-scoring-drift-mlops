# Simulação, Detecção de Data Drift e Degradação Silenciosa

## Objetivo e escopo

Este documento descreve a frente de **Data Drift e Degradação de Modelos**: a formulação do cenário macroeconômico adverso, a mecânica da simulação sintética sobre o conjunto de produção, a detecção estatística via Evidently AI e a mensuração do impacto prático nas decisões do modelo de Credit Scoring.

Esta frente conecta o modelo baseline (Pessoa 1) e o contrato de dados (Pessoa 2) com as esteiras subsequentes de observabilidade contínua (Pessoa 4) e governança/LGPD (Pessoa 5).

---

## Onde está o código

- `src/drift/simulate.py` — Simulação de drift estocástico e controlado sobre o dataset de produção.
- `src/drift/detect.py` — Pipeline de detecção estatística com Evidently (gera HTML e JSON).
- `src/drift/impact.py` — Avaliação comparativa das predições do modelo (Base vs. Drift).
- `tests/test_drift.py` — Testes unitários de integridade, determinismo e conformidade com o contrato.
- `reports/drift_simulation.json` — Manifesto de parâmetros e SHA-256 da base gerada.
- `reports/data_drift_report.html` — Relatório visual interativo com testes de distribuição.
- `reports/data_drift_report.json` — Sumário estruturado das distâncias estatísticas.
- `reports/drift_impact_summary.json` — Comparativo numérico de desempenho e taxas de aprovação.

---

## O Cenário de Negócio: Crise Macroeconômica

No contexto de concessão de crédito, uma das maiores ameaças é a **degradação silenciosa**: o pipeline de ingestão continua aceitando os dados (pois o formato e tipos estão válidos), mas a distribuição dos clientes muda no mundo real.

Para demonstrar esse risco de forma plausível no dataset *Default of Credit Card Clients*, simulamos um choque econômico simultâneo em 3 eixos:

1. **Atraso de Pagamento (`pay_0` a `pay_6`):**
   - 40% dos clientes têm seu status de atraso agravado em 1 a 3 meses adicionais.
   - Respeita o domínio $[-2, 9]$ definido no contrato de dados.
2. **Redução do Valor Pago (`pay_amt1` a `pay_amt6`):**
   - 35% dos clientes passam a pagar apenas 30% do valor habitual (perda de renda/liquidez).
   - Mantém os valores $\ge 0$.
3. **Inflação de Faturas (`bill_amt1` a `bill_amt6`):**
   - 25% dos clientes têm suas faturas aumentadas em 50% (alta de juros e custo de vida).

A base original de produção (`data/production/production_base.csv`) é preservada intacta, gerando o lote de análise em `data/production/production_drifted.csv`.

---

## Detecção Estatística com Evidently AI

O pipeline compara o conjunto de treino histórico (`reference.csv`, 17.999 registros) com a produção sob crise (`production_drifted.csv`, 6.001 registros).

Para colunas numéricas, utilizou-se a métrica normalizada da **Distância de Wasserstein** (Earth Mover's Distance) com corte de alerta em $0.10$. Para variáveis categóricas, utilizou-se a **Distância de Jensen-Shannon**.

### Resultados por Coluna:

| Coluna | Teste Estatístico | Valor Medido | Limiar | Veredito |
|---|---|---:|---:|---|
| `pay_0` | Wasserstein norm. | **0.7231** | 0.10 | 🔴 Drift Crítico |
| `pay_2` | Wasserstein norm. | **0.6858** | 0.10 | 🔴 Drift Crítico |
| `pay_3` | Wasserstein norm. | **0.6755** | 0.10 | 🔴 Drift Crítico |
| `pay_4` | Wasserstein norm. | **0.6910** | 0.10 | 🔴 Drift Crítico |
| `pay_5` | Wasserstein norm. | **0.7053** | 0.10 | 🔴 Drift Crítico |
| `pay_6` | Wasserstein norm. | **0.7264** | 0.10 | 🔴 Drift Crítico |
| `pay_amt1..6` | Wasserstein norm. | ~0.077 - 0.084 | 0.10 | 🟡 Atenção (sub-limiar) |
| `bill_amt1..6` | Wasserstein norm. | ~0.060 - 0.067 | 0.10 | 🟢 Sem Drift |
| Demográficas (`sex`, `age`...) | Jensen-Shannon | < 0.0150 | 0.10 | 🟢 Sem Drift |

O teste comprovou com rigor estatístico que o fenômeno foi puramente comportamental (inadimplência e capacidade financeira), sem contaminação do perfil demográfico.

---

## O Impacto da Degradação Silenciosa no Modelo

Avaliamos as predições do pipeline treinado (`logistic_regression.joblib`) antes e depois do choque:

| Métrica | Base Normal (Sem Drift) | Com Data Drift | Variação / Impacto de Negócio |
|---|---:|---:|---|
| **Inadimplência Prevista** | 12,06% | **29,93%** | **+148%** (rejeição em massa) |
| **Probabilidade Média** | 0,2241 | **0,3662** | Score de risco geral sobe 63% |
| **Acurácia** | 82,47% | **70,47%** | Queda de 12 pontos percentuais |
| **Precisão** | 69,06% | **37,64%** | Falsos positivos disparam |
| **Recall** | 37,65% | **50,90%** | Modelo adota postura ultra-conservadora |
| **F1-Score** | 0,4873 | **0,4328** | Degradação global da qualidade |

### Conclusão de Negócio:
Sem quebrar nenhuma regra de formato, o modelo tornou-se excessivamente punitivo: reprovou quase o triplo de proponentes e sua precisão desabou para 37,6% (ou seja, de cada 10 clientes reprovados, mais de 6 pagariam o empréstimo em dia).

Isso comprova a necessidade mandatória de uma camada de observabilidade contínua.

---

## Como reproduzir

Executar o fluxo completo no terminal:

```powershell
# 1. Simular o cenário com drift e validar contrato
uv run python -m src.drift.simulate
uv run python -m src.validation.cli data/production/production_drifted.csv

# 2. Executar a detecção estatística via Evidently
uv run python -m src.drift.detect

# 3. Gerar o relatório de impacto no modelo
uv run python -m src.drift.impact

# 4. Rodar a suíte de testes unitários
uv run pytest tests/test_drift.py
