# Architecture Decision Rules

架构决策规则库用于 A1-A5 阶段。它的作用不是替用户背书复杂决策，而是把中型项目后端架构负责人最常遇到的选择压成可执行判断。

## 使用原则

- 默认选择更少运行复杂度的方案，直到有明确证据需要升级。
- 每个高风险选择都必须写 ADR：背景、可选方案、选择理由、影响范围、风险、回滚、验证方式。
- 如果团队没有运行、监控、部署和故障处理能力，不得因为“未来扩展”提前引入分布式复杂度。
- 已有项目优先尊重现状；迁移技术栈本身必须单独形成 ADR。

## 模块化单体 vs 微服务

默认：中型项目优先模块化单体或单服务内清晰模块边界。

选择模块化单体，当：

- 团队规模小，后端经验不足，主要由前端工程师承担后端负责人。
- 核心业务边界还在变化。
- 当前最大风险是交付速度、数据一致性、测试闭环和本地可运行。
- 还没有独立部署、独立扩缩容、独立团队所有权的刚性需求。
- 事务需要跨多个业务对象强一致。

考虑少量服务或微服务，当同时满足多数条件：

- 业务边界稳定，能清楚定义 bounded context。
- 不同模块需要独立部署、独立扩缩容或不同技术/数据存储。
- 团队有成熟 CI/CD、日志、追踪、监控、告警和故障响应能力。
- 能接受跨服务调用、网络失败、数据最终一致性和分布式测试成本。
- 每个服务都有明确 owner，不会变成“分布式没人负责”。

禁止把微服务作为默认答案。若只是为了“显得专业”，必须回退到模块化单体。

ADR 必问：

- 哪些模块必须独立部署？
- 哪些数据必须跨边界同步？
- 失败时是否允许最终一致？
- 本地开发、测试、监控和回滚如何处理？
- 如果拆错服务，如何合并或回退？

## PostgreSQL vs MySQL

默认：新中型项目优先 PostgreSQL，已有项目尊重现有数据库。

优先 PostgreSQL，当：

- 需要强关系建模、复杂查询、事务、约束和索引能力。
- 需要关系数据与 JSON/JSONB 混合建模。
- 未来可能需要更复杂的数据完整性、报表查询或扩展能力。
- 团队没有明确 MySQL 运维优势。

优先 MySQL，当：

- 组织已有稳定 MySQL 运维、备份、监控、开发经验。
- 业务以常规 CRUD、读多写少、简单关系模型为主。
- 现有系统、报表、数据同步链路都围绕 MySQL。
- 切换到 PostgreSQL 会带来比收益更高的迁移成本。

禁止事项：

- 因为前端熟悉 JSON 就把所有数据放 JSON 字段。
- 只改 ORM model，不写迁移。
- 未确认历史数据兼容就删除字段、改主键、改唯一约束。

ADR 必问：

- 数据增长量和查询模式是什么？
- 哪些约束必须由数据库保证？
- 哪些字段会被过滤、排序、分页？
- 是否需要 JSON 字段？这些 JSON 字段是否需要查询和索引？
- 备份、恢复、迁移、回滚由谁负责？

## JWT vs Session

默认：浏览器优先、同站 Web 应用优先使用服务端 session + 安全 cookie。

优先 session，当：

- 主要客户端是浏览器。
- 需要可靠登出、强制失效、权限变更后立即生效。
- 可以使用服务端 session 存储或 Redis session。
- 需要降低前端 token 存储风险。

优先 JWT，当：

- 有移动端、第三方 API 客户端、跨服务网关或无共享 session 存储的场景。
- 需要短生命周期 access token + refresh token 流程。
- 可以接受并实现 token 轮换、撤销列表、密钥轮换和泄露响应。
- 团队明确知道 token 放在哪里、怎么过期、怎么吊销。

硬规则：

