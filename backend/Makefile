.PHONY: install dev lint fmt type ci test migrate revision

install:
	uv sync --locked

dev:
	uv run uvicorn app.main:app --reload

lint:
	uv run ruff check app tests

fmt:
	uv run ruff format app tests
	uv run ruff check --fix app tests

type:
	uv run mypy app

ci:
	uv run ruff check app tests
	uv run mypy app
	uv run pytest

test:
	uv run pytest

migrate:
	uv run alembic upgrade head

revision:
	uv run alembic revision --autogenerate -m "$(m)"
