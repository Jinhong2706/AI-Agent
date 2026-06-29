#!/usr/bin/env node

/**
 * browser-web-search-skill postinstall / help script
 * 显示安装后的使用说明
 */

const REQUIRED_VERSION = '0.4.3';

console.log(`
╔══════════════════════════════════════════════════════════════════╗
║           Browser Web Search Skill 安装完成                       ║
╚══════════════════════════════════════════════════════════════════╝

把任何网站变成命令行 API，专为 OpenClaw 设计，复用浏览器登录态。

📦 内置平台 (17 平台，37 命令):
   知乎、小红书、B站、今日头条、36kr、澎湃、腾讯、网易、
   新浪、微博、微信公众号、百度、Bing、Google、CSDN、博客园、BOSS直聘

� 安装:
   npm install -g browser-web-search@${REQUIRED_VERSION}

🚀 快速开始:

   # 查看所有可用命令
   bws site list

   # 运行 adapter
   bws zhihu/hot
   bws xiaohongshu/search "旅行"
   bws bilibili/popular

   # JSON 输出 + jq 过滤
   bws zhihu/hot --json
   bws zhihu/hot --jq '.[].title'

⚠️  前提条件:
   - Node.js >= 18.0.0
   - OpenClaw 环境（openclaw 命令可用）
   - 如需登录态，请先在 OpenClaw 浏览器中登录目标网站

🔐 登录态管理:
   如果命令返回 401/403 错误，请在 OpenClaw 浏览器中登录：
   openclaw browser open https://xiaohongshu.com

📖 详细文档: 查看 SKILL.md

⚡ 安全提示:
   browser-web-search 会在浏览器页面上下文中执行 JavaScript，可访问站点认证数据。
   使用前请审计源码: https://github.com/sipingme/browser-web-search
`);
