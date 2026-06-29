---
name: linkedin-lead-monitor
description: LinkedIn 潜客自动监控与商机提醒。监控目标潜客的职位变动、公司动态、内容发布等关键信号，AI 识别商机优先级并推送跟进建议。使用场景：B2B 外贸销售监控潜客动态、跨境电商 BD 发现采购需求、海外业务拓展跟踪决策人变动。
version: 1.0.0
updated: 2026-04-02
---

# LinkedIn 潜客监控 Skill

## 📋 功能概述

自动监控 LinkedIn 潜客的最新动态，包括：
- ✅ 职位变动（新职位、公司变更）
- ✅ 公司动态（融资、扩张、新产品）
- ✅ 内容发布（帖子、文章、评论）
- ✅ 互动行为（点赞、分享）

自动识别商机优先级，通过飞书推送跟进建议。

---

## 🚀 快速开始（5 分钟配置）

### 步骤 1：安装依赖

```bash
cd "C:\Users\caizheyu\.openclaw\workspace\skills\linkedin-lead-monitor"

# 安装 Python 依赖
pip install playwright sqlite3 requests python-dotenv

# 安装 Chromium 浏览器
playwright install chromium
```

### 步骤 2：初始化配置

```bash
# 创建配置文件
python scripts/cli.py setup
```

这会创建 `.env` 配置文件和 `data/` 数据库目录。

### 步骤 3：配置飞书用户 ID

编辑 `.env` 文件：

```bash
notepad .env
```

修改这一行（你的飞书用户 ID）：
```bash
FEISHU_USER_ID=ou_c3f7154393d37a4f09b784dde48cbf5d
```

### 步骤 4：添加潜客

```bash
# 添加单个潜客
python scripts/cli.py add --url "https://www.linkedin.com/in/潜客 URL" --name "潜客姓名" --priority high

# 示例
python scripts/cli.py add --url "https://www.linkedin.com/in/renqiaoling20200108/" --name "Jolin Ren" --priority high
```

### 步骤 5：首次登录 LinkedIn

```bash
# 手动登录并保存会话
python scripts/cli.py login
```

这会打开浏览器，请在浏览器中登录 LinkedIn，登录后会话会自动保存。

### 步骤 6：开始监控

```bash
# 单次检查
python scripts/cli.py check

# 检查特定潜客
python scripts/cli.py check --name "Jolin Ren"

# 持续监控（每 30 分钟）
python scripts/cli.py watch --interval 30
```

---

## 📁 项目结构

```
linkedin-lead-monitor/
├── .env                          # 配置文件（需手动编辑）
├── .env.template                 # 配置模板
├── SKILL.md                      # 本文档
├── data/
│   ├── leads.db                  # SQLite 数据库（潜客信息）
│   └── state/
│       ├── linkedin-profile/     # LinkedIn 登录会话
│       └── storage.json          # 登录状态备份
├── scripts/
│   ├── cli.py                    # 命令行工具
│   ├── monitor.py                # 监控核心逻辑
│   └── notify.py                 # 消息推送模块
└── references/
    └── opportunity-rules.md      # 商机识别规则
```

---

## ⚙️ 配置文件详解

### `.env` 文件

```bash
# ============ 必填配置 ============

# LinkedIn 账号（用于首次登录）
LINKEDIN_EMAIL=your.email@example.com
LINKEDIN_PASSWORD=your_password

# 飞书用户 ID（接收推送消息）
FEISHU_USER_ID=ou_c3f7154393d37a4f09b784dde48cbf5d

# ============ 可选配置 ============

# 飞书 Webhook（备用推送方式，目前使用 OpenClaw 集成）
FEISHU_WEBHOOK_URL=

# Chrome 用户数据目录（复用已登录的 Chrome，可选）
# CHROME_USER_DATA=C:\Users\你的用户名\AppData\Local\Google\Chrome\User Data\Default

# 监控设置
CHECK_INTERVAL_MINUTES=30
TIMEZONE=Asia/Shanghai

# 浏览器设置
HEADLESS=false          # 是否无头模式（建议 false，便于调试）

# 微信推送（未实现）
WECHAT_ENABLED=false
WECHAT_SESSION_KEY=

# 邮件推送（未实现）
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASSWORD=your_app_password
```

---

## 📊 命令行工具参考

### 潜客管理

```bash
# 添加潜客
python scripts/cli.py add --url <LinkedIn 主页 URL> --name <姓名> [--priority high|medium|low]

# 查看潜客列表
python scripts/cli.py list

# 删除潜客
python scripts/cli.py remove --name <姓名>

# 批量导入（CSV 格式）
python scripts/cli.py import --file leads.csv

# 导出潜客数据
python scripts/cli.py export --format csv --output leads_backup.csv
```

### 监控执行

```bash
# 单次检查全部潜客
python scripts/cli.py check

# 检查特定潜客
python scripts/cli.py check --name "Jolin Ren"

# 持续监控（后台运行）
python scripts/cli.py watch --interval 30

# 查看监控状态
python scripts/cli.py status
```

### 记录查询

```bash
# 查看监控历史
python scripts/cli.py history

# 查看特定潜客的历史
python scripts/cli.py history --lead "Jolin Ren"

# 查看统计报表
python scripts/cli.py stats
```

### 系统工具

```bash
# 初始化配置
python scripts/cli.py setup

# 手动登录 LinkedIn
python scripts/cli.py login

# 查看日志
python scripts/cli.py logs
```

---

## 📬 推送规则

### 优先级分类

