# 安装、分享与发布指南

## 一、安装给自己用

### 项目级
适合只在某个仓库里使用：

```text
项目目录/.workbuddy/skills/knowledge-safe-merge/
```

### 用户级
适合多个项目复用：

```text
~/.workbuddy/skills/knowledge-safe-merge/
```

---

## 二、分享给别人

### 最稳妥的分享内容
直接分享整个 `knowledge-safe-merge/` 文件夹，不要只发 `SKILL.md`。

建议至少包含：
- `SKILL.md`
- `README.md`
- `references/`
- `scripts/`

### 推荐分发格式
- `.skill`：适合标准化分发
- `.zip`：适合手工传输或临时分享

---

## 三、接收方的安装方式

对方拿到后，可以：

1. 解压到自己的 `~/.workbuddy/skills/`
2. 或放到某个项目的 `.workbuddy/skills/`
3. 在需要做知识库 JSON 安全合并时使用它

---

## 四、公开发布前的检查清单

发布前请确认：

- [ ] 没有硬编码你的个人路径
- [ ] 没有硬编码你的域名
- [ ] 没有硬编码你的服务器账号、密钥或 token
- [ ] 没有把某个具体项目误写成通用规则
- [ ] README 已写清楚用途、安装、命令示例
- [ ] 命令示例可直接复制使用
- [ ] 如果有脚本，已经完成 dry-run 验证

---

## 五、推荐公开发布方式

### 方式 1：GitHub 仓库
适合长期维护。

建议仓库结构：

```text
knowledge-safe-merge/
├── SKILL.md
├── README.md
├── references/
├── scripts/
└── examples/
```

### 方式 2：社群分享
适合快速传播。

建议附一句说明：

> 这是一个防止知识库 JSON 更新时覆盖旧文章的 Skill，适合内容站、知识库站、静态 CMS 的安全合并更新。

### 方式 3：作为项目模板的一部分
适合交付给客户、学员或团队成员。

---

## 六、建议的示例话术

### 发给朋友
> 我整理了一个通用 Skill，专门解决“新 JSON 导入后把旧文章覆盖掉”的问题。你把它放到 `.workbuddy/skills/knowledge-safe-merge/` 就能用了。

### 发到 GitHub
> Knowledge Safe Merge is a reusable WorkBuddy skill for safely merging article JSON data without wiping historical content.

---

## 七、后续可继续增强的方向

- 增加对自定义字段的 schema 校验
- 支持更多匹配规则
- 支持 CSV / Markdown 批量导入
- 增加示例数据和自动化测试
