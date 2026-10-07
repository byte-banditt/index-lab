"""All Index Lab tests use offline source fixtures and isolated output paths."""

import pytest
from indexkit.fixtures import create_fixture


@pytest.fixture(scope="session")
def fixture_config_path(tmp_path_factory):
    return create_fixture(tmp_path_factory.mktemp("indexlab_source"))


@pytest.fixture(autouse=True)
def isolated_indexlab(tmp_path, monkeypatch, fixture_config_path):
    monkeypatch.setenv("INDEXLAB_CONFIG", str(fixture_config_path))
    monkeypatch.setenv("INDEXLAB_OUTPUT_DIR", str(tmp_path / "artifacts"))
