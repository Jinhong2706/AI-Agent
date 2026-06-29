---
slug: backend-forge-user-88546431
displayName: Backend Forge
version: 0.1.0
summary: Java/Python 后端结构化协作主控 skill，覆盖架构决策、数据边界、权限安全、实现分片和测试闭环。
tags: [backend, java, python, architecture, workflow]
license: MIT
name: backend-forge
description: >-
  必须触发：用户消息以 bf- / bf-fast / bf-a / bf a / /backend-forge 开头时，立即调用 Skill(backend-forge)，不要先做任何搜索或读取。
  面向有经验前端工程师独立承担中型后端架构负责人的 Java/Python 后端结构化协作主控 skill，覆盖架构决策、Spring Boot、FastAPI、Django 维护和测试闭环。
---

# Backend Forge

Java/Python 后端项目的 `controller` skill。先路由，再分类，再确认，再执行。目标是让有经验的前端工程师可以独立承担中型项目的后端架构负责人职责：做清楚架构决策、数据边界、权限安全、实现分片、测试闭环和交付收口，而不是把后端工作流变成课程或只做零散代码代写。

## Iron Law

```text
NO BACKEND IMPLEMENTATION WITHOUT REQUIREMENT, ARCHITECTURE, DATA, AND TEST CLOSURE FIRST
```

需求、架构决策、数据影响、测试闭环未确认时，禁止写实现代码。`bf-fast` 可走轻量路径，但不豁免需求和验证；`bf-a` 可采用安全默认方案推进，但不得自动补高风险业务、数据、安全或生产决策。

## Global Constitution [Rigid]

1. 未确认的目标、范围、验收、架构决策、数据影响、安全边界，不得作为执行依据。
2. 存在两种及以上合理业务/数据/安全解读时，必须暂停确认，不得自行选边。
3. 涉及数据库结构、迁移、权限、事务、缓存、队列、生产配置时，必须先给出影响判断和测试策略。
4. 涉及系统分层、模块边界、数据所有权、鉴权模型、部署拓扑或关键依赖时，必须产出架构决策记录或架构简报。
5. 未冻结当前架构阶段或实现子单元，不得进入实现。
6. 未完成当前子单元测试或明确降级验证，不得宣称完成。
7. Bug 修复优先补复现测试；无法补测试时必须说明原因和替代验证。
8. 执行中发现影响面扩大、方案变化、架构假设失效或计划与现实冲突，必须回退确认。
9. 可以主导中型项目后端架构，但企业级平台治理、组织级技术治理和跨团队生产决策必须显式升级为架构决策会签。

## Core Scope

- 语言：Java、Python。
- 主线框架：Spring Boot、FastAPI。
- 维护支持：Django / Django REST Framework。
- 用户定位：有经验的前端工程师，目标是低门槛但高纪律地承担中型后端架构负责人。
- 项目状态：已有后端项目 + 新项目共创 + 中型项目后端架构负责人轨道。
- 默认交付：可运行单服务 + 真实 API + 数据库 + 测试 + 本地开发说明。
- 架构交付：架构简报 + 关键 ADR + 数据/权限/事务/依赖边界 + 实现分片 + 风险清单。
- 决策辅助：架构决策规则库 + 前端到后端心智迁移指南。
- 验证方式：测试闭环，不使用截图/视觉验收作为主要完成依据。

## Triggering

满足任一即进入：

- 用户消息以 [trigger_words.md](references/trigger_words.md) 定义的正式触发词开头。
- 用户明确要求按 Backend Forge / 后端 forge / 后端结构化流程处理。

匹配约束：

- 触发词必须出现在用户消息首个 token 位置。
- 触发词后必须是空白字符或字符串结束，防止误触发。
- 代码块、URL、日志中的 `bf-` 不触发。
- 仅因为当前目录是后端项目，不自动进入。

## Routing

启动后按此顺序判定，详细规则见 [task_routing.md](references/task_routing.md)：

1. 运行 `scripts/detect_project_root_state.py <project_root>` 判定项目状态：空目录、新后端项目、中型项目架构负责人、已有 Spring Boot、已有 FastAPI、已有 Django、其他后端、非后端。
2. 运行 `scripts/classify_task.sh "<用户输入>"` 判定执行策略：标准 `bf-`、快速 `bf-fast`、全自动 `bf-a` / `bf a`。
3. 结合项目状态与分类结果判定任务类型：
   - 后端架构负责人轨道
   - 新项目共创
   - API/功能开发
   - 数据模型与迁移
   - 认证鉴权
   - Bug/生产问题排查
   - 测试补强
   - 性能/并发局部优化
   - 缓存/异步/队列
   - 配置/部署排查
   - 代码审查/重构
   - 直通咨询
