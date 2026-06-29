---
name: fanqie-drama-downloader
description: 从番茄达人中心（fanqieopen.com）批量下载漫剧/短剧视频。触发词：下载漫剧、下载短剧、番茄达人、fanqie、批量导出、下载视频、book_id。当用户提到从番茄达人中心下载作品、批量下载剧集、搜索书名/作者名/BookID 后下载时使用此技能。
---

# 番茄达人中心 漫剧下载 Skill

使用 xbrowser 控制已登录的 Chrome 浏览器，在番茄达人中心完成搜索 → 进入详情 → 批量导出下载。全程无需手动干预，下载和文件归档自动完成。

## 前置要求

- Chrome 已启动，且 xbrowser 已通过 `xb init --browser chrome` 初始化
- 番茄达人中心已登录（通常启动 Chrome 时选择「番茄达人」个人资料）
- 已知 Chrome 路径：`D:\常用安装\Google\Chrome\Application`

## 核心工作流程

```
用户请求（提供作品名+总集数）
  → 搜索作品（书名/作者/BookID）
  → 进入详情页
  → 点击「批量导出」
  → 填写集数区间（每批最多50集）
  → 点击下载
  → 【自动】启动 auto-move.ps1 后台监控脚本
    → 检测下载完成（无 .crdownload 文件）
    → 自动创建剧名文件夹（清理特殊符号）
    → 自动剪切 .mp4 到目标文件夹
    → 全部完成后退出
```

## Step 1：搜索作品

在漫剧列表页，使用 `fill` + `press Enter` 搜索：

```bash
# 填入搜索词（填搜索框的ref，格式为 @ref）
xb run --browser chrome fill "@<搜索框ref>" "作品名或BookID"
# 按回车执行搜索（Enter是全局命令，不需要@）
xb run --browser chrome press "" "Enter"
# 等待3秒后拍快照确认结果
xb run --browser chrome wait 3
xb run --browser chrome snapshot --compact
```

**注意**：必须在**红果短剧内容库页面**（`/page/content?tab_type=6`）操作。若当前不在内容库，先点击左侧菜单「内容库」→「红果短剧」进入。

搜索结果出现后，找到目标作品并 `click` 进入详情页。

## Step 2：进入详情页并点击「批量导出」

进入详情页后，快照找到「批量导出」按钮的 ref，然后点击：

```bash
xb run --browser chrome click "@<批量导出按钮的ref>"
```

点击后等待弹窗出现（约2秒），然后拍快照找到弹窗中的 spinbutton（开始集数、结束集数）。

## Step 3：填写集数区间并下载

**关键规则：**
- 每批最多下载 **50 集**，超过需分批
- **【重要规则】**：每批下载完成后，只移动已完成的文件到目标目录，**不再手动提交剩余集数下载**（由网站自动继续或用户自行处理）
- 集数输入框是 `spinbutton` 类型，必须使用 `fill` 命令（不可用 `type`）
- 格式：开始集数填入第一个 spinbutton，结束集数填入第二个 spinbutton

```bash
# 填写开始集数（第一个 spinbutton）
xb run --browser chrome fill "@<start_ref>" "1"
# 填写结束集数（第二个 spinbutton）
xb run --browser chrome fill "@<end_ref>" "20"
# 点击下载按钮
xb run --browser chrome click "@<下载按钮ref>"
```

**下载按钮状态**：初始为 `disabled`，两个 spinbutton 都填写有效数字后变为可点击。点击后弹窗关闭表示任务提交成功。

## Step 4：提交下载 + 自动归档

Chrome 默认下载目录为 `C:\Users\wang\Downloads`。

提交下载任务后，**立即启动 auto-move.ps1 后台监控脚本**，之后的下载和归档全部自动完成，无需任何手动干预。

### 启动自动监控

下载任务提交成功后（弹窗关闭），立即用 `exec background=true` 启动 auto-move.ps1：

