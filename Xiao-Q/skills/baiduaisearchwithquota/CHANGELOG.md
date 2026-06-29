# 更新日志

## v1.0.3 (2026-04-09)

### 调度优化
- 调度优先级调整为：深度智能搜索 → 高性能版 → 百度搜索
- 新增 smart_search (百度搜索) 作为兜底 API
- 配额安全阈值从 10% 提升到 85%（更安全，避免用到 100% 收费）
- 配额计数器加入 smart_search

### API 端点汇总

| API | 端点 | 配额/天 |
|-----|------|---------|
| 深度智能搜索 | `/v2/ai_search/chat/completions` | 100次 |
| 高性能版 | `/v2/ai_search/web_summary` | 100次 |
| 百度搜索 | `/v2/ai_search/web_search` | 50次 |
| 百度百科详情 | `/v2/baike/lemma/get_content` | 50次 |
| 百度百科搜索 | `/v2/baike/lemma/get_list_by_title` | 50次 |
| 热榜查询 | `/v2/tools/trending_lists/medium` | 8次/天 |

---

## v1.0.2 (2026-04-07)

### 功能优化
- 百度搜索 API 新增参数支持：时间过滤、站点过滤、安全搜索
- 深度智能搜索支持 `enable_reasoning` 推理模式参数
- 所有 API 支持 `resource_types` 资源类型过滤 (image/video/web)
- 添加上下文监控策略，避免 400 错误（会话超过 500KB 提醒）
- 修正请求头格式，统一使用 `X-Appbuilder-Authorization`

### API 端点汇总

| API | 端点 | 配额/天 |
|-----|------|---------|
| 深度智能搜索 | `/v2/ai_search/chat/completions` | 100次 |
| 高性能版 | `/v2/ai_search/web_summary` | 100次 |
| 百度搜索 | `/v2/ai_search/web_search` | 50次 |
| 百度百科详情 | `/v2/baike/lemma/get_content` | 50次 |
| 百度百科搜索 | `/v2/baike/lemma/get_list_by_title` | 50次 |
| 热榜查询 | `/v2/tools/trending_lists/medium` | 8次/天 |

---

## v1.0.1 (2026-04-06)

### 首发版本
- 集成百度 AI 搜索全量 API
- 智能调度器自动选择最优 API