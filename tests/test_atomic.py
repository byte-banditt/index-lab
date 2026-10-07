from pathlib import Path

import pandas as pd
import pytest

from indexkit.atomic import publish
from indexkit.data import config, load, output_root


def test_cutoff_applies_to_source_dq(monkeypatch):
    from run_all import run

    cfg = config()
    frame, inventory = load(cfg)
    last = frame.index[frame.date == frame.date.max()][0]
    frame.loc[last, "adj_close"] = float("nan")
    cfg["end"] = "2022-04-29"
    monkeypatch.setattr("run_all.load", lambda cfg: (frame.copy(), inventory))
    run(fast=True, cfg=cfg)
    dq = pd.read_csv(output_root() / "reports/source_dq.csv")
    assert pd.to_datetime(dq.date).max() <= pd.Timestamp(cfg["end"])
    assert "invalid_calculation_price" not in set(dq.check_name)


def test_failed_generation_keeps_previous_outputs(monkeypatch):
    from run_all import run

    destination = output_root()
    for name in ("reports", "docs"):
        path = destination / name
        path.mkdir(parents=True)
        (path / "previous.txt").write_text(name)

    def fail(cfg):
        raise RuntimeError("injected generation failure")

    monkeypatch.setattr("indexkit.options.artifacts", fail)
    with pytest.raises(RuntimeError, match="injected generation failure"):
        run(fast=True)
    for name in ("reports", "docs"):
        assert (destination / name / "previous.txt").read_text() == name
        assert len(list((destination / name).iterdir())) == 1
    assert not list(destination.glob(".build-*"))


def test_publication_rolls_back_second_directory(tmp_path, monkeypatch):
    import os

    stage, destination = tmp_path / "stage", tmp_path / "destination"
    for root, content in ((stage, "new"), (destination, "old")):
        for name in ("reports", "docs"):
            (root / name).mkdir(parents=True)
            (root / name / "snapshot.txt").write_text(content)
    replace = os.replace

    def fail_second(source, target):
        if Path(source) == stage / "docs":
            raise OSError("injected rename failure")
        replace(source, target)

    monkeypatch.setattr("indexkit.atomic.os.replace", fail_second)
    with pytest.raises(OSError, match="injected rename failure"):
        publish(stage, destination)
    for name in ("reports", "docs"):
        assert (destination / name / "snapshot.txt").read_text() == "old"
