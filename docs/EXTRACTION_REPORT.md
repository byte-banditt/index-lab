# Extraction report

Historical extraction snapshot. Current public-install status: [publication validation](PUBLICATION_REPORT.md).

## Outcome

Standalone project: `index-lab`, sibling to the source checkout. No push or merge was executed. The original checkout retains its index directory and stays on master. The unmerged cleanup proposal exists only on a separate branch/worktree. Public installation remains blocked by the unavailable pinned source commit.

## Inventory recorded before extraction

`git log --oneline -- index_lab | wc -l` produced `7`. Original master SHA: `700db229caebf6718acb949a2c145b6513595808`. `git status --short` was empty.

| Original dependency | Observed use | Standalone treatment |
| --- | --- | --- |
| config.yaml | DB path pointed outside the index directory; curve and sector CSV paths were local | DB default now data/mdq.sqlite; env override INDEXLAB_DB; local CSVs retained |
| indexkit/data.py | mdq.checks; project-root locator; config and output env vars | Installed mdq dependency; own checkout root; YAML loading |
| indexkit/fixtures.py | mdq.ingest.upsert_prices; mdq.store.connect/init_db | Same actual schema/upserts from installed dependency; temporary DB |
| indexkit/robustness.py | Git history queried the parent checkout and old config path | Queries standalone Git history and config.yaml |
| Makefile | Included parent test directory | Tests only standalone tests |
| README | Parent editable install and parent src path in command examples | Replaced with standalone commands |
| tests/test_reporting.py | Read both standalone and parent README | Reads standalone README only |
| scripts/explain_day.py, Java reference generator | Added own root to sys.path | Use installed indexkit package |
| Original draft generator | Relative image links walked to reports | Renamed public generator; copies computed plots beside generated drafts |

Config/input paths observed: database, curve_inputs, sector_inputs, ROOT/config.yaml (INDEXLAB_CONFIG override), static constituent sample, docs templates, java_bs resources and r_check resource. The output context used INDEXLAB_OUTPUT_DIR. No outside relative Markdown target was found in the original index-directory README/docs scan; outside paths did appear in README command examples.

Original index tests were already covered by an autouse synthetic fixture config and temporary artifact directory. No index test was found reading the real local market DB or writing the real reports directory under that fixture. The parent README read was the external test dependency. Standalone realdata coverage was added as a read-only optional test.

Imported mdq functions: check_non_positive_price, check_ohlc_inconsistent, check_duplicate_rows, check_missing_sessions, check_stale_price, check_return_outlier, upsert_prices, connect, init_db. Only this portion of mdq is used directly; mdq remains a pinned dependency rather than copied source.

## Extraction method and history hygiene

Installed git-filter-repo in a temporary venv; locally cloned the source with --no-local. Filtering ran twice on the clone: exclusions first, then the subdirectory filter. The original repository was never a filter target. Git-filter-repo removed the clone origin; no standalone remote was subsequently added.

```text
/tmp/index-extraction-tools/bin/git-filter-repo --invert-paths \
  --path index_lab/indexkit/notes.py --path index_lab/tests/test_notes.py \
  --path index_lab/indexkit/audit.py --path index_lab/tests/test_audit.py \
  --path index_lab/indexkit/reporting.py --path index_lab/run_all.py \
  --path index_lab/README.md
/tmp/index-extraction-tools/bin/git-filter-repo --subdirectory-filter index_lab
```

| Excluded original historical path | Reason / current behavior |
| --- | --- |
| indexkit/notes.py | Exact requested historical path-pattern hit. No versions of this path survive; numbers-only functionality reintroduced as drafts.py |
| tests/test_notes.py | Exact path-pattern hit; sanitized public coverage is now test_drafts.py |
| indexkit/audit.py | Contained career-oriented audit sections; removed rather than carried |
| tests/test_audit.py | Covered removed audit tool; removed |
| indexkit/reporting.py | Contained career-facts generator. Old versions excluded; sanitized current reporting reintroduced |
| run_all.py | Referenced career-facts artifact; old versions excluded; sanitized runner reintroduced |
| README.md | Replaced parent-dependent documentation; excluded old versions and wrote standalone README |

The exact requested source history filename scan returned only:

```text
index_lab/indexkit/notes.py
index_lab/tests/test_notes.py
```

No database, generated report, cache or private career document appeared in the original subdirectory history filename list. Such runtime/private paths are ignored in the standalone project. Root files from mdq never entered the subdirectory extraction. README/reporting/runner now have only their new sanitized history. Authorship metadata was retained by the history filter; the contact scan requested here checks history diffs, not author metadata.

### Historical filename proof (snapshot before this report commit)

