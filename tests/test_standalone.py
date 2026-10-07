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


def test_ingestion_config_uses_configured_inputs(tmp_path):
    from mdq.store import load_config

    from scripts.make_ingestion_config import write_config

    cfg = config()
    written = load_config(write_config(cfg, tmp_path / "ingestion.yaml"))
    assert written["database"] == cfg["database"]
    assert written["start_date"] == cfg["ingestion"]["start_date"]
    assert set(cfg["universe"]).issubset(written["symbols"])
    assert cfg["multi"]["fx_symbol"] in written["symbols"]


def test_readme_inventory_covers_package():
    text = (ROOT / "README.md").read_text()
    for module in (ROOT / "indexkit").glob("*.py"):
        assert f"indexkit/{module.name}" in text
