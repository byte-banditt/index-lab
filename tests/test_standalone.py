import os
from pathlib import Path

import pytest

from indexkit.data import ROOT, config, load


def test_db_environment_override(monkeypatch, tmp_path):
    path = tmp_path / "external.sqlite"
    monkeypatch.setenv("INDEXLAB_DB", str(path))
    assert config()["database"] == str(path)


@pytest.mark.realdata
def test_optional_real_database():
    path = Path(os.environ.get("INDEXLAB_DB", ROOT / "data/mdq.sqlite"))
    if not path.is_file():
        pytest.skip("Observed DB absent; set INDEXLAB_DB for the optional read-only check")
    cfg = config(ROOT / "config.yaml")
    frame, inventory = load(cfg)
    assert not frame.empty
    assert {"date", "symbol", cfg["price_field"]}.issubset(frame.columns)
    assert "prices_raw" in inventory
