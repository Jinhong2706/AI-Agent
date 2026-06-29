# Vetting Checklist - 技能安全审查清单

完整的安全审查流程，用于评估待安装技能的安全性。

---

## Step 1: 元数据检查

| 检查项 | 要求 | 红旗 |
|--------|------|------|
| `name` | 匹配预期名称 | typosquatting 疑似 |
| `version` | 符合 semver | 无版本或异常格式 |
| `description` | 清晰匹配功能 | 模糊或误导 |
| `author` | 可识别身份 | 匿名或可疑 |

---

## Step 2: 权限范围分析

| 权限 | 风险等级 | 合法用途示例 | 需审查用途 |
|------|----------|--------------|------------|
| `fileRead` | 🟢 低 | 读取用户请求的文件 | 读取敏感目录 |
| `fileWrite` | 🟡 中 | 写入用户指定的输出 | 修改系统文件 |
| `network` | 🔴 高 | 访问指定 API | 未知端点 |
| `shell` | ⛔ 严重 | 执行用户请求的命令 | 后门命令 |

### 权限组合风险

| 组合 | 风险 | 说明 |
|------|------|------|
| `network` + `shell` | ⛔ 极高 | 可能数据泄露 |
| `fileRead` + `network` | 🔴 高 | 可能上传敏感数据 |
| `fileWrite` + `shell` | 🔴 高 | 可能修改系统配置 |

---

## Step 3: 内容分析红旗

### 关键红旗（立即阻止）⛔

```
- ~/.ssh, ~/.aws, ~/.env 引用
- ~/.gnupg, ~/.config/credentials
- curl | bash, wget | sh 命令
- nc -l, bash -i, /dev/tcp
- Base64 编码内容
- 混淆代码或加密字符串
- 禁用安全设置指令
- 外部服务器/IP引用
- eval(), exec() 不安全调用
```

### 警告红旗（标记审查）🟡

```
- 过宽文件访问: /**/*, /etc/, ~/.*
- 修改 .bashrc, .zshrc, crontab
- sudo 或提权请求
- 提示注入模式: "ignore previous", "you are now"
- 动态代码生成
- 未解释的网络请求
- 隐藏依赖项
```

### 信息红旗（关注）🟢

```
- 缺失描述或版本
- 作者无公开资料
- 文件结构混乱
- 命名不规范
- 缺少测试用例
```

---

## Step 4: Typosquat 检测

### 检测规则

| 原技能 | 仿冒示例 | 检测类型 |
|--------|----------|----------|
| git-commit-helper | git-commiter | 缺字母+换位 |
| github-push | gihub-push | 缺字母 |
| code-review | code-reveiw | 字母换位 |
| node-package | node_packge | 分隔符+缺字母 |
| aws-helper | aws-helpr | 缺字母 |
| slack-bot | slak-bot | 缺字母 |

### 检测方法

1. 单字符增删改
2. 同形字替换（l/1, O/0, a/@）
3. 多余分隔符（- vs _）
4. 常见拼写错误
5. 相似发音词

---

## 信任层级

| 层级 | 来源 | 信任度 | 审查要求 |
|------|------|--------|----------|
| 1 | Official OpenClaw | ⭐⭐⭐⭐⭐ | 基础检查 |
| 2 | UseClawPro 验证 | ⭐⭐⭐⭐ | 基础检查 |
| 3 | 知名作者公开仓库 | ⭐⭐⭐ | 标准审查 |
| 4 | 社区高下载多评论 | ⭐⭐ | 标准审查 |
| 5 | 新作者未知来源 | ⭐ | 全审查 |

---

## 审查报告模板

```
SKILL VETTING REPORT
====================
Skill: <name>
Author: <author>
Version: <version>
Source: <platform/URL>

VERDICT: SAFE / WARNING / DANGER / BLOCK

PERMISSIONS:
  fileRead:  [GRANTED/DENIED] — <justification>
  fileWrite: [GRANTED/DENIED] — <justification>
  network:   [GRANTED/DENIED] — <justification>
  shell:     [GRANTED/DENIED] — <justification>

RED FLAGS:
  Critical: <count>
  Warning:  <count>
  Info:     <count>

FINDINGS:
  1. [SEVERITY] <description>
  2. [SEVERITY] <description>
  ...

RECOMMENDATION:
  <install / review further / sandbox test / do not install>

TRUST LEVEL: <1-5>
NEXT STEPS: <具体建议>
```

---

## 审查规则

1. **永不跳过**：即使热门技能也要审查
2. **版本检查**：安全技能的新版本可能有问题
3. **沙箱优先**：不确定时先在沙箱运行
4. **报告可疑**：发现恶意技能立即报告
5. **定期复查**：已安装技能也需要定期审查