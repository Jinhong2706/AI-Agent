# Changelog

All notable changes to wechat-mp-suite are documented here.

---

## [1.0.1] - 2026-04-07

### Added
- **模块二（下载器）**：新增 `scripts/downloader/download.js`，基于 Puppeteer，支持懒加载图片、视频链接嗅探、完整 DOM 渲染，适合需要完整文章内容的场景
- **远程 MCP 发布**：新增 `scripts/publisher/publish-remote.sh`，通过远程 wenyan-mcp 服务中转发布，解决家庭宽带 IP 白名单问题
- **含视频文章发布**：新增 `scripts/publisher/publish_with_video.js`，支持上传视频封面并发布图文+视频组合内容
- **财经夜报写作风格**：模块三新增财经老韭菜视角写作风格

### Changed
- 模块一览从「七大模块」扩展为「八大模块」，补全下载器模块说明
- SKILL.md 结构优化，新增 Quick Start 触发词示例表
- 排版模块新增外部服务依赖声明
- 所有工作流示例路径统一为 `{baseDir}` 占位符

### Fixed
- 修正工作流示例中使用相对路径的问题

---

## [1.0.0] - 2026-04-06

### Added
- 初始版本，包含七大模块：搜索、爬虫、写作（刘润/爆款/真人）、洗稿、AI配图、排版、发布
- `scripts/search/search_wechat.js`：搜狗微信搜索，支持批量抓取正文
- `scripts/spider/`：Python 实现，轻量级文章爬取
- `scripts/typeset/`：Markdown → 微信富文本排版，双版本预览
- `scripts/publisher/publish.js`：本地 wenyan-cli 发布
