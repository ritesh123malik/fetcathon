.PHONY: install dev api agents web build test lint serve
install:
	uv sync --python 3.11
	cd frontend && npm ci
api:
	uv run uvicorn backend.api:app --reload --host 127.0.0.1 --port 8000
agents:
	uv run python -m agents.runtime
web:
	cd frontend && npm run dev
build:
	cd frontend && npm run build
test:
	uv run pytest -q
lint:
	uv run ruff check backend agents scripts tests
serve:
	uv run python -m scripts.serve
