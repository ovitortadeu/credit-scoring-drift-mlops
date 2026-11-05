"""Configuracao central do MLflow para tracking de experimentos.

Todo script do pipeline que registra experimentos (treino, avaliacao,
deteccao e impacto do drift) usa `configure_mlflow()` para apontar para o
mesmo tracking store local do projeto, evitando que cada execucao crie um
`mlruns/` em um diretorio diferente dependendo de onde o comando foi chamado.
"""

from __future__ import annotations

from pathlib import Path

import mlflow

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MLRUNS_DIR = PROJECT_ROOT / "mlruns"
ARTIFACTS_DIR = MLRUNS_DIR / "artifacts"

# O backend de arquivo puro ("file:./mlruns") esta em modo de manutencao a
# partir do MLflow 3.x; o proprio projeto recomenda SQLite como tracking
# store local leve, sem exigir um servidor separado.
TRACKING_URI = f"sqlite:///{MLRUNS_DIR}/mlflow.db"


def configure_mlflow(experiment_name: str) -> None:
    """Aponta o MLflow para o tracking store local do projeto e seleciona o experimento."""
    MLRUNS_DIR.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(TRACKING_URI)

    if mlflow.get_experiment_by_name(experiment_name) is None:
        mlflow.create_experiment(experiment_name, artifact_location=f"file:{ARTIFACTS_DIR}")

    mlflow.set_experiment(experiment_name)