- 前端不得把“能读 token”当成鉴权依据；后端必须验证每个受保护请求。
- JWT 不自带用户主动撤销能力；需要撤销就必须设计 blocklist、版本号或短过期策略。
- Cookie session 必须考虑 Secure、HttpOnly、SameSite、Path、Domain、过期策略。
- localStorage 存 token 是高风险选择，必须写 ADR 并说明 XSS 风险和替代方案。

ADR 必问：

- 登录态是否必须被服务端主动撤销？
- 权限变化后多久必须生效？
- 客户端是浏览器、移动端、第三方 API，还是混合？
- 前端如何处理 401、403、过期、刷新和登出？
- Token/session 泄露后的响应策略是什么？

## 同步接口 vs 异步任务

默认：用户正在等待结果的交互使用同步接口；不需要立即返回最终结果的流程使用异步任务。

选择同步接口，当：

- 用户必须立刻看到结果。
- 操作很快，失败能直接反馈。
- 调用链短，依赖少。
- 一致性要求高，用户继续操作依赖该结果。

选择异步任务，当：

- 操作耗时长、依赖外部服务或容易超时。
- 需要重试、削峰、批处理、通知、导入导出、发送邮件、生成报表。
- 一个事件需要触发多个后续处理。
- 可以接受“已受理/处理中/成功/失败”的状态机。

硬规则：

- 异步任务必须有任务状态、幂等键、重试策略、失败处理和用户可见反馈。
- 同步接口跨服务调用必须有超时、重试边界、降级和错误语义。
- 不能把异步当成逃避事务和错误处理的手段。

ADR 必问：

- 用户是否需要最终结果才能继续？
- 最大可接受等待时间是多少？
- 失败后用户如何知道和重试？
- 是否需要幂等？
- 任务状态存在哪里？

## Redis 什么时候该上

默认：没有明确性能、会话、限流、队列或实时需求时不上 Redis。

可以使用 Redis，当：

- 热点读明显，数据库压力或延迟成为已验证问题。
- 需要 session 存储、限流、短期验证码、排行榜、轻量队列、pub/sub 或 stream。
- 需要 TTL 控制的临时状态。
- 有明确 cache key、TTL、失效策略和降级策略。

不该使用 Redis，当：

- 只是为了“以后可能快一点”。
- 数据正确性依赖缓存，但没有失效策略。
- 团队无法处理 Redis 不可用、缓存穿透、击穿、雪崩。
- 业务仍能靠数据库索引、分页、查询优化解决。

硬规则：

- 上缓存前必须有基线：慢在哪里、频率多少、目标延迟多少。
- 每个缓存必须定义 key、value、TTL、失效时机、允许脏读时间。
- 必须测试命中、未命中、失效、数据变更和 Redis 不可用。

ADR 必问：

- Redis 是 cache、session store、queue、pub/sub，还是 stream？
- 系统真实数据源是谁？
- Redis 不可用时是失败、降级，还是绕回数据库？
- 如何避免缓存数据越权泄露？
- 如何监控命中率、延迟、内存和淘汰？

## ORM 选择

默认：使用主流框架默认 ORM；不要因为“看起来高级”绕开 ORM，也不要把 ORM 当作不用理解 SQL 的借口。

优先框架默认 ORM，当：

- Spring Boot 项目已有 JPA/Hibernate 生态。
- Django 项目已有 Django ORM。
- FastAPI 项目需要关系建模，可用 SQLAlchemy/SQLModel。
- 业务以常规 CRUD、关系查询、迁移和事务为主。
- 团队需要更快建立数据访问层和测试闭环。

考虑轻量 SQL mapper 或手写 SQL，当：

- 查询高度复杂，涉及窗口函数、CTE、报表、复杂聚合。
- ORM 生成 SQL 不可控，性能问题已被 explain/日志验证。
- 读模型明显不同于写模型。
- 只需要少量简单 SQL，不值得引入完整 ORM。

硬规则：

