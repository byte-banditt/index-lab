# Index Lab

Offline Python research tools for configurable equity and multi-asset indices, daily monitoring, attribution, stress, textbook derivatives pricing and computed Excel/PowerPoint reports. The project uses [mdq](https://github.com/byte-banditt/mdq) for ingestion, SQLite storage and its data-quality checks; it contains no copied mdq implementation.

## Scope and limits

The real-data universe is a survivor sample of Indian equities; current Nifty membership and adjusted-close provenance are unverified. Performance, tracking error and historical beta use the Nifty 50 **price** index (`^NSEI` close) against adjusted-close stocks, so this is not a matched total-return comparison. Sector Brinson attribution uses the labelled equal-weight sample proxy because official Nifty sector weights are absent. MULTI attribution instead compares asset sleeves against fixed configured weights. Rates and skew inputs are illustrative, with no market calibration. R check: **NOT RUN** here because Rscript is unavailable. There are no live operations, vendor integrations or investment recommendations. Fixture observations, including its `^NSEI`, are synthetic; their outputs are not market performance.

## Install

Run from this checkout:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

The exact mdq dependency is pinned in [pyproject.toml](pyproject.toml) to the source repository's local master at extraction, to retain the storage/DQ behavior actually used. That SHA was not available on the public remote when tested. **Public installation and GitHub CI are not yet proven and cannot fetch that pin until it is published.** The extraction proof used a temporary Git URL transport mapping to the local mdq repository at the identical SHA; it did not change the dependency declaration. No pushes were made.

## Quickstart: synthetic fixture

After installation, from the checkout:

```bash
python -m indexkit.fixtures --directory /tmp/index-lab-fixture
python run_all.py --config /tmp/index-lab-fixture/fixture_config.json --output-dir /tmp/index-lab-fixture/artifacts
python run_all.py --full --config /tmp/index-lab-fixture/fixture_config.json --output-dir /tmp/index-lab-fixture/full-artifacts
index-lab --config /tmp/index-lab-fixture/fixture_config.json --output-dir /tmp/index-lab-fixture/console-artifacts
```

The default is fast; full mode also runs Monte Carlo studies and available language cross-checks. Fixture generation is offline and uses mdq's schema/upsert functions. Each artifact root contains `reports/` and generated `docs/`. Without an output override these directories are inside the checkout; reports default to `reports/`. `--output-dir` or `INDEXLAB_OUTPUT_DIR` changes the artifact root. DB defaults to `data/mdq.sqlite`, resolved relative to the config file. `INDEXLAB_DB` overrides only the DB path; `INDEXLAB_CONFIG` overrides the config file. All source DB access by the index pipeline is read-only.

## Build real data with mdq

The installed [mdq CLI](https://github.com/byte-banditt/mdq) accepts these commands. This optional ingestion downloads market data; CI and tests never run it.

```bash
python scripts/make_ingestion_config.py --output data/mdq_ingestion.yaml
mdq init-db --config data/mdq_ingestion.yaml
mdq run --full --config data/mdq_ingestion.yaml
python run_all.py
python run_all.py --full
```

The config writer derives symbols, dates, DB location and DQ settings from [config.yaml](config.yaml), including equity, gold, the US stock, FX and the benchmark. Ingestion itself was **NOT RUN** during extraction. For an existing DB:

```bash
INDEXLAB_DB=/absolute/path/to/mdq.sqlite python run_all.py --output-dir /tmp/index-lab-real
```

Missing MULTI source symbols are reported as `NOT DONE`; they are not substituted with invented data. Required equity data errors block calculation.

## Module inventory

| Module | Purpose | Tests |
| --- | --- | --- |
| [indexkit/__init__.py](indexkit/__init__.py) | Package namespace | [tests/test_standalone.py](tests/test_standalone.py) |
| [indexkit/atomic.py](indexkit/atomic.py) | Directory snapshot publication and rollback | [tests/test_atomic.py](tests/test_atomic.py) |
| [indexkit/attribution.py](indexkit/attribution.py) | Monthly sector/proxy and asset-sleeve attribution; linked contributors | [tests/test_attribution_stress.py](tests/test_attribution_stress.py), [tests/test_multi.py](tests/test_multi.py) |
| [indexkit/calendar.py](indexkit/calendar.py) | Observed sessions, decision/effective dates and calendar flags | [tests/test_phase1.py](tests/test_phase1.py), [tests/test_monitor.py](tests/test_monitor.py) |
| [indexkit/crosschecks.py](indexkit/crosschecks.py) | Equity MC/IV, Java and optional R checks in full builds | [tests/test_crosschecks.py](tests/test_crosschecks.py), [tests/test_java.py](tests/test_java.py) |
| [indexkit/data.py](indexkit/data.py) | Config/env paths, read-only SQLite inventory and reused mdq DQ | [tests/test_phase1.py](tests/test_phase1.py), [tests/test_standalone.py](tests/test_standalone.py) |
| [indexkit/drafts.py](indexkit/drafts.py) | Computed boxes and plots with author placeholders | [tests/test_drafts.py](tests/test_drafts.py) |
| [indexkit/fixtures.py](indexkit/fixtures.py) | Offline synthetic SQLite observations through mdq storage | [tests/conftest.py](tests/conftest.py), [tests/test_reporting.py](tests/test_reporting.py) |
| [indexkit/index_engine.py](indexkit/index_engine.py) | Shared BaseIndex engine, MOM10/LVOL10/MULTI, costs and benchmark metrics | [tests/test_phase1.py](tests/test_phase1.py), [tests/test_multi.py](tests/test_multi.py) |
| [indexkit/monitor.py](indexkit/monitor.py) | Daily exceptions, rebalance proposals and computed explanations | [tests/test_monitor.py](tests/test_monitor.py) |
| [indexkit/multi_asset.py](indexkit/multi_asset.py) | Equity/gold/USD stock sleeves, FX conversion and flagged holiday fills | [tests/test_multi.py](tests/test_multi.py) |
| [indexkit/options.py](indexkit/options.py) | European vanilla/digital prices, Greeks, implied volatility and scenarios | [tests/test_options.py](tests/test_options.py), [tests/test_crosschecks.py](tests/test_crosschecks.py) |
| [indexkit/rates.py](indexkit/rates.py) | Discount curve, swaps, Black-76, spreads and accrual pricing | [tests/test_rates.py](tests/test_rates.py) |
| [indexkit/reporting.py](indexkit/reporting.py) | Computed CSV/Excel/PowerPoint, methodology and periodic reporting | [tests/test_reporting.py](tests/test_reporting.py), [tests/test_atomic.py](tests/test_atomic.py) |
| [indexkit/robustness.py](indexkit/robustness.py) | Active-return bootstrap, parameter disclosure and linked drawdowns | [tests/test_robustness.py](tests/test_robustness.py) |
| [indexkit/stress.py](indexkit/stress.py) | Historical held-weight replay, shocks, beta and composition | [tests/test_attribution_stress.py](tests/test_attribution_stress.py), [tests/test_robustness.py](tests/test_robustness.py) |
| [indexkit/structured.py](indexkit/structured.py) | Illustrative autocall GBM, CRN sensitivities and skew | [tests/test_structured.py](tests/test_structured.py) |
| [indexkit/validation.py](indexkit/validation.py) | Independent autocall simulation, degenerate cases and convergence | [tests/test_structured.py](tests/test_structured.py) |
| [run_all.py](run_all.py) | Fast/full pipeline and atomic outputs; console entry point | [test_reporting.py](tests/test_reporting.py), [test_atomic.py](tests/test_atomic.py) |
| [explain_day.py](scripts/explain_day.py) | Read stored weights, contributions and flags | [test_crosschecks.py](tests/test_crosschecks.py) |
| [make_ingestion_config.py](scripts/make_ingestion_config.py) | Write mdq inputs from config without a download | [test_standalone.py](tests/test_standalone.py) |
| [Java](java_bs/BlackScholes.java) | Independent vanilla price/delta comparison | [test_java.py](tests/test_java.py) |
| [R](r_check/verify.R) | Optional metric comparison; NOT RUN here | [test_crosschecks.py](tests/test_crosschecks.py) checks unavailable-tool status |

## Tests and lint

```bash
pytest -q
ruff check
pytest -q -m 'not realdata'
INDEXLAB_DB=/absolute/path/to/mdq.sqlite pytest -q -m realdata
```

Normal tests build a synthetic fixture DB and write to pytest temporary directories. The `realdata` test is read-only and skips with a reason when its DB is absent. The README link and inventory checks are in [test_reporting.py](tests/test_reporting.py) and [test_standalone.py](tests/test_standalone.py). [CI](.github/workflows/ci.yml) declares the requested Python matrix and offline rebuild; it has not been executed on GitHub.

## Project layout

```text
pyproject.toml       dependency declarations and console entry point
config.yaml          strategy, model, path and ingestion inputs
indexkit/            calculation and reporting package
tests/               synthetic tests and optional read-only realdata check
scripts/             debugging and ingestion-config writer
data/                tracked small static CSVs; local DB ignored
docs/                runbook, templates and generated documents
reports/             generated artifacts; ignored
java_bs/             optional Java reference implementation
r_check/             optional R metric check
run_all.py           fast/full entry point
Makefile             fast, full, fixture, test and lint commands
```

## Calculation choices

Trading sessions come from observed source dates. Decisions use only information through the final observed session of a month, with target holdings effective on the following session. MOM10 selects momentum winners; LVOL10 selects lower trailing realized volatility. Their lookbacks and holding counts are config inputs. Stored weights are beginning-of-day weights and drift with realized constituent returns. Costs use absolute traded weights and configured per-side bps, reducing capital before the session return; gross/net calculations share holdings. `BaseIndex` and its subclasses share one engine.

MULTI combines the equal-weight equity sample, gold and the US stock translated with USDINR. It uses fixed configured targets and the same drift, cost and rebalance engine. The India session calendar governs publication. Missing foreign quotes may carry forward for at most the configured calendar-day age; every carried quote is a monitor flag. Required non-foreign missing bars block calculation. Read [multi_asset.py](indexkit/multi_asset.py) and its tests for the exact convention.

Brinson effects reconcile to monthly gross active return. Trading costs and the multi-period compounding residual are separate fields. Historical stress uses each day's held weights. Market-shock betas are historical paired estimates; sector groupings are static project-authored inputs, not an official classification. Missing benchmark observations remain missing and paired metrics omit invalid pairs.

European options assume constant volatility, continuous rates/dividend yield and European exercise. Black-76 rates products use illustrative forwards and a single log-linearly interpolated discount curve; supplied times are ACT/365-style fractions, without exchange-calendar or collateral adjustments. The autocall is a simplified GBM contract with coupons at alive observations, discrete knock-in monitoring and exact observation-grid nodes. Credit/funding risk and calibration are absent. The independent implementation and convergence outputs describe this contract only; Monte Carlo error remains.

Block-bootstrap intervals and the full parameter grid are disclosures, not selection rules. The configured strategy defaults were not changed during extraction; the default-history CSV recomputes comparisons against the extracted config history. Confidence intervals and drawdown explanations are generated from data. Directory publication rolls back failed renames; it is not a cross-directory transaction for concurrent readers.

## Results and generated documents

Universe membership and adjustment provenance remain unverified. The price-index performance benchmark and the sector proxy have different definitions. All numerical results and result prose are generated by code: read `reports/summary.csv`, `reports/bootstrap.csv`, `reports/default_history.csv`, `docs/commentary.md`, `docs/monitor_review.md` and `docs/drawdown_commentary.md` after a rebuild. This README provides no hand-entered performance values. Generated drafts contain numbers boxes and author placeholders; the [flow primer](docs/equity_derivs_flow_primer.md) remains questions only.
