# 歌词成曲AI 安装说明

版本：1.2.13
Skill slug：lyrics-to-song
默认环境：production
默认 Base URL：https://music.68zysm.cn/api/v3
默认网页入口：https://lexuan.club
最低 Node 版本：>=18

## 你下载到的是什么

这是一个已经打好的 歌词成曲AI Node CLI 发布包，里面已经包含运行所需代码。
对 Agent 注册的工具名仍然是 `aimv`；底层执行方式是 `node ./bin/aimv.js ...`。
最终用户解压后不需要再执行 `pnpm install` 或 `pnpm build`。
发布包不包含无扩展名 Unix 可执行文件，也不包含平台专属二进制。

Powered by 海绵音乐。账号、积分、会员和作品库与海绵音乐小程序 / lexuan.club 互通。

## 安装与初始化

### macOS / Linux / Windows

```bash
node ./bin/aimv.js init
```

如果你不想交互输入，也可以改为：

```bash
node ./bin/aimv.js config set-api-key --stdin
```

## Agent 适配模型

歌词成曲AI 的通用核心是 `SKILL.md` + 本地 Node CLI。不同 Agent 需要适配的是“如何发现说明”和“如何执行本地命令”，不是音乐生成逻辑。

通用要求：

- 让 Agent 读到本目录的 `SKILL.md`
- 让 Agent 能执行本目录的 `bin/aimv.js`，命令为 `node`
- 触发语义：歌词成曲、歌词生成歌曲、歌词作曲、AI歌词成曲、中文歌词成曲、AI作曲、把歌词做成歌、lyrics to song
- 如果 Agent 有 shell/本地命令执行能力，初始化、生成、查询、下载都应由 Agent 直接运行 CLI；不要先让用户复制命令到终端
- 首次未登录时，Agent 应直接运行 `node ./bin/aimv.js init` 或 `node ./bin/aimv.js init --force`，用户只需要扫码授权

命名规范：

- 包展示名：歌词成曲AI
- Powered by：海绵音乐
- Skill slug / 目录名：`lyrics-to-song`
- CLI 命令名：`aimv`
- Agent 工具名：优先 `aimv`；工具底层 command 配置为 `node` + `./bin/aimv.js`
- LLM 触发时可识别“海绵音乐”“写歌”“生成音乐”“BGM”等语义；执行时统一调用 `aimv`

## 适用场景

- 把完整歌词生成一首歌
- 为歌词草稿探索旋律和编曲方向
- 给词作者制作 demo 小样
- 从中文或英文歌词生成多首候选歌曲

## 典型用户说法

- 把这段歌词做成一首温暖的中文民谣
- 把我的歌词生成一首中文流行歌
- 把这段英文歌词做成一首情绪化的 indie pop

### Codex

发布包内的 `SKILL.md` 已经是 Codex 原生 Skill 格式。复制到 Codex 本地 skills 目录后，重启 Codex 即可自动识别 歌词成曲AI。执行命令时使用 `node <安装目录>/bin/aimv.js`。

macOS / Linux:

```bash
CODEX_SKILL_DIR="$HOME/.codex/skills/lyrics-to-song"
mkdir -p "$CODEX_SKILL_DIR"
cp ./SKILL.md "$CODEX_SKILL_DIR/SKILL.md"
```

Windows PowerShell:

```powershell
$CodexSkillDir = Join-Path $env:USERPROFILE ".codex\skills\lyrics-to-song"
New-Item -ItemType Directory -Path $CodexSkillDir -Force | Out-Null
Copy-Item -Path ".\SKILL.md" -Destination (Join-Path $CodexSkillDir "SKILL.md") -Force
```

不要用 `codex mcp add` 注册 `aimv`；`aimv` 是本地 CLI，不是 MCP server。

### Claude / Claude Desktop / Claude Code

Claude 系列客户端的本地工具、Skills 和 MCP 支持会随版本变化。适配时不要复用 Codex 的目录结构，按当前 Claude 客户端支持的方式接入：

- 如果支持本地 Skills 目录，把 `SKILL.md` 放到该目录
- 如果支持本地命令工具，把工具名设为 `aimv`，命令设为 `node`，参数第一个值指向本目录的 `bin/aimv.js`
- 如果只能通过系统提示词说明工具，把 `SKILL.md` 作为能力说明交给 Agent
- 如果只接受 MCP server，需要额外 MCP wrapper；当前 `aimv` 本身不是 MCP server

### OpenClaw / 其他 Agent

如果 Agent 支持本地工具注册：

```json
{
  "name": "aimv",
  "description": "把中文或英文歌词生成完整歌曲，支持标题、风格、演唱方向、试听链接和音频下载。",
  "command": "node",
  "args": ["<本目录 bin/aimv.js 的绝对路径>"]
}
```

如果 Agent 没有工具注册能力，但能执行 shell，也可以读取 `SKILL.md` 后直接运行 `node ./bin/aimv.js init`、`node ./bin/aimv.js song create`、`node ./bin/aimv.js bgm create` 等命令。

## 错误处理与会员引导

CLI 会输出 Agent 友好的 `[error]` / `[hint]` 标签，并保留后台业务码。

- `code=auth_required` / `code=qrcode_expired`：Agent 应直接运行 `node ./bin/aimv.js init --force` 或 `node ./bin/aimv.js init`，让用户扫码授权
- `code=insufficient_points`：后台业务码 `402`，积分不足。展示 CLI 输出的小程序码，引导用户扫码进入海绵音乐小程序开通会员或获取积分
- `code=quota_limited`：后台业务码 `429` 或次数/额度上限。展示 CLI 输出的小程序码，引导用户扫码进入海绵音乐小程序开通会员提升额度
- `code=reference_not_ready`：先查询参考素材或项目状态，稍后再重试生成
- `code=not_found`：ID 可能错误、已删除或不属于当前账号，优先查 `aimv session tail`

固定小程序码：

```md
![海绵音乐小程序码](https://cdn.68zysm.cn/music-mv/qrcode/static/haimian-miniapp-qr-v20260428.jpg)
```

## 验证命令

```bash
node ./bin/aimv.js config show
node ./bin/aimv.js song create --lyrics "..." --title "海风里" --style mandopop warm --wait
node ./bin/aimv.js song create --lyrics-file ./lyrics.txt --title "海风里" --style mandopop warm --wait
```

## 切换环境

这个发布包默认指向 production 环境。
如果需要临时切换：

```bash
node ./bin/aimv.js config set-base-url https://music-test.68zysm.cn/api/v3
node ./bin/aimv.js config reset-base-url
```

## 登录和作品入口

https://lexuan.club
