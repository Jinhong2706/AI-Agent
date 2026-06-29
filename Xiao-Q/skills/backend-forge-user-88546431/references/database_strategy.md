# Database Strategy

数据库是后端闭环的核心。Backend Forge 默认尊重已有项目，不擅自替换数据库、ORM 或迁移工具。

## 默认策略

| 场景 | 默认 |
|---|---|
| Spring Boot 快速验证 | H2 |
| Spring Boot 正式新项目 | PostgreSQL + Flyway/Liquibase |
| FastAPI 快速验证 | SQLite |
| FastAPI 正式新项目 | PostgreSQL + Alembic |
| Django | Django migrations，尊重现有数据库 |
| 已有项目 | 尊重现状 |

## 迁移规则

涉及表结构变化时必须确认：

- 新增/删除/修改字段。
- 默认值。
- 是否允许空值。
- 唯一约束。
- 外键约束。
- 索引。
- 兼容旧数据的方式。
- 回滚或修复策略。

## 事务规则

必须识别：

- 一次请求内的多表写入。
- 状态流转。
- 库存、余额、名额等竞争资源。
- 幂等请求。
- 异步任务与主事务边界。

Spring Boot 优先使用 service 层事务边界。FastAPI 需要明确 session 生命周期和 commit/rollback 位置。

## 查询规则

慢查询或列表 API 必须关注：

- 分页。
- 排序。
- 过滤条件。
- N+1 查询。
- 索引。
- 返回字段是否过大。

## 禁止事项

- 未确认就删除字段或表。
- 未确认就改变主键策略。
- 未确认就改变数据库类型。
- 只改 ORM 不做迁移。
- 只做迁移不更新测试。
