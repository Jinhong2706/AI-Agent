# Authentication And Authorization

认证鉴权是按需核心能力，不是所有新项目默认必选项。

## 触发条件

必须进入认证鉴权设计的情况：

- 用户、账号、登录、注册。
- 角色、权限、后台管理。
- 用户数据隔离。
- 资源归属校验。
- 越权访问风险。
- Token、session、API key。

## 默认方案

Spring Boot：

- Spring Security。
- JWT 或 session 按项目需求选择。
- 方法级或路由级权限尊重现有项目风格。

FastAPI：

- FastAPI security dependencies。
- OAuth2 password bearer / JWT 或 session。
- 使用 dependency 注入当前用户和权限检查。

Django：

- Django auth。
- DRF permissions / authentication classes。
- 尊重现有 middleware 和 permission 结构。

## 必须确认

- 谁可以访问。
- 访问什么资源。
- 资源归属规则。
- 角色和权限粒度。
- 失败时返回 401 还是 403。
- 是否需要审计日志。

## 测试闭环

最低测试：

- 未登录。
- 权限不足。
- 越权访问。
- 正常授权。

可选测试：

- Token 过期。
- Token 伪造。
- 用户禁用。
- 角色变更后权限刷新。

## 架构会签

以下属于架构会签或平台级边界：

- 企业级 IAM。
- SSO 平台。
- OAuth provider。
- 平台级多租户权限模型。
- 跨系统统一权限治理。
