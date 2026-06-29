# Frontend To Backend Mental Model

这个指南用于帮助有经验的前端工程师把已有心智迁移到中型后端架构负责人角色。不要把前端体验直接等同于后端真实状态；前端看到的是投影，后端负责事实、边界和验证。

## 总原则

- 前端状态是视图状态或缓存；后端状态是业务事实。
- 前端路由是页面组织；后端资源是权限、数据所有权和事务边界。
- 前端表单校验是体验优化；后端校验是安全和数据完整性边界。
- 前端权限展示是提示；后端授权检查是唯一可信执行点。
- 前端错误提示是用户语言；后端错误语义必须稳定、可测试、可追踪。

## 页面状态 -> 数据模型

前端熟悉：

- 页面 state。
- store。
- URL query。
- table/list/detail/form。
- loading/empty/error/success。

后端映射：

- 哪些状态需要持久化，变成 table/entity。
- 哪些只是 UI 临时态，不进数据库。
- 哪些状态是可推导的，不要重复存储。
- 哪些状态变化必须记录历史或审计。
- 列表页的筛选、排序、分页决定索引和查询策略。

负责人必须问：

- 这个字段是用户输入、系统生成，还是计算结果？
- 刷新页面后它是否必须存在？
- 它是否需要被其他用户、其他设备或后台任务看到？
- 它是否参与权限、计费、库存、余额、状态流转？

## UI 操作 -> 命令、事务和幂等

前端熟悉：

- 点击按钮。
- 提交表单。
- 乐观更新。
- 防重复点击。
- toast 成功/失败。

后端映射：

- 每个写操作是一个 command。
- command 必须有输入校验、权限检查、事务边界和错误语义。
- 会重复提交的操作必须设计幂等。
- 乐观 UI 必须知道回滚条件。
- 多表写入必须定义全部成功或如何补偿。

负责人必须问：

- 用户重复点击会发生什么？
- 网络超时后前端重试会不会重复扣款、重复创建、重复发货？
- 这个操作是否改变多个实体？
- 失败时哪些数据已经写入？如何回滚或补偿？

## API 契约 -> OpenAPI 和测试契约

前端熟悉：

- request/response type。
- mock 数据。
- loading/error 分支。
- 前后端联调。

后端映射：

- API contract 应写清 path、method、query、body、response、status code。
- OpenAPI 可以作为机器可读接口描述，服务端、客户端、文档和测试都能围绕它协作。
- 每个接口必须定义正常路径和关键错误路径。
- response schema 是长期兼容承诺，不能随意改字段含义。

负责人必须问：

- 这个接口是查询、创建、修改、删除，还是业务动作？
- GET 是否只读？POST/PUT/PATCH/DELETE 是否有正确语义？
- 201、204、400、401、403、404、409、422、500 如何使用？
- 前端需要哪些字段？哪些字段不能暴露？

## 权限展示 -> 后端授权模型

前端熟悉：

- 按角色隐藏按钮。
- 菜单权限。
- 路由守卫。
- 禁用操作入口。

后端映射：

- 隐藏按钮不是安全边界。
- 每个受保护 API 都必须验证身份和授权。
- 授权不仅是角色，还包括资源归属、组织边界、字段级访问。
- 401 是未认证，403 是已认证但无权限，必要时可用 404 隐藏资源存在。

负责人必须问：

- 谁能访问这个资源？
- 用户是否只能访问自己或所属组织的数据？
- 管理员权限是否有范围？
- 列表查询是否过滤了无权资源？
- 导出、批量操作、后台任务是否复用了同一授权规则？

## 错误处理 -> 稳定错误语义

前端熟悉：

- toast。
- inline error。
- retry。
- error boundary。

后端映射：

- 错误要能被前端稳定识别，而不是解析自然语言。
- 业务冲突用稳定 code，例如 `ORDER_ALREADY_CANCELLED`。
- 输入错误要定位到字段。
- 服务端错误要记录日志和 trace id，不能泄露内部栈。

负责人必须问：

- 前端如何区分可重试、需登录、无权限、资源不存在、业务冲突？
- 是否需要错误码字典？
- 日志里能否定位用户、请求、资源和失败原因？
- 错误响应是否会泄露敏感信息？

## 前端缓存 -> 后端缓存和一致性

前端熟悉：

- React Query/SWR cache。
- stale time。
- invalidate query。
- optimistic update。

后端映射：

- 前端缓存是体验优化；后端缓存影响系统正确性和数据新鲜度。
- 后端缓存必须定义 key、TTL、失效策略、允许脏读时间。
- 权限相关数据缓存必须防止越权泄露。
- 缓存不是数据库，数据库仍是事实来源，除非 ADR 明确改成事件源或专用存储。

负责人必须问：

- 用户能接受多久的旧数据？
- 数据变更后谁负责 invalidation？
- 缓存 key 是否包含租户、用户、权限范围？
- 缓存未命中或 Redis 不可用时怎么办？

## 前端路由 -> 资源边界

前端熟悉：

- `/projects/:id/tasks`。
- tabs。
- nested routes。
- route guards。

后端映射：

- URL 参数通常是资源身份。
- 资源身份必须绑定所有权和授权检查。
- 嵌套路由暗示父子关系，但数据库可能是一对多、多对多或聚合根。
- route guard 不能替代 API 鉴权。

负责人必须问：

- `projectId` 是否必须属于当前用户或组织？
- 子资源是否必须属于父资源？
- 删除父资源时子资源如何处理？
- URL 暴露的 ID 是否可枚举？是否需要防越权测试？

## 表单校验 -> 后端校验和约束

前端熟悉：

- required。
- min/max。
- regex。
- disabled submit。

后端映射：

- 所有前端校验后端都必须重新执行。
- 唯一性、外键、金额、库存、状态流转必须由后端和数据库约束兜底。
- 前端格式校验不能防止恶意请求。

负责人必须问：

- 哪些约束必须写入数据库？
- 哪些错误返回字段级信息？
- 并发提交时唯一性和库存如何保证？
- 数据迁移后历史数据是否满足新约束？

## Sources

- React, Sharing State Between Components: https://react.dev/learn/sharing-state-between-components
- React, State as a Snapshot: https://react.dev/learn/state-as-a-snapshot
- OpenAPI, Introduction: https://learn.openapis.org/introduction.html
- OpenAPI, Structure of an OpenAPI Description: https://learn.openapis.org/specification/structure.html
- MDN, HTTP request methods: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods
- MDN, HTTP response status codes: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status
- OWASP Authorization Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- OWASP Session Management Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
