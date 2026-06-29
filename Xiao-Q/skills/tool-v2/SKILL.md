---
name: clean-cdrive
description: >
  Clean up C drive disk space on Windows by safely removing temporary files,
  cache, and other non-essential data. Use this skill when the user says "C
  盘满了", "磁盘清理", "清理C盘", "disk cleanup", "C drive full", "clean up
  disk space", "释放磁盘空间", or asks about freeing up storage. Covers safe
  temp file cleanup, Windows built-in cleanup tools, WinSxS reduction,
  browser cache cleanup, and disk space analysis. Does NOT delete user
  documents, installed programs, or system files. Prioritizes safety —
  verifies paths before deletion and avoids sensitive directories.
---

# C 盘磁盘清理技能 (Windows Disk Cleanup)

## Overview

安全释放 C 盘磁盘空间。本技能使用 Windows 内置工具和安全的 PowerShell 命令清理非必要临时文件，不会删除用户文档、已安装程序或系统关键文件。

## 核心原则

1. **安全第一** — 不删除系统关键文件、用户文档、已安装程序
2. **可逆操作优先** — 优先使用 Windows 内置工具 (cleanmgr, dism)
3. **操作前预览** — 执行删除前先统计可释放空间大小
4. **分级清理** — 提供安全/适度的清理级别

---

## 快速参考

| 任务 | 方法 |
|------|------|
| 快速分析磁盘空间 | `windirstat` 或 `du` 类工具 |
| Windows 磁盘清理 | `cleanmgr /sageset` |
| 系统文件清理 | `cleanmgr /sageset` 含系统文件选项 |
| WinSxS 精简 | `DISM /Online /Cleanup-Image /StartComponentCleanup` |
| 临时文件清理 | PowerShell 删除 `$env:TEMP` 等 |
| 休眠文件释放 | `powercfg /hibernate off` |

---

## 清理流程

### 第一步：分析磁盘使用情况

执行以下命令查看 C 盘整体使用情况：

```powershell
# 查看 C 盘使用概况
Get-PSDrive C | Select-Object Used, Free

# 查看最大的目录 (需要安装 PSWriteProgress 或使用以下方法)
Get-ChildItem "C:\" -Directory -ErrorAction SilentlyContinue | 
    ForEach-Object { $size = (Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum; [PSCustomObject]@{Path=$_.FullName; SizeMB=[math]::Round($size/1MB, 2)} } | 
    Sort-Object SizeMB -Descending | Select-Object -First 20
```

### 第二步：安全清理级别

#### Level 1 — 安全清理 (推荐)

清理 100% 安全的临时文件，不会影响任何功能：

```powershell
# 清理 Windows 临时文件
Remove-Item "$env:WINDIR\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue

# 清理用户临时文件
Remove-Item "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue

# 清理 Delivery Optimization 文件 (Windows Update 下载缓存)
Remove-Item "C:\Windows\SoftwareDistribution\Download\*" -Recurse -Force -ErrorAction SilentlyContinue

# 清理回收站
Clear-RecycleBin -Force -ErrorAction SilentlyContinue

# 清理 thumbnail 缓存
Remove-Item "$env:LOCALAPPDATA\Microsoft\Windows\Explorer\thumbcache_*.db" -Force -ErrorAction SilentlyContinue
Remove-Item "$env:LOCALAPPDATA\Microsoft\Windows\Explorer\*.tmp" -Force -ErrorAction SilentlyContinue
```

**安全原因：** 以上文件均可由 Windows 或应用程序自动重新生成，删除后不影响系统正常运行。

#### Level 2 — Windows 内置磁盘清理

使用 cleanmgr 的标准配置和系统文件清理：

```powershell
# 配置磁盘清理选项 (写入注册表)
$cleanMgrSettings = @{
    "StateFlags0001" = 2
    "StateFlags0001" = 2
}
# 注意：cleanmgr /sageset 需要交互界面，使用以下方法自动化

# 直接使用 cleanmgr 清理 (推荐方法)
cleanmgr /sagerun:1
```