```text
.github/workflows/ci.yml
.gitignore
Makefile
README.md
config.yaml
data/nifty50_constituents.csv
data/rates_inputs.csv
data/sector_map.csv
docs/BUILD_PROOF.md
docs/MOVE_PROPOSAL.md
docs/equity_derivs_flow_primer.md
docs/index_change_note_template.md
docs/rebalance_runbook.md
indexkit/__init__.py
indexkit/atomic.py
indexkit/attribution.py
indexkit/calendar.py
indexkit/crosschecks.py
indexkit/data.py
indexkit/drafts.py
indexkit/fixtures.py
indexkit/index_engine.py
indexkit/monitor.py
indexkit/multi_asset.py
indexkit/options.py
indexkit/rates.py
indexkit/reporting.py
indexkit/robustness.py
indexkit/stress.py
indexkit/structured.py
indexkit/validation.py
java_bs/BlackScholes.java
java_bs/generate_reference.py
pyproject.toml
pytest.ini
r_check/verify.R
ruff.toml
run_all.py
scripts/explain_day.py
scripts/make_ingestion_config.py
tests/conftest.py
tests/test_atomic.py
tests/test_attribution_stress.py
tests/test_crosschecks.py
tests/test_drafts.py
tests/test_java.py
tests/test_monitor.py
tests/test_multi.py
tests/test_options.py
tests/test_phase1.py
tests/test_rates.py
tests/test_reporting.py
tests/test_robustness.py
tests/test_standalone.py
tests/test_structured.py
```

### Full-history diff scan

After filtering, before new commits, identity-word, email and phone scans returned no hits. The later snapshot below includes the new public source commits. Identity-word hits are protective ignore patterns only, not private material:

```text
+*resume*
+*RESUME*
+*interview*
+*INTERVIEW*
```

| Scan | Observed result |
| --- | --- |
| Email pattern | 0 hits |
| International phone pattern | 0 hits |
| Blocked historical filenames | 0 hits |

This report itself records technical exclusion paths and scan terms; those records are not career notes or private contact information. Regex scans are evidence of their matches, not a guarantee of detecting every possible secret format.

## Pinned dependency and installation

Pinned mdq SHA: `700db229caebf6718acb949a2c145b6513595808`. It was the exact local master used by the source project. Its public remote advertised an older master; direct fetch of the requested SHA failed:

```text
fatal: remote error: upload-pack: not our ref 700db229caebf6718acb949a2c145b6513595808
exit_code=128
```

The actual new-venv and clean-clone installs used process-local GIT_CONFIG_COUNT/GIT_CONFIG_KEY_0/GIT_CONFIG_VALUE_0 to map the GitHub mdq URL to the original local Git repository. The installed package still records the exact requested commit. No dependency implementation was copied into indexkit; no global Git URL mapping was installed.

```text
{
  "url": "https://github.com/byte-banditt/mdq.git",
  "vcs_info": {
    "commit_id": "700db229caebf6718acb949a2c145b6513595808",
    "requested_revision": "700db229caebf6718acb949a2c145b6513595808",
    "vcs": "git"
  }
}
```

### Declared dependencies

| Group | Values |
| --- | --- |
| Runtime | `pandas`, `numpy`, `scipy`, `matplotlib`, `openpyxl`, `python-pptx`, `pyyaml`, `mdq @ git+https://github.com/byte-banditt/mdq.git@700db229caebf6718acb949a2c145b6513595808` |
| Dev | `pytest`, `pytest-cov`, `ruff` |

## Step gates: complete successful pytest / lint output

Steps 0 and 1 were read-only inventory/hygiene reporting before a new repository existed. New-project tests, lint and commits for those steps: NOT RUN; no project existed to run or commit. Step 2 restored the necessary sanitized runtime code and added bootstrap test/lint settings before its gate. The bootstrap settings were replaced by pyproject.toml in Step 3.

An initial Step 2 draft test failed because its prerequisite digital plot was absent. The test now calls the actual options artifact generator before draft generation. The first lint gate reported import ordering and one line-length error; these were fixed without disabling rules. No next step began until both checks passed.

### step2

`pytest -q`

```text
........................................................................ [ 77%]
.....................                                                    [100%]
93 passed in 32.74s
```

`ruff check`

```text
All checks passed!
```

### step3

`pytest -q`

```text
................................................................s....... [ 75%]
.......................                                                  [100%]
94 passed, 1 skipped in 30.78s
```

`ruff check`

```text
All checks passed!
```

### step4

`pytest -q`

```text
................................................................s....... [ 74%]
.........................                                                [100%]
96 passed, 1 skipped in 29.77s
```

`ruff check`

```text
All checks passed!
```

### step5

`pytest -q`

```text
................................................................s....... [ 74%]
.........................                                                [100%]
96 passed, 1 skipped in 30.84s
```

`ruff check`

```text
All checks passed!
```

### step5-final

`pytest -q`

```text
................................................................s....... [ 74%]
.........................                                                [100%]
96 passed, 1 skipped in 31.18s
```

`ruff check`

```text
All checks passed!
```

### step6-mdq

`pytest -q` (mdq proposal worktree)

```text
............................                                             [100%]
28 passed in 1.73s
```

`ruff check`

```text
All checks passed!
```

### step6

`pytest -q`

```text
................................................................s....... [ 74%]
.........................                                                [100%]
96 passed, 1 skipped in 28.88s
```

`ruff check`

```text
All checks passed!
```

### step7

`pytest -q`

```text
................................................................s....... [ 74%]
.........................                                                [100%]
96 passed, 1 skipped in 26.97s
```