- ORM entity 不等于 API DTO，不得直接暴露内部字段。
- 使用 ORM 仍必须理解事务、N+1、懒加载、级联、锁和索引。
- 批量写入、复杂查询、报表查询必须允许回退到显式 SQL。
- ORM model 改动必须同步迁移和测试。

ADR 必问：

- 主要查询路径是什么？是否能被 ORM 清楚表达？
- 是否存在 N+1 风险？如何测试和监控？
- 事务边界在哪里？Session/EntityManager 生命周期由谁管理？
- API response 是否使用独立 schema/DTO？
- 何时允许手写 SQL？

## 文件存储

默认：用户上传文件、图片、附件、导出物使用对象存储；数据库只保存元数据和对象 key。

优先对象存储，当：

- 文件大小不可控或数量会增长。
- 需要下载、预览、CDN、生命周期、归档、备份。
- 需要前端直传，后端只签发短期上传凭证。
- 文件不是事务内强一致数据的一部分。

可以存数据库，当：

- 文件很小，数量有限，强事务一致性比扩展性更重要。
- 合规要求必须跟业务记录同库备份和恢复。
- 运维不具备对象存储能力，且规模明确很小。

硬规则：

- 前端直传必须使用短期 signed URL/session URL，不能暴露长期密钥。
- 文件必须有 owner、content type、size、hash、状态、访问权限。
- 上传成功不等于业务绑定成功；必须有“上传中/已上传/已绑定/废弃”的状态。
- 文件访问权限必须由后端签发或代理校验，不能只靠前端隐藏 URL。

ADR 必问：

- 文件最大大小、类型、数量和保存期限？
- 是否需要缩略图、病毒扫描、内容审核、转码？
- 谁可以上传、下载、删除？
- 上传失败、业务提交失败、孤儿文件如何清理？
- URL 过期时间和权限撤销策略是什么？

## 搜索方案

默认：先用数据库查询和索引；搜索需求明确超过数据库能力后再引入搜索引擎。

优先数据库搜索，当：

- 只是精确匹配、前缀匹配、简单过滤、排序、分页。
- 数据量中等，查询可被 B-tree/GIN/GiST/全文索引覆盖。
- 搜索结果必须强一致，不能接受同步延迟。
- 团队不具备维护独立搜索集群能力。

优先 PostgreSQL full text search，当：

- 已使用 PostgreSQL。
- 需要基础全文搜索、排名、highlight、词典配置。
- 搜索数据主要来自业务库，规模和功能需求可控。

考虑 Meilisearch/OpenSearch/Elasticsearch，当：

- 需要 typo tolerance、复杂相关性、分面、聚合、多字段权重、日志搜索、向量/语义搜索。
- 搜索流量和写入流量需要独立扩展。
- 可以接受索引最终一致和重建索引成本。
- 有同步管道、重试、回放和索引版本管理。

硬规则：

- 搜索索引不是事实来源，除非 ADR 明确设计为专用存储。
- 每个搜索索引必须定义数据来源、同步方式、重建方式、延迟窗口。
- 搜索结果必须二次校验权限，不能把无权数据泄露给前端。

ADR 必问：

- 搜索是精确过滤、全文搜索、推荐、日志分析还是向量检索？
- 用户能接受多长索引延迟？
- 数据删除或权限变更后搜索结果多久必须消失？
- 如何全量重建索引？重建期间服务如何可用？
- 搜索失败时是否降级到数据库查询？

## 后台任务

默认：短任务用框架内后台能力；需要可靠重试、状态、调度或分布式执行时使用任务队列/批处理框架。

选择框架内后台任务，当：

- 任务很短、失败影响小、无需持久化状态。
- 只用于非关键通知或轻量请求后处理。
- 单实例部署，重启丢任务可接受。

选择 Celery、Spring Batch、队列 worker 或调度框架，当：

- 任务耗时长、可重试、需要状态、需要定时或批处理。
- 任务失败必须可见、可恢复、可补偿。
- 多实例部署，任务不能因进程重启丢失。
- 需要限速、并发控制、死信、延迟执行。

