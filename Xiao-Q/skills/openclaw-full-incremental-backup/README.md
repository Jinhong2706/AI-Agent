# OpenClaw 全自动备份恢复系统 v2.0.0

## 📦 目录说明

```
openclaw-backup-skill/
├── SKILL.md              # ClawHub 技能描述文件
├── README.md             # 本文档
├── install.sh            # 安装脚本
├── uninstall.sh          # 卸载脚本
├── config/
│   └── config.env        # 配置文件模板
└── scripts/
    ├── openclaw_backup.py  # Python 备份主程序
    ├── backup.sh           # 备份入口（cron 调用）
    └── restore.sh          # 恢复入口
```

## 🚀 快速安装

### 方式一：使用安装向导（推荐）

```bash
# 1. 复制到目标目录
cp -r openclaw-backup-skill /mnt/data3/

# 2. 进入目录
cd /mnt/data3/openclaw-backup-skill

# 3. 添加执行权限
chmod +x install.sh uninstall.sh scripts/*.sh scripts/*.py

# 4. 执行安装（指定备份存储目录）
./install.sh /mnt/data3/openclaw-backup

# 5. 安装向导会提示输入 OpenClaw 路径（默认 /root/.openclaw，直接回车）
```

### 方式二：静默安装（所有参数一次给出）

```bash
./install.sh /mnt/data3/openclaw-backup << EOF

/root/.openclaw
EOF
```

## 📖 使用说明

### 备份

```bash
# 手动执行备份（自动判断增量或全量）
/mnt/data3/openclaw-backup/scripts/backup.sh

# 强制执行（跳过锁检查，一般不需要）
/mnt/data3/openclaw-backup/scripts/backup.sh --force
```

### 恢复

```bash
# 恢复前会自动将当前 .openclaw 目录备份到
# .openclaw.pre-restore-YYYYMMDD-HHMMSS/，无需手动备份

/mnt/data3/openclaw-backup/scripts/restore.sh
```

### 查看备份

```bash
python3 /mnt/data3/openclaw-backup/scripts/openclaw_backup.py list
```

### 验证完整性

```bash
python3 /mnt/data3/openclaw-backup/scripts/openclaw_backup.py verify
```

### 清理过期备份

```bash
python3 /mnt/data3/openclaw-backup/scripts/openclaw_backup.py clean
```

## ⏰ 定时任务

安装后自动注册以下 cron：

| 时间 | 类型 |
|------|------|
| 周六 23:59 | 全量备份 |
| 周一~周五 23:59 | 增量备份 |

查看 cron：
```bash
crontab -l | grep backup
```

## ⚙️ 配置说明

配置文件位于：`/mnt/data3/openclaw-backup/config.env`

```bash
# OpenClaw 家目录（被备份的目录）
OPENCLAW_HOME="/root/.openclaw"

# 备份存储根目录
BACKUP_ROOT="/mnt/data3/openclaw-backup"
```

修改配置后，下次备份自动生效。

## 📊 默认排除规则

以下目录/文件默认不备份（无需配置）：

| 类型 | 目录/文件 |
|------|-----------|
| OpenClaw 运行时缓存 | `logs/`、`media/`、`delivery-queue/`、`subagents/`、`completions/`、`tasks/`、`canvas/`、`hooks/` |
| 插件和依赖缓存 | `plugins/`、`node_modules/`、`__pycache__/` |
| 密钥目录 | `credentials/` |
| 系统干扰目录 | `.cache/`、`.ssh/`、`.gnupg/`、`.config/`、`.vscode-server/` 等 |
| .NET 编译产物 | `bin/`、`obj/`（可重建） |
| 临时文件 | `*.tmp`、`*.log`、`*.lock`、`*.swp` 等 |

## 🔄 备份效果对比

| 版本 | 全量大小 | 说明 |
|------|----------|------|
| 原版 v1.0 | 8.9GB | `--newer` 逻辑失效，增量虚胖 |
| 当前 v2.0 | ~865MB | `--listed-incremental` 真正增量 + 排除无用缓存 |

## 🗑️ 卸载

```bash
cd /mnt/data3/openclaw-backup-skill
chmod +x uninstall.sh
./uninstall.sh

# 如需删除备份数据（谨慎！）
# rm -rf /mnt/data3/openclaw-backup
```

## ❓ 常见问题

**Q: 备份盘快满了怎么办？**
A: 备份系统会自动清理 30 天前的增量备份和 180 天前的全量备份。如需手动清理：
```bash
# 查看各备份大小
python3 /mnt/data3/openclaw-backup/scripts/openclaw_backup.py list
```

**Q: 锁文件残留，备份无法运行？**
A: 使用 `--force` 参数强制执行：
```bash
/mnt/data3/openclaw-backup/scripts/backup.sh --force
```

**Q: 想修改备份时间？**
A: 手动编辑 crontab：
```bash
crontab -e
# 修改 59 23 为你想要的分钟和小时
```

**Q: 恢复后发现不是想要的时间点？**
A: 恢复前会自动将当前目录备份到 `.openclaw.pre-restore-*/`，可手动恢复：
```bash
mv /root/.openclaw /root/.openclaw.corrupt
mv /root/.openclaw.pre-restore-xxx /root/.openclaw
```
