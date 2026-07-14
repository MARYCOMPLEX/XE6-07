# 提案：打印状态查看、异常解释和取件记录

## 动机 / 用户故事

用户确认打印后，需要知道任务是否排队、正在打印、暂停、失败或完成；异常发生时需要理解原因和下一步；完成后需要获得取件记录。本期先跑通“已发送打印 → 状态可见 → 异常可解释 → 完成可取件”的最小闭环，而非完整打印农场系统。

## 目标用户

- 已提交打印任务的普通用户
- 需要查看进度的新手用户
- 处理异常和取件的设备管理员或门店人员

## 现有做法及不足

用户发送打印后离开页面，需要到打印机、厂商 App 或人工询问状态。用户无法区分排队、打印、暂停、失败和完成；设备术语对新手难以理解；完成后没有统一取件凭证；平台也无法沉淀实际完成时间、耗材和异常记录。

## 本期范围

本期做：

- 查看 `queued`、`printing`、`paused`、`failed`、`completed`、`picked_up` 状态。
- 展示任务状态、进度、预计剩余时间、打印机、耗材、开始和完成时间。
- 在暂停或失败时展示异常类型、用户可理解说明、建议下一步和原始设备错误码。
- 完成后记录实际完成时间、实际耗材和完成状态。
- 创建 `PickupRecord`，记录取件码、取件状态、取件时间和操作人。

本期明确不做：复杂打印队列调度、多打印机自动分配、远程暂停/恢复/取消控制面板、摄像头 AI 失败检测、失败赔付或自动重打、取件柜、短信验证码、线下核销、成品图、评分和社区反馈。

## 关键决策与依据

用户只看到平台内 `PrintJob` 状态，不直接暴露厂商原始状态；异常必须同时包含解释、建议和原始错误码；只有 `completed` 后才创建 `PickupRecord`；打印完成与已取件必须是独立状态。

## 基本概念与信息结构

- `PrintJob`：`id`、`checklistId`、`printerId`、`status`、`progress`、`estimatedRemainingTime`、`startedAt`、`completedAt`、`actualTime`、`actualFilament`、`lastErrorCode`、`lastErrorMessage`、`updatedAt`。
- `PrintException`：`id`、`printJobId`、`errorCode`、`rawMessage`、`displayTitle`、`displayExplanation`、`nextAction`、`severity`、`createdAt`。
- `PickupRecord`：`id`、`printJobId`、`pickupCode`、`status`、`pickedUpAt`、`pickedUpBy`、`createdAt`。

状态关系：`queued → printing → paused / failed / completed → waiting_pickup → picked_up`。

## 原型 / 演示

任务页展示模型、打印机、状态、进度、预计剩余时间、耗材和日志入口。异常页展示“耗材不足”、说明、建议和 `FILAMENT_LOW` 等原始码。完成页展示实际耗时、实际耗材、取件码和待取件状态；已取件页展示取件时间。

## 验收标准

### 例子 1：查看打印进度

- 现状：用户无法在平台内确认任务进度。
- 提议后的行为：`printing` 任务展示进度、预计剩余时间、打印机和耗材。
- 验收：进入任务页可观察以上字段且与 `PrintJob` 一致。

### 例子 2：查看排队与完成

- 现状：用户无法区分排队、完成与异常。
- 提议后的行为：`queued` 和 `completed` 展示各自状态。
- 验收：两种状态均不显示错误信息。

### 例子 3：异常可解释

- 现状：设备错误码对用户没有操作意义。
- 提议后的行为：`FILAMENT_LOW` 展示“耗材不足”、原因说明和建议下一步。
- 验收：暂停或失败状态保留原始码，同时展示解释和建议。

### 例子 4：完成后生成取件记录

- 现状：完成与取件没有可追溯记录。
- 提议后的行为：`completed` 时生成 `PickupRecord`。
- 验收：记录为 `waiting_pickup` 且具有取件码。

### 例子 5：取件后更新状态

- 现状：打印完成无法证明实物已交付。
- 提议后的行为：管理员或系统确认取件后记录时间与操作人。
- 验收：`PickupRecord` 更新为已取件，任务状态变为 `picked_up`。

### 例子 6：未完成任务不能取件

- 现状：不应对尚未完成的实物提供取件凭证。
- 提议后的行为：`queued`、`printing`、`paused`、`failed` 不生成可用取件记录。
- 验收：这些状态不能进入取件流程。
