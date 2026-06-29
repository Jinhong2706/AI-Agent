# 飞书机器人配置指南

## 1. 创建飞书机器人

### 步骤 1：打开飞书群
- 打开飞书
- 选择一个群聊（或创建新群）

### 步骤 2：添加机器人
1. 点击右上角 **设置** 图标
2. 选择 **添加机器人**
3. 选择 **自定义机器人**
4. 点击 **添加**

### 步骤 3：配置机器人
- **机器人名称**：LinkedIn 监控助手
- **头像**：可选
- **安全设置**：选择 **自定义关键词**
  - 添加关键词：`LinkedIn`、`潜客`、`商机`

### 步骤 4：复制 Webhook URL
- 复制生成的 Webhook 地址（格式：`https://open.feishu.cn/open-apis/bot/v2/hook/xxx-xxx-xxx`）

---

## 2. 更新配置文件

编辑 `.env` 文件：

```bash
# 飞书推送配置
FEISHU_WEBHOOK_URL=你的 Webhook 地址
FEISHU_USER_ID=ou_c3f7154393d37a4f09b784dde48cbf5d
```

---

## 3. 测试推送

```bash
cd "C:\Users\caizheyu\.openclaw\workspace\skills\linkedin-lead-monitor"
python scripts/cli.py check --name "Jolin Ren"
```

如果配置正确，飞书会收到监控通知。

---

## 4. 推送内容

### 高优先级商机（卡片消息）
- 潜客信息（姓名、公司、职位）
- 动态内容
- 商机解读
- 跟进建议
- LinkedIn 主页链接

### 中优先级动态
- 简化的动态通知

### 低优先级动态
- 计入日报汇总（每日 09:00 发送）

---

## 5. 注意事项

1. **Webhook 安全**：不要将 Webhook URL 提交到 Git
2. **频率限制**：飞书机器人有发送频率限制，建议监控间隔 ≥15 分钟
3. **关键词**：确保推送内容包含设置的关键词，否则会被拦截