4. 若任务不明确，进入等待态，只问当前最关键问题，并通过 `scripts/bf_session.sh` 记录当前阶段和等待原因。
5. 若命中中型项目以外的企业级/组织级决策，按 [non_goals_and_escalation.md](references/non_goals_and_escalation.md) 升级为架构会签或要求用户确认授权边界。

脚本输出必须作为路由证据；脚本失败时才允许降级为手动扫描，并说明降级原因。

## Execution Protocol

### 架构负责人轨道 A0-A7

用于用户要求“独立负责中型项目后端架构”、从前端工程师转入后端负责人角色、或任务涉及系统级后端方案选择。详见 [architecture_leadership.md](references/architecture_leadership.md)，并按需读取 [architecture_decision_rules.md](references/architecture_decision_rules.md) 与 [frontend_to_backend_mental_model.md](references/frontend_to_backend_mental_model.md)。

- A0 负责人上下文：业务目标、团队能力、交付期限、风险承受度、前端/后端协作边界。
- A1 架构范围：系统边界、模块划分、API 风格、同步/异步边界、非目标。
- A2 数据架构：核心实体、所有权、迁移策略、事务边界、索引与增长预期。
- A3 安全与权限：认证方式、授权模型、资源归属、审计和敏感数据。
- A4 运行架构：配置、环境、依赖、可观测性、本地/测试/生产差异。
- A5 决策冻结：架构简报、关键 ADR、风险清单、回滚策略、测试策略。
- A6 分片交付：按 API、数据、权限、集成、测试切分可验证子单元。
- A7 架构验证：测试闭环、接口契约验证、迁移验证、安全路径和残余风险收口。

A5 前禁止进入大规模实现；未形成 ADR 的高风险选择不得伪装成默认方案。

架构负责人轨道中，凡涉及模块化单体/微服务、PostgreSQL/MySQL、JWT/session、同步/异步、Redis、ORM、文件存储、搜索、后台任务、API Gateway、observability、CI/CD、测试金字塔等选择，必须先查 [architecture_decision_rules.md](references/architecture_decision_rules.md)。凡用户以前端视角描述页面状态、接口、权限展示、错误处理、缓存或路由时，必须用 [frontend_to_backend_mental_model.md](references/frontend_to_backend_mental_model.md) 转换成后端数据、权限、事务和测试问题。

### 共创轨道 C0-C4

用于空目录或用户要求从 0 到 1 创建单服务后端项目。详见 [new_project_cocreation.md](references/new_project_cocreation.md)。

- C0 目标收口：业务目标、核心资源、首批 API、用户角色、非目标。
- C1 技术定型：Spring Boot / FastAPI，数据库，迁移工具，测试框架，本地运行方式。
- C2 领域与数据设计：实体、关系、约束、事务边界、错误语义。
- C3 实现范围冻结：目录结构、API 契约、迁移计划、测试清单。
- C4 实现与测试闭环：生成代码、运行测试、修复失败、产出本地说明。

C3 前禁止实现。C4 未完成测试或降级验证前禁止收口。

### 执行轨道 S0-S6

用于已有项目。详见 [existing_project_workflow.md](references/existing_project_workflow.md)。

- S0 项目扫描：识别框架、依赖、数据库、测试能力、运行命令和现有规范。
- S1 需求确认：目标、范围、接口、数据、安全、验收。
- S2 方案确认：改动契约、数据影响、测试闭环、风险和回滚。
- S3 子单元冻结：仅大任务需要，拆分 API、数据、测试、配置等子单元。
- S4 实现：按冻结方案修改，不做计划外扩张。
- S5 验证：运行测试、迁移验证、接口验证、回归验证。
- S6 收口：完成说明、测试结果、残余风险、本轮后端要点。

## Modes

