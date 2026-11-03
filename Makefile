.PHONY: start-worker test

start-worker:
	DEPLOYMENT_NAME=mwig-daily-digest uv run python src/entrypoints/worker.py

test:
	python3 tests/test_parsing.py
