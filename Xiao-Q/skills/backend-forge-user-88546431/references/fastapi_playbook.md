# FastAPI Playbook

FastAPI 是 Backend Forge 的 Python 主线。

## 项目扫描

先看：

- `pyproject.toml`、`requirements.txt`、`Pipfile`。
- app 入口。
- router 组织。
- Pydantic schema。
- SQLAlchemy/SQLModel model。
- database session 管理。
- Alembic 目录。
- 测试目录和 pytest 配置。

## 默认分层

推荐结构：

- routers：HTTP 契约。
- schemas：Pydantic request/response。
- services：业务逻辑。
- repositories/crud：数据访问。
- models：ORM model。
- core/config：配置。
- db/session：数据库会话。
- exceptions：错误处理。

不要把数据库写入和复杂业务都塞进 router。

## 数据与迁移

正式新项目默认 PostgreSQL + Alembic。快速验证可使用 SQLite。

必须明确：

- SQLAlchemy 还是 SQLModel。
- session 生命周期。
- commit/rollback 边界。
- migration 是否同步。

## 依赖注入

FastAPI dependency 用于：

- 数据库 session。
- 当前用户。
- 权限检查。
- 配置和外部客户端。

避免在全局初始化中隐藏难以测试的状态。

## 异常处理

推荐：

- 明确 HTTPException 状态码。
- 对业务错误定义稳定结构。
- 不向客户端泄露内部 traceback。
- 日志记录请求关键信息。

## 测试

常见组合：

- pytest。
- TestClient 或 httpx AsyncClient。
- pytest fixtures。
- 临时 SQLite 或测试 PostgreSQL。

最低要求：

- service 测试。
- router 接口测试。
- 数据库持久化验证。
- Alembic 迁移验证，涉及结构变化时。
- 鉴权测试，涉及权限时。

## 常见风险

- Pydantic schema 与 ORM model 混用。
- session 泄漏或 commit 位置混乱。
- router 过重。
- Alembic migration 缺失。
- async/sync 混用不清。
- 测试依赖真实外部服务。
