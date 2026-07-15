.PHONY: install dev lint fmt type ci test migrate revision

install:
	uv sync --locked

dev:
	uv run uvicorn app.main:app --reload

lint:
	uv run ruff check app

fmt:
	uv run ruff format app
	uv run ruff check --fix app

type:
	uv run mypy app

ci:
	uv run ruff check app
	uv run mypy app

# 骨架阶段不运行单元测试，只做静态检查；保留 test 目标向后兼容。
test: ci

migrate:
	uv run alembic upgrade head

revision:
	uv run alembic revision --autogenerate -m "$(m)"
