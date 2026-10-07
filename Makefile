.PHONY: all fast test lint fixture
all:
	python run_all.py --full
fast:
	python run_all.py
fixture:
	python -m indexkit.fixtures --directory .fixture
	python run_all.py --config .fixture/fixture_config.json --output-dir .fixture/artifacts
test:
	pytest -q
lint:
	ruff check