```powershell
# 注意：使用 -Command 调用（避免 UTF-8 BOM 文件被 PowerShell 当成脚本来解析导致编码错误）
powershell -NoExit -Command "& 'C:\Users\wang\.qclaw\skills\fanqie-drama-downloader\scripts\auto-move.ps1' -WorkTitle '<作品名>' -TotalEp <总集数>"
```

**参数说明**：
- `-WorkTitle`：作品名称（将自动清理特殊符号，保留中文/字母/数字）
- `-TotalEp`：总集数
- 可选 `-DstRoot`：目标根目录（默认 `D:\短剧素材`）
- 可选 `-SrcDir`：下载源目录（默认 `C:\Users\wang\Downloads`）

### auto-move.ps1 自动完成以下工作

1. 每 8 秒扫描 `C:\Users\wang\Downloads\`
2. 检测到 `.crdownload` 消失且存在 `.mp4` → 判定本批完成
3. 自动创建目标文件夹（清理符号，命名格式：`剧名+总集数+集`，如 `清水谷幽红灾79集`）
4. Move-Item 剪切 .mp4 到目标目录
5. 全部 .mp4 和 .crdownload 都消失 → 打印完成信息并退出

### 文件夹命名规则

自动移除所有非中文/字母/数字/下划线字符，保留中文和字母数字。

例如：输入 `"清水谷·幽红灾！"` → 自动创建文件夹 `清水谷幽红灾79集`

### ⚠️ PowerShell 注意事项

- auto-move.ps1 已加 UTF-8 BOM，可直接调用
- 使用 `-f` 格式化字符串：`("{0}{1}集" -f $CleanTitle, $TotalEp)`
- 避免在 Write-Host 字符串中直接写方括号 `[xxx]`，PowerShell 会解析为数组索引
- 用引号包裹路径中有空格的参数

### 手动确认下载完成的备选方案

如需手动确认，用 PowerShell 检查：

```powershell
# 下载中（有 .crdownload 文件）
Get-ChildItem "C:\Users\wang\Downloads\*.crdownload" | Select-Object Name, @{N="Size(MB)";E={[math]::Round($_.Length/1MB,1)}}

# 无 .crdownload → 下载全部完成
Get-ChildItem "C:\Users\wang\Downloads\*.mp4" | Select-Object Name, @{N="Size(MB)";E={[math]::Round($_.Length/1MB,1)}}
```

## 常见问题

### 页面不在内容库
先点击左侧「内容库」→ 展开后点击「红果短剧」进入。

### spinbutton 填写无反应
必须用 `fill` 命令，不可用 `type` 命令。`type` 对 spinbutton 会返回空结果。

### 下载按钮一直是 disabled
检查两个 spinbutton 是否都填写了**有效整数**，且结束集数 ≥ 开始集数。

### 每批超过50集
需要分批操作，但 auto-move.ps1 会持续监控，每批完成后自动移动，无需手动干预。

### auto-move.ps1 脚本运行报错
检查是否是编码问题，重新用以下命令写入（UTF-8 BOM）：
```powershell
$BOM = [byte[]](0xEF, 0xBB, 0xBF)
$contentBytes = [System.Text.Encoding]::UTF8.GetBytes((Get-Content 'C:\Users\wang\.qclaw\skills\fanqie-drama-downloader\scripts\auto-move.ps1' -Raw))
[System.IO.File]::WriteAllBytes('C:\Users\wang\.qclaw\skills\fanqie-drama-downloader\scripts\auto-move.ps1', $BOM + $contentBytes)
```

## 页面关键 URL

| 页面 | URL 特征 |
|------|-----------|
| 主页 | `/page/task` |
| 内容库（红果短剧） | `/page/content?tab_type=6` |
| 作品详情 | `/page/content/book-detail?tab_type=6&book_id=...` |

## 参考资料

- 页面 refs 对照表：见 `references/page_refs.md`
- 文件移动脚本：见 `scripts/move_downloads.ps1`