硬规则：

- 后台任务必须有任务 ID、状态、幂等键、重试策略和失败处理。
- 任务 payload 不应携带大对象或敏感明文；只传引用和必要参数。
- 任务执行必须记录日志和关键指标。
- 重试必须区分可重试错误和永久失败。

ADR 必问：

- 任务是否允许丢失？
- 任务是否可重复执行？幂等键是什么？
- 最大重试次数、退避策略、死信处理是什么？
- 用户如何看到任务状态？
- 任务和主事务的提交顺序如何保证？

## API Gateway

默认：中型单服务或少量服务不默认引入 API Gateway；先用应用自身路由、反向代理或云负载均衡。

考虑 API Gateway，当：

- 需要统一认证、限流、配额、请求/响应转换、API key、开发者门户。
- 多个后端服务需要统一入口。
- 需要 WebSocket/API 管理、OpenAPI 导入、监控和策略治理。
- 组织已经有标准 API 管理平台。

不该引入 API Gateway，当：

- 只有一个后端服务，应用自身已能处理认证和路由。
- 只是为了解决 CORS 或路径转发。
- 团队无法承担网关策略、版本、部署和排障复杂度。

硬规则：

- Gateway 不能替代服务内授权；后端仍必须验证身份、权限和资源归属。
- Gateway 策略必须版本化，并纳入环境差异和回滚计划。
- 网关日志、指标、追踪必须能关联到后端请求 ID。

ADR 必问：

- 网关解决的是认证、限流、聚合、转换、治理，还是入口统一？
- 失败时是网关问题还是后端问题，如何定位？
- 是否需要开发者门户或 API key？
- 本地开发和测试环境如何模拟网关？
- 网关引入后如何避免把业务逻辑塞进策略？

## Observability

默认：中型项目最低要有结构化日志、基础指标、健康检查和错误追踪；分布式链路增加后再引入 tracing。

最低要求：

- 每个请求有 request id 或 trace id。
- 记录关键业务事件、错误、慢查询和外部依赖调用。
- 暴露健康检查和基础指标。
- Dashboard 至少覆盖流量、延迟、错误、资源饱和度。
- Alert 只针对需要人处理的用户影响或风险，不为噪声报警。

引入 OpenTelemetry，当：

- 有多个服务、队列、异步任务或复杂外部依赖。
- 需要统一 traces、metrics、logs 的上下文。
- 需要供应商中立的采集和导出。

硬规则：

- 日志不能泄露 token、密码、身份证、银行卡、隐私字段。
- Error log 必须包含定位信息，但不能把内部栈直接返回给前端。
- 指标必须有 owner 和动作建议；没有响应动作的报警应删除或降级为 dashboard。

ADR 必问：

- 用户怎么知道系统坏了？
- 研发怎么定位一次失败请求？
- 四个黄金信号是否有 dashboard？
- 哪些错误需要报警，哪些只记录？
- 日志、指标、trace 保存多久，谁能访问？

## CI/CD

默认：每个中型后端项目至少要有 CI；CD 根据部署成熟度逐步引入。

最低 CI：

- 每个 PR 运行格式/静态检查、单元测试、关键集成测试。
- 生成测试报告或至少输出清晰失败日志。
- 数据库迁移检查或迁移 dry run，若涉及 schema。
- 构建可运行 artifact 或镜像。

考虑 CD，当：

- 主干保持可发布。
- 有自动化测试、回滚策略、环境配置和密钥管理。
- 部署步骤可重复，失败可停止或回滚。
- 有 staging/preview 环境验证。

硬规则：

- CI 不得依赖开发者本机状态。
- 密钥必须使用 CI secret store，不能写入仓库。
- 部署前必须区分环境配置，不能把测试配置推到生产。
- 数据迁移和应用发布必须定义顺序和回滚方案。

ADR 必问：