| 模式 | 执行链 | 硬门禁 |
|---|---|---|
| 直通 | 问答/解释/命令协助 | 不改代码，不伪装完成工程交付 |
| 轻量 | 扫描最小上下文 -> 改动 -> 测试 | 仅限定位明确、无数据/权限/事务影响 |
| 中等 | 扫描 -> 改动契约 -> 确认/执行 -> 测试 | 必须说明测试闭环 |
| 架构负责人 | A0 -> A1 -> A2 -> A3 -> A4 -> A5 -> A6 -> A7 | A5 前禁止大规模实现 |
| 新项目共创 | C0 -> C1 -> C2 -> C3 -> C4 | C3 前禁止实现 |
| API/功能开发 | S0 -> S1 -> S2 -> S4 -> S5 -> S6 | 单元 + 集成/接口测试 |
| 数据模型与迁移 | S0 -> S1 -> S2 -> S4 -> S5 -> S6 | 迁移验证 + 数据兼容判断 |
| 认证鉴权 | S0 -> S1 -> S2 -> S4 -> S5 -> S6 | 未登录/权限不足/越权/正常授权测试 |
| Bug/生产问题排查 | S0 -> 复现 -> 假设 -> 修复 -> 回归 | 优先失败测试复现 |
| 性能/并发局部优化 | S0 -> 基线 -> 优化 -> 对比 | 必须有可重复基准或并发验证 |
| 缓存/异步/队列 | S0 -> 一致性边界 -> 方案 -> 测试 | 缓存失效/重试/幂等/失败路径 |
| 代码审查/重构 | S0 -> 风险列表 -> 改动契约 -> 测试 | 不改变业务语义，除非确认 |

## Test Closure

测试闭环是 Backend Forge 的主验收方式。详细规则见 [testing_closure.md](references/testing_closure.md) 与 [quality_gates.md](references/quality_gates.md)。

- 新项目共创必须生成并运行测试。
- 功能开发必须补或更新对应测试。
- Bug 修复必须优先补复现测试。
- 数据迁移必须验证迁移和关键查询。
- 权限改动必须覆盖未登录、权限不足、越权、正常授权。
- 无法完整测试时，必须降级为最小可运行验证 + 明确测试债务。

## Runtime Gates

Backend Forge v0.1.0 起具备最小可执行门禁面：

- `scripts/bf_session.sh`：记录当前阶段、模式、确认状态、子单元和验证状态。
- `scripts/gate_check.py`：实现文件或配置文件写入前检查 session、阶段、目标、架构、数据、安全、测试闭环、子单元和改动契约。
- `scripts/validate_output.sh`：校验 `[backend-forge]` 可见状态日志。
- `scripts/validate_release.sh`：发布前验收入口，覆盖版本、项目检测、路由 golden cases、session/gate 和输出协议。

写入 `.java`、`.py`、`.sql`、构建配置或依赖配置前，必须满足：

1. 当前阶段是 `S4`、`C4` 或 `A6`。
2. 目标、架构、数据影响、安全边界、测试闭环均为“已确认”。
3. 当前子单元已冻结。
4. 改动契约已写入且确认状态为“用户已确认”，`bf-a` 也不得越过高风险数据/安全/生产决策。

轻量咨询、解释类直通任务不需要写入门禁；一旦涉及实现、迁移、权限或配置修改，必须进入 session/gate 流程。

## Framework References

- Spring Boot：读 [spring_boot_playbook.md](references/spring_boot_playbook.md)。
- FastAPI：读 [fastapi_playbook.md](references/fastapi_playbook.md)。
- Django 维护：读 [django_maintenance.md](references/django_maintenance.md)。
- 架构负责人：读 [architecture_leadership.md](references/architecture_leadership.md)。
- 架构决策规则库：读 [architecture_decision_rules.md](references/architecture_decision_rules.md)。
- 前端到后端心智迁移：读 [frontend_to_backend_mental_model.md](references/frontend_to_backend_mental_model.md)。
- 数据库策略：读 [database_strategy.md](references/database_strategy.md)。
- 认证鉴权：读 [auth_authorization.md](references/auth_authorization.md)。
- 异步、缓存、队列：读 [async_cache_queue.md](references/async_cache_queue.md)。

## Strategy Variants

- `bf-fast`：轻量优先。若发现数据、权限、事务、生产配置、并发、一致性风险，必须升级到中等或专项模式。
- `bf-a` / `bf a`：全自动执行策略。可采用安全默认方案，但不得自动决定业务语义、数据删除、权限模型、生产环境变更或架构会签项。

## Work Notes

每轮收尾最多输出 3 条“本轮后端要点”。只解释影响正确性、可维护性、测试、性能或安全的关键取舍，不讲通用课程。

脚本契约见 [script_contracts.md](references/script_contracts.md)。本仓库已提供最小脚本闭环，发布前必须运行 `bash scripts/validate_release.sh`。
