# Contratos de dados

## Objetivo e escopo

Este documento descreve o contrato de dados do projeto: as regras
rigidas que todo lote deve atender antes de alimentar o modelo, a
forma de execucao, a demonstracao de bloqueio e os pontos de
integracao com as demais frentes.

O contrato cobre a validacao de qualidade e consistencia das 25
colunas do dataset Default of Credit Card Clients. Nao cobre
analise causal, detecao de drift, observabilidade nem governanca,
que pertencem a outras frentes.

## Onde esta o codigo

- `src/validation/schema.py` — `CreditDefaultSchema`, modelo Pandera
  com os campos e as regras.
- `src/validation/invalid_batch.py` — gera um lote proposital
  invalido para demonstrar o bloqueio.
- `src/validation/cli.py` — linha de comando para validar qualquer CSV.
- `tests/test_schema.py` — 11 testes positivos e negativos.

## Regras do contrato

O contrato trata o dataset como estritamente tipado. Nenhuma coluna
extra e permitida (`strict=True`) e nenhuma coercao de tipo e feita
(`coerce=False`).

| Coluna | Tipo | Regra |
|---|---|---|
| `client_id` | int | unico, >= 1, nao nulo |
| `limit_bal` | int | > 0, nao nulo |
| `sex` | int | em {1, 2}, nao nulo |
| `education` | int | em [0, 6], nao nulo |
| `marriage` | int | em [0, 3], nao nulo |
| `age` | int | em [18, 100], nao nulo |
| `pay_0`, `pay_2..pay_6` | int | em [-2, 9], nao nulo |
| `bill_amt1..bill_amt6` | int | nao nulo (sem restricao de sinal) |
| `pay_amt1..pay_amt6` | int | >= 0, nao nulo |
| `default_next_month` | int | em {0, 1}, nao nulo |

### Observacoes sobre as regras

- `limit_bal` deve ser positivo. Limite zero ou negativo e tratado
  como corrupcao.
- `age` em [18, 100] cobre a maioridade de contrato e um limite
  superior plausivel.
- `pay_amt*` precisa ser nao negativo. Pagamento negativo e dado
  invalido.
- `bill_amt*` pode ser negativo. Credito a devolver existe no
  dominio e nao deve ser rejeitado.
- `sex`, `education`, `marriage` e os codigos de status de pagamento
  usam o encoding original da UCI. Valores fora da faixa documentada
  sao rejeitados.
- A unicidade de `client_id` previne data leakage por duplicatas
  entre conjuntos.

## Modo de execucao

A validacao usa `lazy=True`: todos os erros do lote sao coletados
antes de levantar a excecao, em vez de parar no primeiro. Isso
facilita o diagnostico quando varios campos estao corrompidos ao
mesmo tempo.

A funcao exportada e `src.validation.schema.validate(df)`.

```python
import pandas as pd
from src.validation.schema import validate

data = pd.read_csv("data/reference/reference.csv")
validate(data)  # levanta pandera.errors.SchemaErrors em caso de falha
```

## Pontos de integracao

O contrato ja e chamado como gate obrigatorio antes do uso dos dados em:

- `src/models/train.py` — valida `data/reference/reference.csv`
  antes do treinamento.
- `src/models/evaluate.py` — valida `data/test/test.csv` antes
  da avaliacao.

Novos consumidores (inferencia em producao, simulacao de drift)
devem seguir o mesmo padrao: ler o CSV, chamar `validate(df)` e
somente entao prosseguir.

## Demonstracao de bloqueio

O guia tecnico exige a demonstracao de um lote invalido que o
contrato bloqueia antes da inferencia.

### Gerar o lote invalido

```bash
uv run python -m src.validation.invalid_batch
```

Isso cria `data/production/invalid_batch.csv` com sete tipos de
violacao simultaneos: id duplicado, id negativo, limite zero,
limite negativo, sexo invalido, educacao fora da faixa, estado civil
fora da faixa, idade abaixo de 18, idade acima de 100, status de
pagamento fora de [-2, 9], valor de pagamento negativo e alvo
fora de {0, 1}.

### Validar o lote invalido

```bash
uv run python -m src.validation.cli data/production/invalid_batch.csv
```

A saida esperada e um relatorio tabulado das violacoes, encerrando
com exit code 1.

### Validar um lote valido

```bash
uv run python -m src.validation.cli data/reference/reference.csv
```

A saida esperada e `OK — 17999 linhas aprovadas pelo contrato`,
com exit code 0.

## Testes

```bash
uv run pytest tests/test_schema.py
```

Os onze testes verificam:

- amostra sintetica valida e aprovada;
- dataset de referencia real e aprovado quando disponivel;
- lote invalido e bloqueado por completo;
- cada regra individual rejeita o valor fora da faixa (idade,
  sexo, duplicata de id, limite zero, alvo invalido, pagamento
  negativo, coluna extra).

Os testes negativos sao o que comprova que o contrato realmente
barra o dado ruim: sem eles, um contrato permissivo passaria sem
ninguem perceber.

## Integracao com as outras frentes

### Drift

Antes de comparar lotes de producao com a referencia, cada lote
deve passar pelo contrato. Lotes rejeitados nao devem alimentar
nem o modelo nem os testes de drift.

Alteracoes propositais para simulacao de drift (mudanca de media,
mudanca de proporcao de classes) devem respeitar o contrato ou
serao rejeitadas na ingestao. Isso e intencional: o contrato
distingue dado corrompido de dado valido com distribuicao
diferente.

### Observabilidade

A chamada a `validate()` levanta `pandera.errors.SchemaErrors` com
`failure_cases`, uma tabela pandas com coluna, regra violada,
indice da linha e valor invalido. Esse objeto pode ser serializado
e enviado para logs estruturados ou metricas de contagem de
violacoes por regra.

### Governanca

As regras documentadas aqui compoem evidencia auditavel: cada
decisao sobre range, categoria valida e unicidade esta registrada
em codigo e em texto. Isso atende a exigencia de rastreabilidade
de dados que entram em decisao automatizada.
