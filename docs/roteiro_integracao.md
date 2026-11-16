# Roteiro de integração

## Objetivo

Definir a ordem de dependências entre as frentes P1–P5, os artefatos de
handoff e o critério de “pronto” para a entrega integrada do Tech Challenge.

## Papéis

| Pessoa | Liderança | Entrega principal |
|---|---|---|
| 1 | Dados e modelo baseline | Dataset, split, treino, avaliação |
| 2 | Qualidade e contratos | Schema Pandera, CLI, lote inválido |
| 3 | Drift | Simulação, Evidently, impacto no modelo |
| 4 | Observabilidade e automação | Logs, alertas, MLflow, dashboard, CI |
| 5 | Governança e integração | README, LGPD/model card, checklist, vídeo |

## Grafo de dependências

```text
P1 (dados + baseline)
 ├─► P2 (contrato consome schema/colunas do baseline)
 ├─► P3 (drift consome referência/produção e modelo)
 │     └─► P4 (alertas/dashboard/MLflow consomem P2+P3)
 └─► P5 (documenta e valida o conjunto integrado)
       └─► vídeo STAR + checklist final
```

Ordem recomendada de merge/integração:

1. Baseline reproduzível (P1)
2. Contrato bloqueando lote inválido (P2)
3. Simulação + detecção + impacto de drift (P3)
4. Logs, alertas, dashboard, CI (P4)
5. Governança, README consolidado, checklist e vídeo (P5)

## Handoffs por artefato

| De → Para | Artefato / contrato de interface |
|---|---|
| P1 → P2 | Nomes de colunas, ranges e categorias documentados em `docs/baseline.md` |
| P1 → P3 | `data/reference`, `data/production/production_base.csv`, modelo `.joblib` |
| P1 → P5 | Métricas, limitações, nota sobre atributos demográficos |
| P2 → P4 | `SchemaErrors` / bloqueio via CLI para alerta de contrato |
| P3 → P4 | `reports/data_drift_report.json` e limiar 0,10 |
| P4 → P5 | `docs/observabilidade.md`, dashboard, CI verde |
| P5 → time | README único, checklist, roteiro de gravação |

## Critério de integração “done”

- [ ] Comandos do README (passos 0–6) concluem sem erro manual não documentado
- [ ] Lote inválido é bloqueado (`src.validation.cli` exit ≠ 0)
- [ ] Drift crítico gera alertas esperados (`pay_0`…`pay_6`)
- [ ] Dashboard HTML abre e resume saúde do pipeline
- [ ] CI GitHub Actions verde em `main`
- [ ] Docs de governança linkadas no README
- [ ] Checklist final assinado pelo time (ou pela Pessoa 5 na entrega)

## Revisão cruzada obrigatória (guia técnico)

| Quem | O que revisa |
|---|---|
| Pessoa 5 | Observabilidade da Pessoa 4 **do zero** (ver `docs/revisao_observabilidade.md`) |
| Pessoa 1 | Confirma que README/governança da Pessoa 5 representam o código real |

## Manutenção deste roteiro

Qualquer mudança de interface (colunas, limiares, paths de report) deve
atualizar este arquivo e o checklist na mesma PR.
