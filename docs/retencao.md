# Retenção e ciclo de vida dos artefatos

## Objetivo

Definir o que é versionado, o que é gerado em runtime e por quanto tempo
cada classe de artefato deve ser mantida neste projeto acadêmico.

## Mapa de artefatos

| Artefato | Versionado no Git? | Geração | Política de retenção (demo) |
|---|---|---|---|
| `data/raw/manifest.json` | Sim | Download | Permanente (procedência) |
| `data/raw/*.csv` | Não (`.gitignore`) | `src.data.download` | Regenerável; pode apagar a qualquer momento |
| `data/reference|test|production/*.csv` | Não | `split` / `simulate` / `invalid_batch` | Regenerável após cada execução completa |
| `models/*.joblib` | Não | `src.models.train` | Regenerável; reter só enquanto reprodutível localmente |
| `reports/*.json`, `reports/baseline_report.md` | Sim (evidência) | train/evaluate/drift/obs | Permanente na entrega acadêmica |
| `reports/*.html` | Não | Evidently / dashboard | Regenerável; abrir no navegador após o pipeline |
| `logs/pipeline.log` | Não | runtime | Apagar entre execuções limpas; não commitá |
| `mlruns/`, `mlartifacts/` | Não | MLflow | Local; pode ser recriado ao retreinar |
| Documentação em `docs/` | Sim | manual | Permanente |

## Princípios

1. **Regenerabilidade:** qualquer CSV, modelo, HTML, log ou banco MLflow
   deve ser reconstruível pelos comandos do README.
2. **Evidência mínima versionada:** mantemos JSONs de métricas/alertas e o
   manifesto para auditoria sem versionar dados brutos.
3. **Sem segredos:** não há `.env` de produção; arquivos sensíveis
   (`.pem`, `.key`, `.env`) estão no `.gitignore`.
4. **Finalidade acadêmica:** não há obrigação legal de retenção bancária
   (ex.: anos de histórico de concessão). Ao encerrar a disciplina, basta
   manter o repositório Git e regenerar artefatos se necessário.

## Procedimento de limpeza local

```bash
# Artefatos regeneráveis (cuidado: exige rerodar o pipeline)
rm -f data/raw/*.csv data/reference/*.csv data/test/*.csv data/production/*.csv
rm -f models/*.joblib reports/*.html
rm -rf logs mlruns mlartifacts
```

Depois, seguir [Como rodar o projeto do zero](../README.md#como-rodar-o-projeto-do-zero).

## Relação com LGPD

Como não há dados de titulares brasileiros sob nosso controle, a política
acima foca em **higiene de artefatos técnicos** e em não acumular cópias
desnecessárias da base fora do fluxo documentado. Detalhes em
[`docs/lgpd.md`](lgpd.md).
