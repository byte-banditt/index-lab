# Public dependency validation

Current mdq pin: `f02f418c99a6771a692572b3390ef8beea16f17e` on public branch `fix/computed-report-only`. The unavailable extraction pin was `700db229caebf6718acb949a2c145b6513595808`. Publishing the local mdq master would expose additional local audit material, so only the report fix and regression test were published on a branch from the already public master. The original mdq master and unmerged removal proposal remain unchanged.

Installed provenance (public GitHub fetch, no local URL mapping):

```json
{
  "url": "https://github.com/byte-banditt/mdq.git",
  "vcs_info": {
    "commit_id": "f02f418c99a6771a692572b3390ef8beea16f17e",
    "requested_revision": "f02f418c99a6771a692572b3390ef8beea16f17e",
    "vcs": "git"
  }
}
```

An existing same-version mdq installation initially retained its previous commit metadata. It was explicitly reinstalled with --force-reinstall --no-deps, then provenance was verified before these tests. Fresh editable installs fetch the pin normally.

The installed core matches the extraction source byte-for-byte:

```text
git diff --exit-code 700db229caebf6718acb949a2c145b6513595808 f02f418c99a6771a692572b3390ef8beea16f17e -- src/mdq pyproject.toml
exit_code=0
diff output: empty
```

| Validation command | Exit code |
| --- | --- |
| `.venv/bin/python -c 'import importlib.metadata; print(importlib.metadata.distribution("mdq").read_text("direct_url.json"))'` | 0 |
| `.venv/bin/python -m indexkit.fixtures --directory /tmp/index-public-fixture` | 0 |
| `.venv/bin/python run_all.py --config /tmp/index-public-fixture/fixture_config.json --output-dir /tmp/index-public-artifacts/fast` | 0 |
| `.venv/bin/python run_all.py --full --config /tmp/index-public-fixture/fixture_config.json --output-dir /tmp/index-public-artifacts/full` | 0 |
| `.venv/bin/pytest -q` | 0 |
| `.venv/bin/ruff check` | 0 |

## pytest

```text
................................................................s....... [ 74%]
.........................                                                [100%]
96 passed, 1 skipped in 19.22s
```

## ruff

```text
All checks passed!
```

## mdq-pytest

```text
............................                                             [100%]
28 passed in 0.46s
```

## mdq-ruff

```text
All checks passed!
```

## Full-build language status

```json
{
  "java": "Python/Java cases passed: 5",
  "R": "NOT DONE: Rscript unavailable; R cross-check NOT RUN"
}
```

No market-price DB, generated reports, private career files or environment credentials were included in this commit. Historical extraction reports describe their earlier no-push state; this publication is separately authorized. GitHub CI status will be reported after the push; no CI success is claimed here.
