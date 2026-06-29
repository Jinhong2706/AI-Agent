# Spring Boot Playbook

Spring Boot 是 Backend Forge 的 Java 主线。

## 项目扫描

先看：

- `pom.xml` 或 `build.gradle`。
- Spring Boot 版本。
- 启动类。
- `application.yml` / `application.properties`。
- Controller、Service、Repository 分层。
- Entity、DTO、Mapper。
- 测试目录和测试框架。
- Flyway/Liquibase 目录。

## 默认分层

推荐结构：

- Controller：HTTP 契约、输入校验、状态码。
- DTO/Request/Response：外部 API 模型。
- Service：业务逻辑和事务边界。
- Repository：数据访问。
- Entity：持久化模型。
- Exception handler：统一错误响应。

不要把业务逻辑放进 Controller。

## 数据与迁移

正式新项目默认 PostgreSQL。快速验证可使用 H2。

迁移工具：

- Flyway：简单、直观，适合第一版默认。
- Liquibase：需要更强变更描述或项目已有时使用。

已有项目优先尊重现状。

## 事务

事务边界优先放在 Service 层。

必须关注：

- 多表写入。
- 状态流转。
- 并发更新。
- 外部调用不能随意放进长事务。
- 异步任务不能默认共享请求事务。

## 异常处理

推荐：

- 使用统一 `@ControllerAdvice`。
- 区分 400、401、403、404、409、500。
- 错误响应结构稳定。
- 日志记录排障信息，不泄露敏感数据。

## 测试

常见组合：

- JUnit 5。
- Mockito。
- Spring Boot Test。
- MockMvc 或 WebTestClient。
- Testcontainers，若项目已有或需要真实 PostgreSQL。

最低要求：

- Service 单元测试。
- Controller 接口测试。
- Repository/迁移验证，涉及数据库时。
- 鉴权测试，涉及权限时。

## 常见风险

- DTO 与 Entity 混用导致接口泄露内部字段。
- Controller 过重。
- 事务注解放错层。
- 迁移缺失。
- 只测 happy path。
- N+1 查询。
- 统一异常缺失导致错误语义不稳定。
