.PHONY: build

ci:
	uv sync
	uv run ruff format .
	uv run ruff check --fix .
	uv run ty check app/
	uv run pytest

dev:
	uv run fastapi dev main.py