| 优先级 | 触发条件 | 推送方式 |
|--------|----------|----------|
| 🔴 **高** | 职位变动、公司变更、融资/扩张新闻 | 飞书即时推送 |
| 🟡 **中** | 高优先级潜客的新动态、第一条动态 | 飞书即时推送 |
| 🟢 **低** | 普通动态、日常内容发布 | 计入日报汇总 |

### 报告格式

**动态报告示例：**
```
📊 LinkedIn 潜客动态报告

潜客：Jolin Ren
公司：XXX 公司
时间：2026-04-02 14:52

最新动态（5 条）:
1. 任巧玲 - B2B Social Media & AI Lead Generation...
2. 越来越多的企业重视社媒，需要在社媒上开发...
3. 越来越多的企业重视社媒，需要在社媒上开发...
4. 任巧玲 - B2B Social Media & AI Lead Generation...
5. Today's global trade briefing is not about more in...

💡 建议：点赞互动 + 关注动态 + 寻找沟通时机

主页：https://www.linkedin.com/in/renqiaoling20200108/
```

---

## 🔧 故障排查

### 问题 1：浏览器启动失败

**症状：**
```
Error: browserType.launch: Executable doesn't exist
```

**解决：**
```bash
# 重新安装 Chromium
playwright install chromium

# 验证安装
python -c "from playwright.sync_api import sync_playwright; print('OK')"
```

### 问题 2：LinkedIn 登录失败

**症状：**
```
[WARN] 未登录 LinkedIn，尝试自动登录...
[ERROR] 登录失败
```

**解决：**
1. 检查 `.env` 中的账号密码是否正确
2. LinkedIn 可能要求验证码，需手动登录
3. 使用 `python scripts/cli.py login` 手动登录并保存会话

### 问题 3：飞书推送失败

**症状：**
```
✗ 飞书消息发送失败：[plugins] plugins.allow is empty
```

**解决：**
- 这是 OpenClaw 飞书集成的编码问题
- 解决方案：通过 `message` 工具发送，或联系管理员配置飞书 Webhook

### 问题 4：页面加载超时

**症状：**
```
[ERROR] 检查主页失败：Page.goto: Timeout 30000ms exceeded
```

**解决：**
1. 检查网络连接
2. LinkedIn 可能需要更长时间加载，修改 `monitor.py` 中的 timeout 参数
3. 使用已登录的 Chrome 用户数据（配置 `CHROME_USER_DATA`）

### 问题 5：动态抓取为空

**症状：**
```
[WARN] 未找到动态内容
```

**解决：**
1. 确保 LinkedIn 已登录
2. 潜客可能没有公开动态
3. 检查选择器是否过期（LinkedIn 经常更新页面结构）

---

## 📋 最佳实践

### 1. 潜客选择策略

**高优先级潜客：**
- 目标公司的决策者（VP/Director/Manager）
- 采购部门负责人
- 近期有互动但未转化的潜客

**中优先级潜客：**
- 行业相关人士
- 潜在合作伙伴
- 竞争对手公司员工

### 2. 监控频率建议

| 潜客类型 | 检查间隔 | 推送策略 |
|----------|----------|----------|
| 高优先级 | 15-30 分钟 | 即时推送 |
| 中优先级 | 30-60 分钟 | 即时推送 |
| 低优先级 | 2-4 小时 | 日报汇总 |

### 3. 跟进时机

- **职位变动后 24 小时内**：发送祝贺消息，重新介绍产品
- **公司动态后 48 小时内**：发送祝贺 + 价值主张
- **内容发布后**：点赞评论互动，建立联系

### 4. 会话管理

- 定期（每周）检查登录会话是否有效
- 如会话失效，运行 `python scripts/cli.py login` 重新登录
- 备份 `data/state/storage.json` 以防丢失

---

## 🔒 安全注意事项

### 1. LinkedIn 账号安全

- ⚠️ 不要频繁登录/退出，避免触发风控
- ⚠️ 建议使用专门的监控账号
- ⚠️ 设置合理的检查间隔（≥15 分钟）
- ⚠️ 遵守 LinkedIn 服务条款

### 2. 数据存储安全

- 🔒 `.env` 文件不要提交到 Git
- 🔒 数据库文件定期备份
- 🔒 敏感信息（密码）使用环境变量

### 3. 合规使用

- ✅ 仅监控已建立业务联系的潜客
- ✅ 不要用于骚扰或垃圾营销
- ✅ 尊重用户隐私

---

## 📝 CSV 导入格式

批量导入潜客时，CSV 文件格式：

```csv
name,url,company,position,priority
John Doe,https://www.linkedin.com/in/john-doe,TechCorp,Marketing Director,high
Jane Smith,https://www.linkedin.com/in/jane-smith,StartupXYZ,CEO,medium
```

---

## 🧪 测试命令

```bash
# 测试登录状态
python scripts/cli.py login

# 测试单次检查
python scripts/cli.py check --name "Jolin Ren"

# 测试推送
python -c "from scripts.notify import NotificationManager; m = NotificationManager(); m.send_dynamic_report('Test', [{'content': '测试内容', 'type': 'post'}], {'name': 'Test', 'linkedin_url': 'https://linkedin.com'})"

# 查看数据库
python -c "import sqlite3; conn = sqlite3.connect('data/leads.db'); print(conn.execute('SELECT * FROM leads').fetchall())"
```

---

## 🔄 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0.0 | 2026-04-02 | 完整功能发布：自动登录、动态抓取、飞书推送 |
| v0.1.0 | 2026-03-31 | 初始版本，核心监控框架 |

---

## 📞 支持与反馈

如有问题或建议，请联系：
- 开发者：薯条 🍟
- 所属团队：Kingsway Video 产品运营

---

**🍟 薯条提示：配置完成后，运行 `python scripts/cli.py check` 测试一下！**
