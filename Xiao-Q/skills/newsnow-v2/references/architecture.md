# NewsNow 架构与实现笔记

## 概述

NewsNow 是一个轻量级的新闻聚合服务，通过统一的 API 接口聚合了 60+ 个中文和英文新闻源。本技能封装了 NewsNow 的 Web API，提供 CLI 和 Python API 两种使用方式。

## 系统架构

```
┌─────────────────┐     ┌─────────────────────────────┐
│   Claude Agent  │────▶│     newsnow.py CLI         │
└─────────────────┘     └─────────────────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Fetch Multiple │
                       │  (ThreadPool)    │
                       └──────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
           ┌─────────────────┐   ┌─────────────────┐
           │  fetch_news()   │   │  fetch_news()   │
           │  (HTTP GET)     │   │  (HTTP GET)     │
           └─────────────────┘   └─────────────────┘
                    │                       │
                    └───────────┬───────────┘
                                ▼
                    ┌────────────────────────┐
                    │  NewsNow Aggregator    │
                    │  (newsnow.busiyi.world)│
                    └────────────────────────┘
```

## API 参考

### fetch_news(sid, base_url, timeout)

获取单个新闻源的数据。

**参数:**
- `sid` (str): 新闻源 ID，从 `list_sources()` 获取
- `base_url` (str): NewsNow 服务地址，默认 `https://newsnow.busiyi.world`
- `timeout` (int): 请求超时时间（秒），默认 12

**返回:**
```python
{
  "id": "ithome",
  "status": "fresh",  # 或 "cache"
  "items": [
    {
      "title": "新闻标题",
      "url": "https://...",
      "pubDate": "2025-01-15 10:30",
      "extra": {
        "date": "2025-01-15 10:30",
        "info": "来源标注"
      }
    }
  ]
}
```

### fetch_multiple(sids, limit, concurrent)

并发获取多个新闻源。

**参数:**
- `sids` (List[str]): 新闻源 ID 列表
- `limit` (int): 每个源最多返回条数，默认 30
- `concurrent` (bool): 是否并发请求，默认 True
- `max_workers` (int): 并发线程数，默认 6

### list_sources(include_broken=False)

列出所有可用新闻源。

**返回:**
```python
{
  "ithome": {"name": "IT之家", "type": "科技媒体"},
  "sspai": {"name": "少数派", "type": "科技媒体"},
  ...
}
```

## 可用新闻源分类

| 分类 | 源数 | 示例 |
|------|------|------|
| 科技媒体 | 4 | ithome, sspai, solidot, freebuf |
| 技术社区 | 7 | juejin, v2ex, pcbeta, coolapk, github, hackernews, producthunt |
| 财经媒体 | 8 | wallstreetcn, jin10, mktnews, gelonghui, cls, fastbull... |
| 社交媒体 | 6 | weibo, zhihu, douyin, bilibili, tieba, douban |
| 综合新闻 | 8 | thepaper, ifeng, toutiao, baidu, tencent, sputniknewscn, cankaoxiaoxi, zaobao |
| 其他 | 8 | steam, xueqiu, hupu, nowcoder, iqiyi, qqvideo, chongbuluo, kaopu |

**总计**: 41 个源（其中 6 个已验证不可用）

### 不可用源列表
- `linuxdo` - Linux.do 技术社区
- `kuaishou` - 快手
- `xiaohongshu` - 小红书
- `smzdm` - 什么值得买
- `_36kr` - 36氪
- `ghxi` - 果核剥壳

## 超时与重试策略

- **默认超时**: 12 秒
- **请求延迟**: 0.3 秒（避免触发限流）
- **并发数**: 6 线程
- **错误处理**: 单源失败不影响其他源，返回 error 字段

## 缓存机制

NewsNow 服务端启用约 30 分钟的缓存，响应中包含 `status` 字段：
- `"fresh"` - 新鲜数据
- `"cache"` - 来自缓存

## 依赖要求

- Python 3.8+
- 仅使用标准库：`argparse`, `json`, `urllib`, `concurrent.futures`
- 无需额外安装任何第三方包

## 部署注意事项

1. **网络访问**: 需要能访问 `newsnow.busiyi.world`
2. **时区**: 返回的时间为 UTC+8 北京时间
3. **字符编码**: 所有数据使用 UTF-8，中文无乱码
4. **速率限制**: 建议每源请求间隔 ≥0.3 秒
5. **错误监控**: 建议记录 error 字段并定期检查不可用源的状态

## 扩展新闻源

要添加新的新闻源：

1. 在 `SOURCES` dict 中添加新条目：
```python
"new_source": {"name": "新源名称", "type": "分类"}
```

2. 确保服务端已支持该源（需修改 NewsNow 后端）

3. 更新 `list_src_txt()` 中的分类汇总

4. 更新 SKILL.md 中的新闻源表格

5. 运行 `--test-all` 验证可用性

## 性能指标

- **单源请求**: ~1-2 秒
- **多源并发（6线程）**: ~3-5 秒（6个源）
- **内存占用**: <50MB（标准负载）
- **CPU**: 主要在网络等待

## 常见问题

**Q: 为什么某些源一直不可用？**  
A: 可能是源网站改了结构，需要服务端适配。联系 NewsNow 维护者更新。

**Q: 如何获取更多条数？**  
A: 使用 `--limit` 参数，最大 100 条（服务端可能限制）。

**Q: JSON 输出格式是什么？**  
A: 完整响应结构，包含 `id`, `status`, `items` 数组。

**Q: 如何集成到定时任务？**  
A: 使用 `cron-manager` 技能或系统 cron 定期运行 CLI。

## 版本历史

- **v1.0** - 初始发布，支持 39 个源
- **v1.1** - 更新至 41 个源，修复并发问题
