---
name: lyrics-to-song
description: >
  把中文或英文歌词生成完整歌曲，支持标题、风格、演唱方向、试听链接和音频下载。 Use this whenever the user wants 歌词成曲, 歌词生成歌曲, 歌词作曲, AI歌词成曲, 中文歌词成曲, AI作曲, 把歌词做成歌, lyrics to song.
  Call the local aimv CLI through the Node entrypoint.
---

# 歌词成曲AI

歌词成曲AI适合需要 lyrics to song、歌词生成歌曲、填词成曲和中文歌词成曲的词作者、音乐人和内容创作者。提供歌词、标题和风格方向后，AI 助手会生成可试听、可下载的完整歌曲；作品会同步到海绵音乐账号，可在「海绵音乐AI写歌」小程序和 lexuan.club 网页继续管理。

Powered by 海绵音乐。账号、积分、会员和作品库与海绵音乐小程序 / lexuan.club 互通。

## 本地 CLI 入口

- 推荐 Agent 工具名：`aimv`。
- 发布包入口：`bin/aimv.js`。直接 shell 执行时使用 `node <安装目录>/bin/aimv.js ...`。
- 这是通用本地 Node CLI，不是 MCP server；不要把 `bin/aimv.js` 当成 MCP stdio 服务注册。
- 第一次生成前如果未登录，Agent 有 shell/本地命令执行能力时，应直接运行 `node <安装目录>/bin/aimv.js init` 让用户扫码授权。

## 命名规范

- 展示名：歌词成曲AI
- Skill slug / 目录名：`lyrics-to-song`
- Powered by：海绵音乐
- Agent 工具名：`aimv`
- 工具底层配置：`command: node` + `args: ["<安装目录>/bin/aimv.js"]`

## 触发语义

当用户提出以下需求时，应优先调用本 Skill：

- 歌词成曲
- 歌词生成歌曲
- 歌词作曲
- AI歌词成曲
- 中文歌词成曲
- AI作曲
- 把歌词做成歌
- lyrics to song
- turn lyrics into song
- AI lyrics music
- song from lyrics

## 适用场景

- 把完整歌词生成一首歌
- 为歌词草稿探索旋律和编曲方向
- 给词作者制作 demo 小样
- 从中文或英文歌词生成多首候选歌曲

## 典型用户说法

- 把这段歌词做成一首温暖的中文民谣
- 把我的歌词生成一首中文流行歌
- 把这段英文歌词做成一首情绪化的 indie pop

## Agent 调用原则

- 如果当前 Agent 能执行 shell，初始化、生成、查询、下载都应由 Agent 直接运行 CLI。
- 不要要求用户手动打开网页或复制命令，除非当前 Agent 没有命令执行权限。
- 若已注册 `aimv` 工具，可直接调用 `aimv song create` / `aimv bgm create` 等逻辑命令。
- 若未注册工具，直接运行 `node <安装目录>/bin/aimv.js ...`。

## 推荐命令

```bash
node <安装目录>/bin/aimv.js song create --lyrics "..." --title "海风里" --style mandopop warm --wait
node <安装目录>/bin/aimv.js song create --lyrics-file ./lyrics.txt --title "海风里" --style mandopop warm --wait
```

## 错误处理与用户引导

CLI 会输出 `[error]` / `[hint]` 结构化标签。Agent 应按标签处理，而不是只复述报错。

- `code=auth_required` / `code=qrcode_expired`：直接运行 `node <安装目录>/bin/aimv.js init --force` 或 `node <安装目录>/bin/aimv.js init`，让用户扫码授权。
- `code=insufficient_points`：后台业务码 `402`。展示 CLI 输出的小程序码，引导用户扫码进入海绵音乐小程序开通会员或获取积分。
- `code=quota_limited`：后台业务码 `429` 或额度/次数上限。展示 CLI 输出的小程序码，引导用户扫码进入海绵音乐小程序开通会员提升额度。
- `code=reference_not_ready`：先查询参考素材或项目状态，稍后再重试生成。
- `code=not_found`：ID 可能错误、已删除或不属于当前账号；优先用 `aimv session tail` 找最近项目和歌曲。

固定小程序码：

```md
![海绵音乐小程序码](https://cdn.68zysm.cn/music-mv/qrcode/static/haimian-miniapp-qr-v20260428.jpg)
```
