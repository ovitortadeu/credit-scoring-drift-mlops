"""Testes para a configuracao de logging estruturado."""

from __future__ import annotations

import importlib
import json
import logging

import pytest

from src.observability import logging_config


@pytest.fixture(autouse=True)
def _reset_root_logger():
    """Remove os handlers e a flag de configuracao entre testes para isolamento."""
    root_logger = logging.getLogger(logging_config.ROOT_LOGGER_NAME)
    original_handlers = list(root_logger.handlers)
    original_configured = getattr(root_logger, logging_config._CONFIGURED_ATTR, False)
    root_logger.handlers = []
    setattr(root_logger, logging_config._CONFIGURED_ATTR, False)
    yield
    for handler in root_logger.handlers:
        if handler not in original_handlers:
            handler.close()
    root_logger.handlers = original_handlers
    setattr(root_logger, logging_config._CONFIGURED_ATTR, original_configured)


def test_setup_logging_creates_log_file(tmp_path, monkeypatch):
    log_path = tmp_path / "logs" / "pipeline.log"
    monkeypatch.setattr(logging_config, "LOGS_DIR", log_path.parent)
    monkeypatch.setattr(logging_config, "LOG_FILE_PATH", log_path)

    logger = logging_config.setup_logging("test_module")
    logger.info("mensagem de teste")

    assert log_path.exists()
    assert logger.name == f"{logging_config.ROOT_LOGGER_NAME}.test_module"


def test_setup_logging_is_idempotent(tmp_path, monkeypatch):
    log_path = tmp_path / "logs" / "pipeline.log"
    monkeypatch.setattr(logging_config, "LOGS_DIR", log_path.parent)
    monkeypatch.setattr(logging_config, "LOG_FILE_PATH", log_path)

    logging_config.setup_logging("mod_a")
    logging_config.setup_logging("mod_b")

    root_logger = logging.getLogger(logging_config.ROOT_LOGGER_NAME)
    # Conta apenas os handlers que nos adicionamos: o pytest pode anexar os
    # seus proprios handlers de captura ao mesmo logger durante o teste.
    file_handlers = [h for h in root_logger.handlers if isinstance(h, logging.FileHandler)]
    stream_handlers = [
        h
        for h in root_logger.handlers
        if type(h) is logging.StreamHandler  # exclui subclasses, como a do pytest
    ]
    assert len(file_handlers) == 1
    assert len(stream_handlers) == 1


def test_json_lines_formatter_produces_valid_json(tmp_path, monkeypatch):
    log_path = tmp_path / "logs" / "pipeline.log"
    monkeypatch.setattr(logging_config, "LOGS_DIR", log_path.parent)
    monkeypatch.setattr(logging_config, "LOG_FILE_PATH", log_path)

    logger = logging_config.setup_logging("test_json")
    logger.warning(
        "drift critico em %s",
        "pay_0",
        extra={"event": "drift_alert", "data": {"column": "pay_0", "value": 0.72}},
    )

    for handler in logging.getLogger(logging_config.ROOT_LOGGER_NAME).handlers:
        handler.flush()

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1

    record = json.loads(lines[0])
    assert record["level"] == "WARNING"
    assert record["message"] == "drift critico em pay_0"
    assert record["event"] == "drift_alert"
    assert record["data"] == {"column": "pay_0", "value": 0.72}


def test_module_reimport_does_not_break_handlers():
    importlib.reload(logging_config)
    logger = logging_config.setup_logging("reload_check")
    assert logger.name.endswith("reload_check")
