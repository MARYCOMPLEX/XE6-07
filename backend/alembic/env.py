"""Alembic migration environment (async).

Pulls the DB URL from application settings (single source of truth) instead of
the ini, and targets the shared ``Base.metadata`` from ``app.models`` — importing
that package registers every table so ``--autogenerate`` sees the full schema.
"""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import the models package so every table registers on Base.metadata.
import app.models  # noqa: F401
from app.core.config import settings
from app.models.base import Base

config = context.config
# set_main_option 走 ConfigParser 插值，URL 里的 `%`（如密码 `p%40ss`）会被当成
# 插值语法而报错，因此转义为 `%%`。env.py 各处使用时用的是原始 settings.database_url，
# 只有写入 ini 配置项时需要转义。
config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit SQL without a live DB connection."""
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations with an async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
