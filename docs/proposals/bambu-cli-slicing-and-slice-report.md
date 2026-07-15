# 提案：Bambu Studio CLI 主切片链路与 SliceReport

## 动机 / 用户故事

当模型满足前置检查时，用户需要得到可读的基础切片结果和后续打印可用的产物，而不是直接面对 Bambu Studio CLI 的日志。

## 目标用户

- 已完成模型可打印性检查并准备切片的用户
- 消费统一切片结果的后续打印流程

## 本期范围

本期做：作为切片编排总提案 #116 下的 Bambu 主适配器，接收切片任务、模型 revision 内容哈希、目标设备 profile 及版本和切片方案；调用固定版本的 Bambu Studio CLI；生成切片产物；将日志和报告归一为 `SliceReport`，表达耗时、耗材、支撑、风险、产物位置、产物哈希和所用切片器版本。

本期明确不做：OrcaSlicer 或 PrusaSlicer 回退、真实打印机、复杂多色和工业级参数优化。

## 关键决策与依据

业务功能只消费 `SliceReport`，不依赖 CLI 原始输出。每次执行必须锁定并回显 `modelRevisionHash`、`profileId/profileVersion`、切片方案和 `slicerId/slicerVersion`，避免输入变化后误用旧 G-code。Bambu CLI 不可用、超时、异常退出或产物缺失时必须返回结构化错误；是否继续尝试 Orca/Prusa 由 #116/#91 的编排与回退策略决定，本适配器不自行回退。

## 基本概念与信息结构

- `BambuSliceInput`：`sliceJobId`、`modelRevisionHash`、`profileId/profileVersion`、切片方案和输出约束。
- `SliceReport`：执行状态、预计时间、耗材、支撑、风险、产物位置与内容哈希、`slicerId/slicerVersion`，以及完整输入绑定。
- `SlicerError`：错误分类、错误码、可解释原因、是否可重试和原始日志引用；业务层不直接解析原始日志。

## 验收标准

### 例子 1：基础切片成功

- 现状：切片执行结果不可读或无法交给后续打印。
- 提议后的行为：通过前置检查的测试模型以“稳妥”方案切片。
- 验收：获得产物以及时间、耗材、支撑和风险信息；结果注明 Bambu Studio CLI 及版本，回显模型 revision hash、profile 版本和方案，产物具有内容哈希。

### 例子 2：CLI 失败

- 现状：不可用、超时、异常退出和产物缺失难以区分。
- 提议后的行为：记录统一失败结果。
- 验收：四类失败均返回结构化 `SlicerError` 并正确标记是否可重试，且业务层不解析原始日志；本适配器不直接调用 OrcaSlicer 或 PrusaSlicer。

### 例子 3：不满足前置检查

- 现状：未通过可打印性检查的模型可能进入切片。
- 提议后的行为：在调用 CLI 前阻断。
- 验收：不创建可用产物，并给出明确失败状态。

### 例子 4：输入或工具版本变化

- 现状：模型几何未变之外的 profile 或 CLI 升级也可能让旧 G-code 不再适用。
- 提议后的行为：每个 `SliceReport` 保存不可变输入绑定；任一绑定变化都必须创建新的切片执行结果。
- 验收：只改变 `profileVersion` 或 `slicerVersion` 时，旧报告不能作为新任务的可用结果；新执行生成绑定新版本的报告，旧报告仅保留用于追溯。
