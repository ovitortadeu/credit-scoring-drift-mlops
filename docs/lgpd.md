# LGPD e privacidade de dados

## Objetivo e escopo

Este documento registra as decisões de privacidade do projeto acadêmico
**credit-scoring-drift-mlops** (Tech Challenge Fase 4 — POS TECH), sob a
perspectiva da Lei Geral de Proteção de Dados (Lei nº 13.709/2018).

O projeto **não** opera em produção bancária real. Trata-se de demonstração
de pipeline MLOps com dataset público de pesquisa.

## Natureza dos dados

| Aspecto | Situação no projeto |
|---|---|
| Fonte | UCI Machine Learning Repository — dataset 350 |
| Nome | Default of Credit Card Clients |
| Licença | CC BY 4.0 |
| Volume | 30.000 registros históricos (Taiwan, contexto 2005) |
| Identificador | `ID` original → `client_id` (não entra no modelo) |
| Dados sensíveis potenciais | atributos demográficos (`sex`, `education`, `marriage`, `age`) |

A base é pública e amplamente usada em pesquisa. Ainda assim, a
disponibilidade pública **não elimina** o dever de discutir finalidade,
minimização e riscos de uso inadequado em decisões de crédito.

Registro de procedência: [`data/raw/manifest.json`](../data/raw/manifest.json).

## Bases e finalidade (contexto acadêmico)

- **Finalidade:** estudar credit scoring, contratos de dados, detecção de
  drift e observabilidade de pipelines — não conceder ou negar crédito a
  pessoas reais.
- **Base legítima (análoga):** pesquisa acadêmica / demonstração técnica,
  com dados já publicados sob licença permissiva.
- **Limitação de finalidade:** os artefatos deste repositório não devem ser
  reutilizados como motor de decisão de crédito sem nova análise jurídica,
  validação temporal e avaliação de equidade.

## Minimização e tratamento

- O identificador `client_id` é preservado para rastreabilidade dos splits,
  mas **não** é feature do modelo.
- Não há enriquecimento com bases externas (CPF, e-mail, telefone, renda).
- Não há coleta de novos dados pessoais de titulares brasileiros.
- Logs estruturados (`logs/pipeline.log`) registram eventos de pipeline
  (métricas, alertas, hashes), não PII adicional inventada.

## Direitos dos titulares (leitura teórica)

Em um cenário real com dados de titulares no Brasil, o controlador deveria
viabilizar: confirmação de tratamento, acesso, correção, anonimização/
bloqueio, portabilidade e informação sobre compartilhamento.

Neste projeto acadêmico **não há canal operacional de atendimento a
titulares**, porque não há controladoria sobre dados de clientes reais:
trabalhamos apenas com a base histórica pública da UCI.

## Responsabilidades no time

| Papel | Responsabilidade |
|---|---|
| Pessoa 5 (governança) | Manter esta política e o model card alinhados ao código |
| Pessoa 1 | Garantir que origem, splits e limitações do baseline estejam corretos |
| Pessoa 2 | Manter o contrato Pandera como evidência auditável do que entra no pipeline |
| Pessoa 4 | Garantir que logs/alertas não exponham segredos nem PII além do necessário |

## O que este projeto não faz

- Não armazena credenciais de clientes.
- Não envia dados para APIs externas de scoring.
- Não implementa consentimento eletrônico nem DPO.
- Não substitui parecer jurídico para uso comercial.
