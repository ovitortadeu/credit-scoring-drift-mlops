# Checklist final da entrega

Tech Challenge Fase 4 — credit-scoring-drift-mlops.
Responsável pela consolidação: **Pessoa 5** (governança e integração).

Marque cada item após validar. Itens técnicos dependem das frentes P1–P4;
itens de governança/vídeo são da Pessoa 5.

**Status P5 (2026-11-16):** docs de governança, README consolidado, roteiros,
reprodutibilidade e revisão da observabilidade publicados no repositório.
Resta gravar/entregar o **vídeo** e pedir à Pessoa 1 a confirmação cruzada
do README/governança vs. código.

## Pessoa 1 — Dados e baseline

- [ ] Download UCI reproduzível (`src.data.download` + `manifest.json`)
- [ ] Split documentado e gerado (`src.data.split`)
- [ ] Modelo treinado e avaliado (`reports/baseline_metrics.json`)
- [ ] `docs/baseline.md` atualizado
- [ ] Limitações (recall, demografia, sem validação temporal) comunicadas à P5

## Pessoa 2 — Qualidade e contratos

- [ ] Schema Pandera alinhado às decisões do baseline
- [ ] CLI valida lote válido e bloqueia inválido
- [ ] `docs/contratos.md` atualizado
- [ ] Testes de schema/contrato passando

## Pessoa 3 — Drift

- [ ] Simulação de crise macroeconômica
- [ ] Relatório Evidently gerado
- [ ] Impacto no modelo medido
- [ ] `docs/drift.md` atualizado
- [ ] Testes de drift (com skip documentado se faltar CSV de produção)

## Pessoa 4 — Observabilidade e CI/CD

- [ ] Logs estruturados em `logs/pipeline.log`
- [ ] Alertas em `reports/alerts.json`
- [ ] MLflow local funcional
- [ ] Dashboard HTML gerado
- [ ] GitHub Actions: lint + pytest + gate do contrato
- [ ] `docs/observabilidade.md` atualizado

## Pessoa 5 — Governança e integração

- [ ] README consolidado (papéis, fluxo, limitações, links)
- [ ] [`docs/lgpd.md`](lgpd.md)
- [ ] [`docs/retencao.md`](retencao.md)
- [ ] [`docs/vieses.md`](vieses.md)
- [ ] [`docs/model_card.md`](model_card.md)
- [ ] [`docs/roteiro_integracao.md`](roteiro_integracao.md)
- [ ] [`docs/reproducibilidade.md`](reproducibilidade.md) preenchido após rodar do zero
- [ ] [`docs/revisao_observabilidade.md`](revisao_observabilidade.md) (cross-review P4)
- [ ] Vídeo do projeto gravado e entregue conforme o edital (roteiro STAR local, fora do Git)

## Gates “pronto para gravar”

- [ ] Pipeline 0–6 do README executado com sucesso nesta máquina
- [ ] `pytest` verde (ou skips conhecidos documentados)
- [ ] Abrir `reports/observability_dashboard.html`
- [ ] Mostrar bloqueio do `invalid_batch.csv`
- [ ] Mostrar alertas de drift (6 colunas `pay_*`)
- [ ] CI recente em `main` com status de sucesso
- [ ] Pessoa 1 avisada para revisar se README/governança batem com o código

## Critérios numéricos esperados (cenário demo)

| Sinal | Esperado |
|---|---|
| ROC AUC logística (teste) | ≈ 0,75 |
| Alertas de drift crítico | 6 (`pay_0`…`pay_6`) |
| Alerta de contrato (lote inválido) | ≥ 1 |
| Exit code CLI no lote inválido | ≠ 0 |
