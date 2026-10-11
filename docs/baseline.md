# Dados e modelo baseline

## Objetivo e escopo

Este documento descreve a entrega: obtenção dos dados,
inspeção inicial, separação dos conjuntos, pré-processamento,
treinamento e avaliação do modelo baseline.

O baseline será utilizado pelas etapas de validação, simulação de drift
e observabilidade. Os contratos completos de dados, a simulação de drift,
o monitoramento e a documentação geral de governança pertencem às demais
frentes do projeto.

## Dataset

- Nome: Default of Credit Card Clients.
- Fonte: UCI Machine Learning Repository.
- Identificador UCI: 350.
- DOI: https://doi.org/10.24432/C55S3H
- Licença: CC BY 4.0.
- Atribuição: Yeh, I. (2009). Default of Credit Card Clients [Dataset].
  UCI Machine Learning Repository.
- Volume: 30.000 registros e 23 variáveis explicativas.
- Contexto: dados históricos de clientes de cartão de crédito em Taiwan.
- Alvo: inadimplência no mês seguinte, com 1 para inadimplência e 0
  para ausência de inadimplência.

O identificador original é preservado como `client_id`, mas não entra
no modelo. O alvo recebe o nome `default_next_month`.

O dataset não possui renda. A coluna `limit_bal` representa limite
de crédito, e os valores monetários da fonte estão em dólares de Taiwan.

A base original permanece em `data/raw/credit_default.csv`.
O arquivo `data/raw/manifest.json` registra origem, data de obtenção,
versões e SHA-256 do CSV.

Os CSVs ficam fora do Git. Sua obtenção é reproduzível pelo script
de download. O dicionário recebido da UCI é salvo em `data/raw/variables.csv`.

## Inspeção e decisões de preparação

A inspeção inicial encontrou:

- Nenhum valor nulo.
- Nenhum identificador repetido.
- 35 ocorrências adicionais iguais ao desconsiderar o ID.
- 56 ocorrências adicionais com as mesmas features, desconsiderando ID e alvo.
- 23.364 registros da classe 0 e 6.636 da classe 1.

Os registros foram preservados. Features iguais não comprovam que
clientes com IDs diferentes sejam duplicatas indevidas.

Para evitar sobreposição de perfis entre os conjuntos, registros
com as mesmas 23 features foram mantidos no mesmo grupo durante
a separação, independentemente do alvo.

Os códigos 0, 5 e 6 em `education`, 0 em `marriage` e os códigos
de status de pagamento não explicados pelo dicionário consultado
foram preservados como categorias, sem atribuição de significado adicional.

Valores negativos de faturas e valores monetários extremos foram
preservados. Não houve substituição automática por zero, remoção
de outliers ou imputação.

Essas decisões devem orientar a implementação dos contratos:
não se deve exigir que toda coluna numérica seja positiva.

## Separação dos conjuntos

A divisão usa `StratifiedGroupKFold`, cinco blocos e semente 42.

- Blocos 2, 3 e 4: referência/treino.
- Bloco 0: teste.
- Bloco 1: produção base.

| Conjunto | Registros | Inadimplência | Uso |
|---|---:|---:|---|
| Referência | 17.999 | 22,12% | Ajuste do pipeline |
| Teste | 6.000 | 22,12% | Avaliação do baseline |
| Produção base | 6.001 | 22,13% | Simulação posterior de drift |

A separação preserva todos os registros e verifica a ausência de
sobreposição de IDs e grupos de features.

Trata-se de uma separação para simulação acadêmica, não de uma
divisão cronológica real.

O arquivo `reports/split_summary.json` registra a configuração,
os tamanhos, as distribuições e os hashes dos conjuntos.

A produção base deve ser preservada. Os lotes com drift devem ser
gravados em outros arquivos.

## Pré-processamento

Os nomes das colunas estão centralizados em `src/data/schema.py`.

São tratadas como categorias:

- `sex`, `education`, `marriage`;
- `pay_0`, `pay_2`, `pay_3`, `pay_4`, `pay_5`, `pay_6`.

Essas colunas recebem `OneHotEncoder(handle_unknown="ignore")`.
Uma categoria não vista no treino produz indicadores zerados para
aquela variável. Esse comportamento não substitui validação ou
monitoramento de categorias novas.

As demais features recebem `StandardScaler`.

O pré-processamento é ajustado somente na referência. Teste e produção
utilizam as transformações já aprendidas.

ID e alvo ficam fora das features. O pipeline recebe as 23 colunas
originais renomeadas, antes da codificação e da padronização.

## Modelos

### Regressão logística

Configuração inicial fixa:

- `solver="lbfgs"`;
- `C=1.0`;
- `max_iter=2000`;
- `tol=0.0001`;
- `class_weight=None`.

O treinamento interrompe caso seja emitido um aviso de falta de convergência.

### Modelo de comparação

`DummyClassifier(strategy="most_frequent")`, que sempre prevê
a classe mais frequente na referência.

Cada modelo possui um pipeline independente, contendo pré-processamento
e classificador.

