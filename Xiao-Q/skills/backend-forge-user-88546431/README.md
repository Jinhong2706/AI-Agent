# Backend Forge

`backend-forge` 是面向有经验前端工程师的 Java/Python 后端架构与交付 controller。它用于真实中型项目，不是训练课程：通过架构决策、需求确认、数据影响分析、安全边界、实现分片、测试闭环和收口说明，帮助前端工程师低门槛但高纪律地独立承担中型项目后端架构负责人。

当前版本：**v0.1.0**

## 触发词

- `bf-`
- `bf-fast`
- `bf-a`
- `bf a`
- `/backend-forge`

触发词需要位于用户消息开头。

## 能力边界

覆盖：

- 中型项目后端架构负责人轨道
- 架构简报、关键 ADR、实现分片和风险清单
- 模块化单体/微服务、PostgreSQL/MySQL、JWT/session、同步/异步、Redis、ORM、文件存储、搜索、后台任务、API Gateway、observability、CI/CD、测试金字塔等架构决策规则
- 前端页面状态、接口、权限展示、错误处理、缓存、路由到后端模型的心智迁移
- Spring Boot 后端开发
- FastAPI 后端开发
- Django / DRF 维护支持
- 新项目共创
- 已有项目开发、排障、优化、补测试
- API、业务逻辑、数据库、迁移、事务、认证鉴权
- 缓存、异步任务、消息队列的中型项目内用法
- 中型项目内性能和并发验证
- 配置、部署、本地运行排查

必须升级会签：

- 组织级技术治理
- 多团队平台化治理
- 企业级 IAM/SSO 平台设计
- 跨业务线数据治理
- 平台级多租户权限模型
- 大规模云平台或 DevOps 平台建设

这些不是不能讨论，而是不能由 `bf-a` 自动决定，必须形成架构会签项或用户明确授权。

## 架构负责人交付

架构负责人轨道默认产出：

- 负责人上下文摘要
- 架构范围说明
- 数据架构说明
- 权限模型和安全测试清单
- 运行架构说明
- 架构简报
- 关键 ADR
- 实现分片计划
- 风险清单和回滚策略
- 架构决策依据
- 前端到后端问题转换清单

## 默认新项目交付

新项目共创默认产出：

- 可运行单服务
- 真实业务 API
- 数据库模型与迁移/建表方案
- 单元测试与接口/集成测试
- 基础异常处理、日志、配置分层
- 本地启动、测试、配置说明

Docker、CI/CD、消息队列、缓存、认证鉴权默认不强制，按需求触发。

## 测试闭环

`backend-forge` 不依赖截图验收。完成依据是测试闭环：

- 单元测试
- 集成/接口测试
- 数据库迁移验证
- 认证鉴权测试
- Bug 复现与回归测试
- 性能/并发可重复验证

无法完整测试时，必须说明降级验证和测试债务。

## 文档结构

- [SKILL.md](SKILL.md)：主 controller。
- [VERSION](VERSION)：当前版本。
- [CHANGELOG.md](CHANGELOG.md)：版本变更记录。
- [QUICKSTART.md](QUICKSTART.md)：常用入口。
- [CHEATSHEET.md](CHEATSHEET.md)：模式和门禁速查。
- [scripts/](scripts)：最小运行脚本和 release validation。
- [tests/](tests)：路由 golden cases。
- [references/forge_controller_protocol.md](references/forge_controller_protocol.md)：Backend Forge 与通用 forge controller 协议的映射。
- [references/architecture_leadership.md](references/architecture_leadership.md)：架构负责人轨道。
- [references/architecture_decision_rules.md](references/architecture_decision_rules.md)：架构决策规则库。
- [references/frontend_to_backend_mental_model.md](references/frontend_to_backend_mental_model.md)：前端到后端心智迁移。
- [references/](references)：厚细节和专项 playbook。
