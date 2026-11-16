# Vieses, equidade e riscos de uso

## Objetivo

Registrar os riscos de viés associados ao baseline de credit scoring e o
que **não** foi avaliado neste Tech Challenge — de forma explícita para
o vídeo, o README e o model card.

## Atributos demográficos no modelo

O baseline utiliza, entre outras, as features:

- `sex`
- `education`
- `marriage`
- `age`

Esses campos podem funcionar como proxies de grupos protegidos e, em um
contexto real de crédito, exigiriam análise de impacto discriminatório
(direto ou indireto).

Fonte da decisão de escopo: handoff da Pessoa 1 em
[`docs/baseline.md`](baseline.md) (seção Documentação e governança).

## O que foi e o que não foi feito

| Avaliação | Status |
|---|---|
| Métricas globais (accuracy, precision, recall, F1, ROC AUC) | Feito |
| Comparação com classificador dummy (classe majoritária) | Feito |
| Métricas por grupo (`sex`, `education`, `marriage`, faixas de `age`) | **Não realizado** |
| Paridade demográfica / equalized odds / calibration por grupo | **Não realizado** |
| Remoção ou mitigação de features sensíveis | **Não realizado** |
| Validação temporal (treino passado → teste futuro) | **Não realizado** |

## Riscos conhecidos

1. **Baixo recall (~0,35) da regressão logística:** o modelo deixa de
   identificar grande parte dos inadimplentes. Em produção isso pode
   gerar perda de crédito; o oposto (muitos falsos positivos) geraria
   exclusão indevida de bons pagadores — ambos têm impacto social.
2. **Desbalanceamento de classes** (~22% positivos): métricas de acurácia
   sozinhas são insuficientes; por isso o projeto reporta F1 e ROC AUC.
3. **Contexto geográfico e histórico:** dados de Taiwan (anos 2000) não
   representam o mercado brasileiro atual.
4. **Drift simulado:** a crise macroeconômica altera padrões de
   pagamento (`pay_*`). Sem monitoramento, o desempenho e o perfil de
   erros podem degradar de forma silenciosa — inclusive de maneira
   desigual entre grupos (não medido aqui).

## Controles indiretos já presentes no pipeline

Embora não substituam fairness metrics, o pipeline reduz alguns riscos
operacionais:

- **Contrato Pandera (Pessoa 2):** bloqueia lotes inválidos antes da
  decisão.
- **Detecção de drift (Pessoa 3):** evidencia mudança de distribuição.
- **Alertas e dashboard (Pessoa 4):** tornam a degradação visível.
- **Governança (Pessoa 5):** documenta limitações e proíbe uso como
  motor real de crédito sem nova análise.

## Posição do projeto

O modelo é um **baseline acadêmico**. Qualquer uso real exigiria, no
mínimo: avaliação de equidade por grupo, validação temporal, revisão
jurídica/LGPD e governança de mudança de modelo.
