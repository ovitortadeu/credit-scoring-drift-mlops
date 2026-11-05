"""Configuracao central de logging estruturado para todo o pipeline.

Cada etapa (treino, validacao, drift) chama `setup_logging(__name__)` para
obter um logger que escreve simultaneamente:

- no console, em texto legivel para acompanhamento humano;
- em `logs/pipeline.log`, uma linha JSON por evento, para consumo
  automatizado pelo agregador de metricas (`src/observability/metrics.py`).
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = PROJECT_ROOT / "logs"
LOG_FILE_PATH = LOGS_DIR / "pipeline.log"

ROOT_LOGGER_NAME = "credit_scoring"

# Atributo marcador no logger raiz: evita reconfigurar quando outra
# ferramenta (ex.: o capturador de logs do pytest) anexa seus proprios
# handlers ao mesmo logger, o que tornaria `root_logger.handlers` nao vazio
# sem que nos tivessemos de fato configurado nada.
_CONFIGURED_ATTR = "_credit_scoring_configured"

# Atributos padrao de um LogRecord, usados para isolar os campos extras
# passados via `extra={...}` nas chamadas de log.
_STANDARD_RECORD_ATTRS = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys())


class JsonLinesFormatter(logging.Formatter):
    """Formata cada registro como uma linha JSON, incluindo campos extras."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "message": record.getMessage(),
        }

        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _STANDARD_RECORD_ATTRS and key != "message"
        }
        if extras:
            payload.update(extras)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, default=str)


def setup_logging(name: str) -> logging.Logger:
    """Garante os handlers do logger raiz do projeto e retorna um logger filho.

    Idempotente: pode ser chamado em todo modulo sem duplicar handlers,
    mesmo quando varios scripts do pipeline sao importados no mesmo processo
    (por exemplo, durante a suite de testes).
    """
    root_logger = logging.getLogger(ROOT_LOGGER_NAME)

    if not getattr(root_logger, _CONFIGURED_ATTR, False):
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

        root_logger.setLevel(logging.INFO)
        root_logger.propagate = False

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )

        file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
        file_handler.setFormatter(JsonLinesFormatter())

        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        setattr(root_logger, _CONFIGURED_ATTR, True)

    return logging.getLogger(f"{ROOT_LOGGER_NAME}.{name}")