`ruff check`

```text
All checks passed!
```

## Clean-clone commands and exit codes

A new --no-local clone at /tmp/proof and a new venv were created. Runtime: Python 3.13.12. The install below had the local transport mapping described above. No system-site-packages shortcut was used.

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

The real-data commands additionally set INDEXLAB_DB to the existing original DB. Fast and full fixture rebuilds, console rebuild, real-data fast rebuild and the optional realdata test succeeded. The real-data full rebuild was NOT RUN during extraction. Full fixture output recorded:

```text
{
  "java": "Python/Java cases passed: 5",
  "R": "NOT DONE: Rscript unavailable; R cross-check NOT RUN"
}
```

Realdata pytest output:

```text
.                                                                        [100%]
1 passed, 96 deselected in 0.59s
```

## Outputs, confinement and original-repository proof

Hash snapshots covered 104 existing source DB/report/doc files. Changed paths after the local proof: `[]`. The original source status stayed empty and master stayed at `700db229caebf6718acb949a2c145b6513595808`. Output roots for the proof were under /tmp/index-proof-artifacts; tests used pytest temporary directories. Market-price DB reads are read-only.

NOT DONE: universal filesystem-write confinement. The initial extraction-tool install used the default home pip cache. The subsequent cache scan observed these modified-file counts:

| Cache | Modified since tool-venv creation |
| --- | --- |
| pip | 8 |
| matplotlib | 0 |

Subsequent pip installs and later proof/test matplotlib caches were explicitly redirected to temporary directories. The cache observation is not an exhaustive filesystem audit; no claim of zero external writes is made.

## Unmerged mdq cleanup proposal

Branch: `move-index-lab`; commit `e1cee89f9155f5e1485bfe6e0a198787e8d1b1d3`. Commits ahead of master: `1`. It removes tracked index files and replaces the index-specific README sections with a NEW_REPO_URL move placeholder. Created/tested in /tmp/mdq-move-index-lab; the original checkout never had its index files removed.

Original checkout final branch/head verification:

```text
master
700db22 docs: record rebuild evidence and project limits
git status --short: empty
```

## Behavior changes

- Own checkout paths and installed dependency replace parent-source paths. INDEXLAB_DB overrides the configured DB; normal tests explicitly clear that override.
- PyYAML accepts YAML configs as well as the existing JSON syntax; static configuration input values for strategy defaults were retained.
- Git default-history checks now inspect the extracted config history.
- Career-facts output and the career-oriented audit module/test were removed. Computed report generation remains; public drafts use the new drafts module and local plot copies.
- Added ingestion-config writer, optional read-only realdata test, README inventory coverage and the requested offline CI definition. No ingestion download was executed.
- Artifact root semantics remain: reports and generated docs under the chosen root. Default reports directory is reports inside the standalone checkout.
- Directory publication retains rollback semantics; no live-operation behavior was introduced.

## NOT DONE / NOT RUN

- NOT DONE: fetching the exact pinned mdq SHA from GitHub; public installation remains blocked until that source commit is publicly available.
- NOT RUN: GitHub Actions, or local Python matrix runtimes other than the actual runtime above.
- NOT RUN: R comparison; Rscript unavailable. Java comparison did run in the full fixture build.
- NOT RUN: market-data download, real-data full rebuild, wheel/non-editable runtime proof.
- NOT DONE: blanket zero-external-files claim; initial pip-cache writes occurred as documented.
- NOT RUN: repository creation, any push, cleanup merge or deletion from the original master checkout.
- NOT DONE: replacement of the proposal URL placeholder; requires the actual published repository URL.

## Publish commands for the user — not executed

Before these commands, the requested mdq pin must become publicly fetchable for public installs and CI to work. No source commit was published during extraction. From the standalone checkout:

```text
gh repo create index-lab --public --source=. --remote=origin
git push -u origin master
```

Or create the remote repository yourself, then:

```text
git remote add origin https://github.com/byte-banditt/index-lab.git
git push -u origin master
```

After publishing and explicitly confirming the mdq removal, from the original mdq checkout:

```text
git switch master
git show --stat move-index-lab
git merge --ff-only move-index-lab
pytest -q
ruff check
```

Replace NEW_REPO_URL in mdq README with the published URL and commit that documentation update normally. Do not amend existing mdq commits. The temporary proposal worktree can then be removed if no longer needed. No merge/push command above was run.

## Standalone log before the final report commit

```text
b3a5a00 docs: record unmerged mdq move proposal
87cb32f test: record local clean-clone proof
4fe757c docs: document standalone setup and inputs
39480e8 build: package index-lab and add offline CI
f6a30ca refactor: extract standalone index toolkit
c7eea71 docs: record rebuild evidence and project limits
bcc63b0 feat: generate author drafts with numbers boxes
cd5bc9c feat: exercise full build and language checks
c5b11f3 feat: report bootstrap and drawdown robustness
d2b3167 feat: independently validate autocall pricing
9acf5f3 feat: add INR multi-asset index and audit fixes
ddc63cb feat: add index and derivatives toolkit
```
