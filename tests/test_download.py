"""Verifica o download com manifesto existente, sem acessar a internet."""

import hashlib
import json
from types import SimpleNamespace

import pandas as pd
import pytest

from src.data import download


@pytest.mark.parametrize("matching_hash", [True, False])
def test_download_respects_existing_manifest(tmp_path, monkeypatch, matching_hash):
    data = pd.DataFrame(
        {
            "ID": range(1, 30_001),
            **{f"X{i}": [1] * 30_000 for i in range(1, 24)},
            "Y": [0, 1] * 15_000,
        }
    )
    csv_bytes = data.to_csv(index=False, lineterminator="\n").encode("utf-8")
    checksum = hashlib.sha256(csv_bytes).hexdigest()

    dataset_path = tmp_path / "credit_default.csv"
    dictionary_path = tmp_path / "variables.csv"
    manifest_path = tmp_path / "manifest.json"

    manifest_text = json.dumps(
        {
            "csv_sha256": checksum if matching_hash else "hash-diferente",
            "downloaded_at_utc": "data-original-preservada",
        }
    )
    manifest_path.write_text(manifest_text, encoding="utf-8")

    dataset = SimpleNamespace(
        data=SimpleNamespace(original=data),
        variables=pd.DataFrame({"name": data.columns}),
        metadata=SimpleNamespace(
            repository_url="https://example.org/dataset",
            data_url="https://example.org/data.csv",
        ),
    )

    monkeypatch.setattr(download, "RAW_DIR", tmp_path)
    monkeypatch.setattr(download, "DATASET_PATH", dataset_path)
    monkeypatch.setattr(download, "DICTIONARY_PATH", dictionary_path)
    monkeypatch.setattr(download, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(download, "fetch_ucirepo", lambda **kwargs: dataset)

    if matching_hash:
        download.main()
        assert dataset_path.read_bytes() == csv_bytes
        assert dictionary_path.exists()
    else:
        with pytest.raises(ValueError, match="difere do manifesto"):
            download.main()
        assert not dataset_path.exists()
        assert not dictionary_path.exists()

    assert manifest_path.read_text(encoding="utf-8") == manifest_text