- 哪些检查阻塞合并？
- 哪些检查只提示风险？
- 失败日志是否足够让前端负责人定位？
- 部署是否需要人工批准？
- 回滚是代码回滚、配置回滚、数据库回滚，还是补偿迁移？

## 测试金字塔

默认：多写快速、稳定、低层测试；少写昂贵、脆弱、全链路测试。

推荐结构：

- 单元测试：覆盖纯业务逻辑、校验、状态流转、权限规则。
- 集成测试：覆盖数据库、ORM、迁移、外部依赖适配器。
- 契约/API 测试：覆盖 OpenAPI 契约、status code、错误响应。
- E2E 测试：只覆盖少量关键用户路径。
- 探索测试：用于体验、可用性、异常组合，不替代自动化。

硬规则：

- Bug 修复优先补复现测试。
- 数据迁移必须有迁移验证和关键查询验证。
- 鉴权必须测未登录、权限不足、越权、正常授权。
- 不要用大量 E2E 测试弥补单元/集成测试缺失。
- 测试失败不得宣称完成。

ADR 必问：

- 当前风险应该在哪一层测试最便宜地发现？
- 哪些测试必须进 PR 阻塞？
- 哪些测试可以 nightly 或手动运行？
- 测试数据如何构造和清理？
- 外部服务如何 mock、fake 或用 testcontainer 替代？

## Sources

- Martin Fowler, Microservice Trade-Offs: https://martinfowler.com/articles/microservice-trade-offs.html
- AWS, Monolithic vs Microservices: https://aws.amazon.com/compare/the-difference-between-monolithic-and-microservices-architecture/
- AWS Prescriptive Guidance, Decomposing monoliths into microservices: https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-decomposing-monoliths/welcome.html
- Microsoft Learn, Interservice communication in microservices: https://learn.microsoft.com/en-us/azure/architecture/microservices/design/interservice-communication
- PostgreSQL JSON Types: https://www.postgresql.org/docs/current/datatype-json.html
- MySQL JSON Data Type: https://dev.mysql.com/doc/refman/en/json.html
- OWASP Session Management Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- OWASP JSON Web Token Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html
- Redis Use Cases: https://redis.io/docs/latest/develop/use-cases/
- Hibernate ORM Documentation: https://hibernate.org/orm/documentation/
- SQLAlchemy ORM Documentation: https://docs.sqlalchemy.org/en/20/orm/
- Django QuerySet API Reference: https://docs.djangoproject.com/en/stable/ref/models/querysets/
- AWS S3 Documentation: https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html
- Google Cloud Storage Signed URLs: https://cloud.google.com/storage/docs/access-control/signed-urls
- PostgreSQL Full Text Search: https://www.postgresql.org/docs/current/textsearch.html
- OpenSearch Getting Started: https://docs.opensearch.org/docs/getting-started/
- Meilisearch Search API: https://www.meilisearch.com/docs/reference/api/search
- Spring Batch Reference: https://docs.spring.io/spring-batch/reference/
- Celery Documentation: https://docs.celeryq.dev/
- AWS API Gateway Documentation: https://docs.aws.amazon.com/apigateway/
- Azure API Management Gateway: https://learn.microsoft.com/en-us/azure/api-management/api-management-gateways-overview
- OpenTelemetry Documentation: https://opentelemetry.io/docs/
- Google SRE, Monitoring Distributed Systems: https://sre.google/sre-book/monitoring-distributed-systems/
- GitHub Actions Documentation: https://docs.github.com/en/actions
- GitLab CI/CD Documentation: https://docs.gitlab.com/ee/ci/
- Martin Fowler, Continuous Integration: https://martinfowler.com/articles/continuousIntegration.html
- Martin Fowler, Test Pyramid: https://martinfowler.com/bliki/TestPyramid.html
- Martin Fowler, Practical Test Pyramid: https://martinfowler.com/articles/practical-test-pyramid.html
- Google Testing Blog, Just Say No to More End-to-End Tests: https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html
