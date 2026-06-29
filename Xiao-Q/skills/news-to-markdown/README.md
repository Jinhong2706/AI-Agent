# news-to-markdown Skill

> 输入文章 URL，输出干净的 Markdown 正文 — 17 个平台专项优化，专为 AI Agent 设计

## 快速开始

```bash
# 基本转换
npx --yes news-to-markdown@^3.3.1 --url "https://www.toutiao.com/article/123"

# 保存到文件
npx --yes news-to-markdown@^3.3.1 --url "https://mp.weixin.qq.com/s/xxx" --output article.md

# 下载图片到本地（生成离线包）
npx --yes news-to-markdown@^3.3.1 --url "https://36kr.com/p/xxx" \
  --download-images --output-dir ./article

# 与 browser-web-search 配合：搜索 → 提取正文
bws site toutiao/search "ai agent" --count 3
npx --yes news-to-markdown@^3.3.1 --url "https://www.toutiao.com/article/111"
```

## 专项优化平台（17 个）

| 平台 | 域名 |
|-----|------|
| **今日头条** | toutiao.com |
| **微信公众号** | mp.weixin.qq.com |
| **小红书** | xiaohongshu.com |
| **知乎** | zhihu.com |
| **36kr** | 36kr.com |
| **虎嗅** | huxiu.com |
| **华尔街见闻** | wallstreetcn.com |
| **澎湃新闻** | thepaper.cn |
| **InfoQ** | infoq.cn / infoq.com |
| **Bilibili 专栏** | bilibili.com |
| **掘金** | juejin.cn |
| **CSDN** | csdn.net |
| **博客园** | cnblogs.com |
| **简书** | jianshu.com |
| **SegmentFault** | segmentfault.com |
| **开源中国** | oschina.net |
| **人人都是产品经理** | woshipm.com |

其余平台走通用算法（Mozilla Readability），大多数文章均可正常提取。

## 参数速查

| 参数 | 说明 |
|-----|------|
| `--url` | 文章 URL（必填） |
| `--output` | 输出文件路径 |
| `--download-images` | 下载图片到本地 |
| `--output-dir` | 图片输出目录 |
| `--no-metadata` | 只要正文，不含标题/作者/时间 |
| `--selector` | 自定义内容区域 CSS 选择器 |
| `--noise` | 移除指定元素（逗号分隔） |
| `--verbose` | 详细日志 |

## 环境要求

- Node.js >= 18.0.0
- 可选：`npx playwright install chromium`（动态页面支持）

## 文档

详细使用说明：[SKILL.md](./SKILL.md)

## 链接

- [news-to-markdown GitHub](https://github.com/sipingme/news-to-markdown)
- [npm 包](https://www.npmjs.com/package/news-to-markdown)

## License

MIT
