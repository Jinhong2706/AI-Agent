# 百度AI搜索 (BaiduAISearch)

百度 AI 搜索技能 for OpenClaw

## 简介

百度 AI 搜索是一个集成百度 AI 搜索能力的 OpenClaw 技能，提供：
- 智能搜索（自动选择最优 API）
- 百科查询
- 热榜获取

## 功能特性

| 功能 | 说明 |
|------|------|
| 深度智能搜索 | AI 总结 + 引用，100次/天 |
| 高性能搜索 | 快速 AI 总结，100次/天 |
| 百科查询 | 词条详情/搜索，50次/天 |
| 热榜获取 | 微博/知乎/抖音/B站等，8次/天 |

## 快速开始

### 1. 安装

```bash
# 方式一：克隆仓库
git clone https://github.com/Stan-Xia/baidu-ai-search.git

# 方式二：下载 ZIP
# 从 https://github.com/Stan-Xia/baidu-ai-search/raw/main/baidu-ai-search.zip 下载
```

### 2. 配置凭证

**必需：百度 API Key**

1. 访问 https://console.bce.baidu.com/qianfan/
2. 创建应用，获取 API Key
3. 设置环境变量：

```bash
export BAIDU_API_KEY="你的API Key"
```

### 3. 使用

```bash
# 智能搜索
python3 scripts/smart_search.py '搜索内容'

# 查询热榜
python3 scripts/trending.py weibo
python3 scripts/trending.py bilibili
```

## 注意事项

1. **凭证安全**：API Key 不要泄露给他人
2. **网络**：需要能访问百度 API
3. **⚠️ 免费额度监控（必读）**
   - 百度计算调用次数的方式与实际可能有较大出入
   - 请以千帆后台实际用量为准：https://console.bce.baidu.com/qianfan/studio/resource
   - 建议实时监控千帆控制台的用量统计，避免额度用完导致服务中断
   - 免费额度宝贵，**不要随意测试**，仅在实际需要时调用

4. **💰 后付费政策**
   - 免费额度用完后将自动转为后付费模式
   - 超额使用会产生欠费，请及时关注账户余额

## 技术支持

- GitHub: https://github.com/Stan-Xia/baidu-ai-search
- 问题反馈: Issues

## 更新日志

### v1.0.3 (2026-04-09)
- 调度优先级：深度智能搜索 → 高性能版 → 百度搜索
- 新增 smart_search 兜底 API
- 配额安全阈值 85%

### v1.0.2 (2026-04-07)
- 优化百度搜索 API 参数：支持时间过滤、站点过滤、安全搜索
- 修正请求头格式

### v1.0.1
- 添加使用方法与注意事项
- 优化文档结构

### v1.0.0
- 初始版本
- 支持智能搜索、百科查询、热榜获取