---
name: send-txmail
version: 0.2.1
description: OpenClaw 通用邮件发送技能，支持交互式/命令行模式，基于QQ邮箱SMTP加密协议，纯原生Python实现，自动记录发送日志，跨环境兼容无绝对路径依赖。
author: 28.7Blog
---

# 📧 send-txmail - OpenClaw 邮件发送技能
支持手动交互 + AI 自动化调用的QQ邮箱发送工具，自带日志持久化，无绝对路径硬编码，可跨服务器无缝迁移。

## 📌 核心特性
- 双模式运行：交互式（人工）、命令行（AI/自动化）
- 强制日志记录：留存发送时间、收件人、主题、内容、发送结果
- 无硬编码路径：基于技能目录自适应，跨服务器兼容
- QQ邮箱SMTP加密传输，安全稳定

## 🚀 运行规范（无绝对路径，跨环境通用）
> 所有执行命令**基于技能根目录**运行（`send-txmail/`），无需修改任何路径

### 方式一：交互式模式（人工手动发送）
```bash
# 进入技能脚本目录
cd scripts
python3 send-txmail.py
```

### 方式二：命令行模式（AI/自动化调用，推荐）
```bash
cd scripts
python3 send-txmail.py --to "2022471677@qq.com" --subject "邮件主题" --content "邮件正文内容"
```

### 调试模式
```bash
cd scripts
python3 send-txmail.py --to "测试邮箱" --subject "测试主题" --content "测试内容" --debug
```

## 📋 强制日志记录规则（必须执行）
技能会**自动记录所有发送行为**，无需手动操作，日志永久留存

### 日志存储路径
```
技能根目录/scripts/emailSend.log
```
（自适应路径，跨服务器迁移无需修改）

### 日志记录字段（完整可追溯）
1. 发送时间（精确到秒）
2. 目标收件邮箱
3. 邮件主题
4. 邮件完整内容
5. 发送结果（成功/失败）

### 日志标准格式
```
[2026-04-22 18:00:00] 收件人: 2022471677@qq.com | 主题: 测试邮件 | 状态: 发送成功 | 内容: 今天也想你了~
[2026-04-22 18:01:00] 收件人: test@qq.com | 主题: 通知 | 状态: 发送失败 | 内容: 测试内容
```

## ⚙️ 配置文件
### 配置路径
```
scripts/lib/config.json
```

### 配置示例
```json
{
    "BaseConfig": {
        "QemailSMTPDress": "smtp.qq.com",
        "QEmailSMTPtimeout": "60",
        "QemailSMTPort": "465"
    },
    "SenderConfig": {
        "QemailPass": "你的QQ邮箱SMTP授权码",
        "QemailSender": "2022471677@qq.com",
        "AliasSenderName": "28.7Blog"
    },
    "DefaultConfig": {
        "DefaultSubjectPrefix": "由OpenClaw发出的邮件-来自28.7Blog",
        "DefaultReplayEmailDress": "2022471677@qq.com"
    }
}
```

## 🎯 使用场景
### 1. OpenClaw AI 自动调用
```bash
cd scripts
python3 send-txmail.py --to "女朋友@qq.com" --subject "我爱你" --content "今天也想你了~💕"
```

### 2. 定时任务（配合 cron 自动化）
```bash
0 8 * * * cd ~/.openclaw/workspace/skills/send-txmail/scripts && python3 send-txmail.py --to "用户@qq.com" --subject "早安" --content "新的一天开始啦！✨"
```

### 3. 批量发送
```bash
for email in 用户1@qq.com 用户2@qq.com; do
  cd scripts && python3 send-txmail.py --to "$email" --subject "通知" --content "重要通知"
done
```

## 🔧 部署步骤
1. 开启QQ邮箱 SMTP/IMAP 服务，获取16位授权码
2. 填写 `config.json` 配置文件
3. 直接运行脚本，无需修改任何路径

## 🐛 故障排查
| 问题 | 解决方案 |
|------|----------|
| 认证失败 | 重新获取QQ邮箱授权码 |
| 连接失败 | 检查网络/端口465是否可用 |
| 配置错误 | 校验config.json格式 |
| 日志未生成 | 检查scripts目录读写权限 |

## 🔄 版本更新
- v0.2.1 - 优化绝对路径问题，新增强制日志规范，跨环境兼容
- v0.2.0 - 支持双模式运行，命令行参数，调试模式
- v0.1.0 - 基础交互式发送

## 📞 使用说明
- AI 调用优先使用**命令行模式**
- 人工使用优先使用**交互式模式**
- 所有发送记录自动归档至日志，永久可查

