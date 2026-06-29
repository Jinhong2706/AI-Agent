---
name: openclaw-backup
version: 2.0.0
description: >
  OpenClaw 全自动备份恢复系统。为 OpenClaw 提供企业级增量备份能力：
  - 基于 tar --listed-increural 的真正增量备份
  - 每周六自动全量 + 工作日增量，保留策略 30天/180天
  - 防并发锁、完整性自动校验、备份前自动快照当前目录
  - 安装时用户指定备份路径，灵活适配不同环境
  - 支持 Linux/macOS，需 Python 3.8+
  使用场景：保护 OpenClaw 配置、工作区、扩展、记忆文件不丢失
---

# OpenClaw 全自动备份恢复系统 v2.0

## 功能特性

- ✅ **真正增量备份**：使用 `tar --listed-incremental`，只备份变化文件，增量体积极小
- ✅ **智能全量策略**：每周六自动全量 + 距上次全量≥7天自动升全量
- ✅ **防误删保护**：恢复前自动将当前目录备份到 `.openclaw.pre-restore-时间戳/`
- ✅ **完整性校验**：每次备份后自动 `tar -tzf` 验证包体
- ✅ **并发保护**：fcntl 锁文件，防止同时运行多个备份进程
- ✅ **灵活安装**：安装时用户指定备份目录，不硬编码路径
- ✅ **自动清理**：按保留策略自动清理过期备份

## 安装

```bash
# 1. 复制 skill 到任意目录（可以是备份盘）
cp -r openclaw-backup-skill /mnt/data3/

# 2. 进入目录并执行安装
cd /mnt/data3/openclaw-backup-skill
chmod +x install.sh uninstall.sh scripts/*.sh scripts/*.py
./install.sh /mnt/data3/openclaw-backup
# 安装向导会询问 OpenClaw 路径（默认 /root/.openclaw，直接回车）

# 3. 确认安装成功
python3 /mnt/data3/openclaw-backup/scripts/openclaw_backup.py list
```

## 目录结构

```
<BACKUP_ROOT>/          # 安装时由用户指定
├── config.env              # 配置文件（安装时生成）
├── full/                   # 全量备份目录
├── incremental/            # 增量备份目录
├── snapshots/              # tar 快照文件（.fsf）
├── backup.log              # 备份日志
└── scripts/
    ├── openclaw_backup.py  # 主程序
    ├── backup.sh           # 备份入口（cron 调用）
    └── restore.sh          # 恢复入口
```

## 备份策略

| 触发条件 | 备份类型 |
|----------|----------|
| 首次备份 | 全量 |
| 每周六 | 全量 |
| 周一~五 | 增量 |
| 距上次全量≥7天 | 全量 |

## 保留策略

- 增量备份：30天
- 全量备份：180天

## 常用命令

```bash
# 手动执行备份
<BACKUP_ROOT>/scripts/backup.sh

# 恢复最新备份
<BACKUP_ROOT>/scripts/restore.sh

# 查看备份列表
python3 <BACKUP_ROOT>/scripts/openclaw_backup.py list

# 验证备份完整性
python3 <BACKUP_ROOT>/scripts/openclaw_backup.py verify

# 清理过期备份
python3 <BACKUP_ROOT>/scripts/openclaw_backup.py clean
```

## 排除规则（默认排除，无需配置）

- **运行时缓存**：`logs/`、`media/`、`delivery-queue/`、`subagents/`、`completions/`、`tasks/`、`canvas/`、`hooks/`
- **插件缓存**：`plugins/`、`node_modules/`、`__pycache__/`
- **密钥目录**：`credentials/`（防泄露）
- **系统目录**：`/root` 下的 `.cache/`、`.ssh/`、`.gnupg/` 等干扰目录
- **.NET 编译产物**：`bin/`、`obj/`

## 卸载

```bash
cd /path/to/openclaw-backup-skill
chmod +x uninstall.sh
./uninstall.sh
# 然后手动删除备份目录（如需）
# rm -rf /mnt/data3/openclaw-backup
```

## 系统要求

- Python 3.8+
- tar（GNU tar）
- cron 守护进程
- 建议备份盘剩余空间 ≥ 5GB