更好的方法是使用 Dism 清理 WinSxS：

```powershell
# 查看 WinSxS 大小
DISM /Online /Cleanup-Image /AnalyzeComponentStore

# 安全清理 WinSxS (保留最近 30 天版本以便回滚)
DISM /Online /Cleanup-Image /StartComponentCleanup /ResetBase
```

> **注意：** `/ResetBase` 会删除旧版本 Windows 组件，导致无法卸载最近的系统更新。仅当用户确认不需要回滚时执行。

#### Level 3 — 适度清理 (需用户确认)

```powershell
# 清理 Prefetch 文件 (应用启动缓存，可被重建)
Remove-Item "C:\Windows\Prefetch\*" -Recurse -Force -ErrorAction SilentlyContinue

# 清理 Windows 错误报告
Remove-Item "C:\Windows\Logs\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:LOCALAPPDATA\Microsoft\Windows\WER\*" -Recurse -Force -ErrorAction SilentlyContinue

# 清理临时 Internet 文件
Remove-Item "$env:LOCALAPPDATA\Microsoft\Windows\INetCache\*" -Recurse -Force -ErrorAction SilentlyContinue
```

### 第三步：浏览器缓存清理

```powershell
# Edge 浏览器缓存
Remove-Item "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Code Cache\*" -Recurse -Force -ErrorAction SilentlyContinue

# Chrome 浏览器缓存
Remove-Item "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Code Cache\*" -Recurse -Force -ErrorAction SilentlyContinue
```

### 第四步：可选的大文件处理 (需用户明确确认)

向用户展示以下选项并让其选择：

| 操作 | 可释放空间 | 说明 |
|------|-----------|------|
| 关闭休眠 | 约 3-20 GB | 禁用后无法使用快速启动 |
| 删除 Windows.old | 约 10-30 GB | 升级后 30 天内可回滚 |
| 卸载不常用应用 | 不定 | 列出按大小排序的已安装应用 |
| 移动个人文件 | 不定 | 如微信/QQ 文件存储目录 |

---

## 安全限制 (禁止操作)

以下路径和文件类型**永远不能删除**：

- `C:\Windows\System32\` — 系统关键文件
- `C:\Program Files\` 或 `C:\Program Files (x86)\` — 已安装程序
- `C:\Users\*\Documents\` — 用户文档
- `C:\Users\*\Desktop\` — 桌面文件
- `C:\Boot\` — 启动文件
- `C:\ProgramData\` — 谨慎处理，不批量删除
- `*.exe`, `*.dll`, `*.sys`, `*.drv` — 可执行和系统文件
- 页面文件 `pagefile.sys` 和休眠文件 `hiberfil.sys` (除非用户明确要求使用 `powercfg` 关闭)

## 输出模板

每次清理完成后，按以下格式输出摘要：

```
## 磁盘清理结果

### 清理前状态
- 总空间: [总大小]
- 已用: [已用大小]
- 可用: [可用大小]
- 使用率: [百分比]

### 执行的操作
- [操作1] — ✓ 完成 / ⚠️ 部分失败
- [操作2] — ✓ 完成 / ⚠️ 部分失败

### 清理结果
- 释放空间: [释放的 MB/GB]
- 清理后可用: [清理后可用空间]

### 建议
- [后续优化建议]
```

---

## Error Handling

| 错误 | 处理方式 |
|------|---------|
| 文件被占用无法删除 | 跳过该文件，记录路径，继续清理其余文件 |
| 清理无权限的目录 | 报告需要管理员权限，建议以管理员身份运行 Claude |
| cleanmgr 不可用 | 回退到 PowerShell 手动清理 |
| 磁盘空间仍然不足 | 建议用户使用 Level 3 选项或手动移动大文件 |

---

## References

- `references/du-cn.md` — 当用户需要可视化分析磁盘空间时读取
