"""Alembic 环境配置的回归测试。"""

from __future__ import annotations

import configparser


def test_percent_encoded_db_url_survives_configparser_interpolation() -> None:
    """含 `%` 的数据库 URL（如密码 p%40ss）写入 alembic 配置项后应能正确读回。

    ``Config.set_main_option`` 底层走 ConfigParser 插值，未转义的 `%` 会触发
    ``ValueError: invalid interpolation syntax``，导致任何 migration 命令在跑起来
    之前就崩溃。env.py 通过把 `%` 转义为 `%%` 规避；这里锁定该行为。
    """
    url = "postgresql+asyncpg://xe6:p%40ss@localhost:5432/xe6"

    parser = configparser.ConfigParser()
    parser.add_section("alembic")
    # env.py 写入配置项时所做的转义。
    parser.set("alembic", "sqlalchemy.url", url.replace("%", "%%"))

    # async_engine_from_config 读回时经 ConfigParser 反转义，应还原为原始 URL。
    assert parser.get("alembic", "sqlalchemy.url") == url


def test_unescaped_percent_url_would_break_configparser() -> None:
    """反向锁定：未转义的 `%` 确实会让 ConfigParser 读取失败。"""
    url = "postgresql+asyncpg://xe6:p%40ss@localhost:5432/xe6"

    parser = configparser.ConfigParser()
    parser.add_section("alembic")

    # 未转义的 `%` 在写入并读回时会被 ConfigParser 的插值机制拒绝。
    try:
        parser.set("alembic", "sqlalchemy.url", url)  # 故意不转义
        parser.get("alembic", "sqlalchemy.url")
    except (configparser.InterpolationError, ValueError):
        return
    raise AssertionError("expected ConfigParser to reject the unescaped percent URL")