Os artefatos são salvos em:

- `models/logistic_regression.joblib`;
- `models/dummy.joblib`.

Eles ficam fora do Git e são regenerados pelo treinamento.
Carregue somente artefatos de origem confiável.

## Resultados iniciais

Avaliação em 6.000 registros de teste, sem ajuste de limiar nesse conjunto.

Precision, recall e F1 referem-se à classe positiva 1.
ROC AUC utiliza a probabilidade da classe 1.

| Modelo | Acurácia | Precision | Recall | F1 | ROC AUC |
|---|---:|---:|---:|---:|---:|
| Regressão logística | 0,8175 | 0,6652 | 0,3519 | 0,4603 | 0,7531 |
| Dummy | 0,7788 | 0,0000 | 0,0000 | 0,0000 | 0,5000 |

Matriz de confusão da regressão logística:

| Classe real | Previsto 0 | Previsto 1 |
|---|---:|---:|
| Real 0 | 4.438 | 235 |
| Real 1 | 860 | 467 |

A regressão superou o dummy em 3,87 pontos percentuais de acurácia,
mas deixou de identificar 860 dos 1.327 inadimplentes, aproximadamente
64,81% deles.

O resultado serve como baseline acadêmico. Não comprova adequação
para decisões reais de crédito.

No dummy, a precision é registrada como zero por convenção
(`zero_division=0`), pois não há previsões positivas.

As métricas completas estão em `reports/baseline_metrics.json`.
O relatório legível está em `reports/baseline_report.md`.

Melhorias futuras devem usar validação dentro da referência,
preservando grupos de perfis. O teste não deve orientar ajustes sucessivos.

## Como reproduzir

Execute os comandos na raiz do repositório.

Ambiente utilizado: Python 3.12.2. As dependências estão registradas
em `uv.lock`.

### Instalação

```bash
uv sync --locked --extra dev
```

No Windows, caso a instalação falhe por incompatibilidade com hardlinks,
execute no PowerShell e repita a instalação:

```powershell
$env:UV_LINK_MODE = "copy"
```

### Primeira execução

```bash
uv run python -m src.data.download
uv run python -m src.data.inspect_data
uv run python -m src.data.split
uv run python -m src.models.train
uv run python -m src.models.evaluate
```

O download bloqueia a sobrescrita quando os CSVs de saída já existem.
Quando somente o manifesto versionado está presente, o script baixa
a base, confere seu SHA-256 e preserva o manifesto. Se o hash divergir,
interrompe antes de gravar os CSVs.

Quando a base original já estiver disponível, pule o download.

A separação, o treinamento e a avaliação regeneram seus respectivos
arquivos. Ao retreinar, execute a avaliação novamente para manter
os relatórios associados aos novos artefatos.

Datas, durações e hashes de artefatos podem mudar entre execuções.
Diferenças pequenas de resultados também podem ocorrer entre ambientes.

### Testes

```bash
uv run pytest tests/test_preprocessing.py tests/test_model_serialization.py
```

Os cinco testes verificam:

- exclusão de ID e alvo da transformação;
- tratamento de categorias novas;
- reutilização das estatísticas aprendidas no treino;
- preservação de previsões e probabilidades após salvar e recarregar
  cada tipo de pipeline.

Os testes usam dados fictícios e não dependem de download.
Eles não substituem os testes integrados dos contratos e do drift.

## Integração com as outras frentes

### Contratos

Utilizar os nomes de `src/data/schema.py` e validar os dados antes
da inferência.

Distinguir duplicação de identificador de clientes com perfis iguais.
Preservar a diferença entre colunas de fatura, pagamento e códigos
categóricos ao definir regras.

### Drift

Utilizar `data/production/production_base.csv` como ponto de partida
e salvar os cenários modificados em arquivos separados.

Exemplo de inferência, após a validação do lote:

```python
import joblib
import pandas as pd

from src.data.schema import FEATURE_COLUMNS

model = joblib.load("models/logistic_regression.joblib")
batch = pd.read_csv("data/production/production_base.csv")

features = batch[FEATURE_COLUMNS]
predictions = model.predict(features)

positive_index = list(model.classes_).index(1)
probabilities = model.predict_proba(features)[:, positive_index]
```

Não chamar `fit` ou `fit_transform` na produção.
O pipeline já contém o pré-processamento treinado.

Para monitorar distribuições, preservar também as features anteriores
ao pré-processamento. O alvo disponível na simulação deve ficar
separado das entradas do modelo.

### Observabilidade

Os JSONs em `reports/` fornecem configuração, duração do treinamento,
métricas e hashes. Podem ser integrados ao tracking e ao monitoramento.

### Documentação e governança

Incorporar ao README geral a origem dos dados, o fluxo de execução,
os resultados e as limitações.

O baseline utiliza atributos demográficos. Não foi realizada avaliação
de equidade entre grupos. A disponibilidade pública da base não elimina
a necessidade de discutir privacidade, finalidade e vieses.

O baixo recall, o contexto histórico e geográfico e a ausência de
validação temporal devem constar das limitações do projeto.