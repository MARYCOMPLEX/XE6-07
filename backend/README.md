# XE6-07 Backend

XE6-07 一站式 3D 打印系统的后端服务。

这是后端的**分模块骨架**，按功能桶逐个 PR 落地。已就位：

- **应用装配与共享基础设施**：FastAPI 装配、配置、日志、异常、DB/依赖脚手架。
- **用户身份与认证模块**（users）：注册 / 登录发放 JWT / `GET`、`PATCH /me`。
- **工作流桶**（projects / generation / 状态机）：项目工作台、状态流转、设计意图、
  对话，多模态生成入口（文生图 / 图生图 / 图生模型 / 意图识别），以及项目状态机、
  意图规划器与基于 Celery 的任务编排骨架。
- **资产桶**（assets）：模型资产与不可变版本（血缘链 / 当前版本指针 / 回滚）、网格
  审计报告数据模型，以及对象存储客户端与凭据可观测层（骨架 mock，不连 S3/MinIO）。

各模块 service 层当前为不落库的 **mock 桩**，只锁定 API 契约、状态机边界与数据模型，
待真实持久化接入后替换。其余业务模块（社区、打印等）与外部服务集成会在后续独立 PR
中陆续加入。

技术栈：FastAPI + async SQLAlchemy，任务编排用 Celery（骨架强制 eager 内联，不连
Redis），对象存储抽象为 StorageClient（骨架 mock），用 [uv](https://docs.astral.sh/uv/) 管理依赖。

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
├── core/         # config / db / logging / exceptions / security / deps / storage / credentials
├── contracts/    # 跨模块共享的不可变契约（DTO / 枚举 / WorkflowEvent）
├── models/       # SQLAlchemy 基类、mixin 与 User / Project / Generation / Asset 模型
├── domain/       # 纯领域规则：项目状态机、意图规划器（无 I/O，可单测）
├── repositories/ # 通用异步仓储基类
├── schemas/      # 共享 Pydantic 响应模式
├── modules/      # 业务模块（users / projects / generation / assets —— router / service / schemas）
├── tasks/        # Celery 应用与任务（骨架 eager 内联）：generation / workflow 事件桥接
├── api/          # 版本化路由聚合（已挂载 users / projects / generation / assets 路由）
└── main.py       # FastAPI 应用工厂
alembic/          # 数据库迁移脚手架（骨架阶段无业务迁移）
docker/           # API 镜像 Dockerfile
```

## CI

仓库根的 `.github/workflows/ci.yml` 会在推送到 `main` 或提交 PR 时运行，进入本 `backend/` 目录执行：

- Ruff 代码检查与格式校验
- mypy 严格类型检查
- Python 编译与 FastAPI 应用导入
- pytest 回归测试
- pytest 回归测试

CI 不连接外部服务、不部署应用。依赖版本由 `uv.lock` 锁定。
