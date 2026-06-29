# LinkedIn 潜客监控 - 快速参考

> 🍟 薯条提示：这是精简版快速参考，完整文档见 [SKILL.md](SKILL.md)

---

## ⚡ 3 分钟快速启动

```bash
# 1. 进入目录
cd "C:\Users\caizheyu\.openclaw\workspace\skills\linkedin-lead-monitor"

# 2. 安装依赖
pip install playwright sqlite3 requests python-dotenv
playwright install chromium

# 3. 初始化配置
python scripts/cli.py setup

# 4. 添加潜客
python scripts/cli.py add --url "https://www.linkedin.com/in/潜客 URL" --name "姓名" --priority high

# 5. 登录 LinkedIn
python scripts/cli.py login

# 6. 开始监控
python scripts/cli.py check
```

---

## 📋 常用命令

| 命令 | 说明 |
|------|------|
| `python scripts/cli.py list` | 查看潜客列表 |
| `python scripts/cli.py check` | 检查全部潜客 |
| `python scripts/cli.py check --name "姓名"` | 检查特定潜客 |
| `python scripts/cli.py watch --interval 30` | 持续监控（30 分钟） |
| `python scripts/cli.py login` | 手动登录 LinkedIn |
| `python scripts/cli.py status` | 查看监控状态 |

---

## ⚙️ 配置检查清单

- [ ] `.env` 文件已创建（运行 `setup` 命令）
- [ ] `FEISHU_USER_ID` 已配置（你的飞书用户 ID）
- [ ] LinkedIn 账号已登录（运行 `login` 命令）
- [ ] 至少添加了 1 个潜客（运行 `add` 命令）

---

## 📬 推送说明

- **推送方式**：飞书消息（通过 OpenClaw 集成）
- **推送内容**：潜客动态报告（汇总格式）
- **推送时机**：每次检查时发现新动态

---

## 🔧 常见问题

**Q: 浏览器启动失败？**
```bash
playwright install chromium
```

**Q: LinkedIn 登录失败？**
```bash
python scripts/cli.py login
# 在打开的浏览器中手动登录
```

**Q: 飞书推送失败？**
- 检查 `FEISHU_USER_ID` 是否正确
- 确保 OpenClaw 飞书集成已配置

**Q: 动态抓取为空？**
- 确保 LinkedIn 已登录
- 潜客可能没有公开动态

---

## 📁 重要文件

| 文件 | 说明 |
|------|------|
| `.env` | 配置文件（账号、推送设置） |
| `data/leads.db` | 数据库（潜客信息） |
| `data/state/storage.json` | LinkedIn 登录会话 |
| `scripts/cli.py` | 命令行工具 |

---

## 🚀 下一步

1. 添加更多潜客
2. 设置持续监控：`python scripts/cli.py watch --interval 30`
3. 查看完整文档：[SKILL.md](SKILL.md)

---

**🍟 薯条出品，必属精品！**
