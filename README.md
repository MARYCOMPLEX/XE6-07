# XE6-07

XE6-07 一站式 3D 打印系统：用户从文本/图片/已有模型出发，经 Agent 引导 → 模型生成 → 可打印审计 → 轻量修复 → 切片 → 打印确认，完成从创意到实物的闭环。

## 仓库结构

本仓库按 monorepo 组织，各端代码位于独立子目录：

```
backend/     后端服务（FastAPI + async SQLAlchemy）
frontend/    前端应用（规划中）
```

## 后端

后端当前处于**基础骨架**阶段，只包含应用装配、共享基础设施和项目结构。业务模块与外部服务集成会在后续独立 PR 中陆续加入。

开发与运行说明见 [backend/README.md](backend/README.md)。

## 持续集成

`.github/workflows/ci.yml` 在推送或向 `main` / `master` 提交 PR 时运行，进入 `backend/` 执行锁文件校验、Ruff 检查与格式校验、Mypy 严格类型检查、编译、应用导入和 pytest 测试。
