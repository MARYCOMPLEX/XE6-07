# XE6-07 Backend

XE6-07 一站式 3D 打印系统的后端服务。

这是后端的**基础骨架**：只包含 FastAPI 应用装配、共享基础设施和项目结构。
业务模块（身份、工作流、资产、社区、打印等）与外部服务集成会在后续独立 PR 中陆续加入。

技术栈：FastAPI + async SQLAlchemy，用 [uv](https://docs.astral.sh/uv/) 管理依赖。

## 环境要求

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/)

## 快速开始

```bash
make install    # uv sync --locked，安装锁定依赖
make dev        # 启动 API（热重载）
```

启动后访问：

- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

当前骨架不连接数据库：`app.core.db` 提供一个记录日志的会话替身，
让依赖与迁移环境在没有 Postgres 的情况下也能解析。真实数据库装配会在基础设施 PR 中接入。

## 常用命令

| 命令 | 作用 |
|---|---|
| `make install` | 安装锁定依赖（uv sync --locked） |
| `make dev` | 启动 API（热重载） |
| `make lint` | Ruff 代码检查 |
| `make fmt` | Ruff 格式化并自动修复 |
| `make type` | mypy 严格类型检查 |
| `make ci` | CI 检查（ruff + mypy + pytest） |
| `make test` | 运行 pytest 回归测试 |
| `make migrate` | 应用 Alembic 迁移到最新 |
| `make revision m="..."` | 生成新的 Alembic 迁移 |

## 目录结构

```
app/
├── core/         # config / db / logging / exceptions
├── contracts/    # 跨模块共享的不可变契约（DTO / 枚举）
├── models/       # SQLAlchemy 声明式基类与 mixin
├── repositories/ # 通用异步仓储基类
├── schemas/      # 共享 Pydantic 响应模式
├── api/          # 版本化路由聚合（骨架阶段为空）
└── main.py       # FastAPI 应用工厂
alembic/          # 数据库迁移脚手架（骨架阶段无业务迁移）
docker/           # API 镜像 Dockerfile
```

## CI

仓库根的 `.github/workflows/ci.yml` 会在推送到 `main` 或提交 PR 时运行，进入本 `backend/` 目录执行：

- Ruff 代码检查
- mypy 严格类型检查
- Python 编译与 FastAPI 应用导入
- pytest 回归测试

CI 不连接外部服务、不部署应用。依赖版本由 `uv.lock` 锁定。
