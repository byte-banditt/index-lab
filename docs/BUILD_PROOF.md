# Local clean-clone proof

Historical extraction snapshot. Current public-install status: [publication validation](PUBLICATION_REPORT.md).

Public pinned commit fetch failed. This proof used a process-local Git URL mapping to the original local mdq repository, not a public GitHub install. Python runtime: `Python 3.13.12`. No package source was copied into this project.

| Command in /tmp/proof | Exit code |
| --- | --- |
| `.venv/bin/pip install -e '.[dev]'` | 0 |
| `.venv/bin/pytest -q` | 0 |
| `.venv/bin/ruff check` | 0 |
| `.venv/bin/python -m indexkit.fixtures --directory /tmp/index-proof-fixture` | 0 |
| `.venv/bin/python run_all.py --config /tmp/index-proof-fixture/fixture_config.json --output-dir /tmp/index-proof-artifacts/fast` | 0 |
| `.venv/bin/python run_all.py --full --config /tmp/index-proof-fixture/fixture_config.json --output-dir /tmp/index-proof-artifacts/full` | 0 |
| `.venv/bin/index-lab --config /tmp/index-proof-fixture/fixture_config.json --output-dir /tmp/index-proof-artifacts/console` | 0 |
| `.venv/bin/python run_all.py --output-dir /tmp/index-proof-artifacts/real` | 0 |
| `.venv/bin/pytest -q -m realdata` | 0 |

## step5-pytest

```text
................................................................s....... [ 74%]
.........................                                                [100%]
96 passed, 1 skipped in 30.84s
```

## step5-ruff

```text
All checks passed!
```

## step5-real-test

```text
.                                                                        [100%]
1 passed, 96 deselected in 0.59s
```

## Installed mdq provenance

```json
{
  "url": "https://github.com/byte-banditt/mdq.git",
  "vcs_info": {
    "commit_id": "700db229caebf6718acb949a2c145b6513595808",
    "requested_revision": "700db229caebf6718acb949a2c145b6513595808",
    "vcs": "git"
  }
}
```

## Limits

R cross-check NOT RUN: Rscript unavailable. GitHub workflow NOT RUN. Public installation NOT DONE: the requested pinned SHA is absent on the remote. Initial extraction-tool pip installation modified home pip-cache files; exhaustive filesystem confinement is NOT DONE. Subsequent pip and matplotlib cache paths were directed to temporary directories.
