# Search Platforms - 技能搜索平台指南

多平台技能发现和搜索策略。

---

## 平台对比

| 平台 | 特点 | 最佳用例 | 访问方式 |
|------|------|----------|----------|
| **skills.sh** | 官方生态，规模最大 | 正式搜索 | `npx skills` |
| **Cocoloop** | 国内加速，安全审计 | 国内用户 | 浏览器 |
| **GitHub** | 开源社区，可控 | 开发者 | `gh` CLI |
| **SkillsMP** | 中文界面 | 中文用户 | 浏览器+API |
| **ClawHub** | 易用但有限流 | 备选 | `clawhub` CLI |

---

## skills.sh（推荐）

### 基本命令

```bash
# 搜索技能
npx skills find "关键词"

# 搜索示例
npx skills find "postgres backups"
npx skills find "react hooks"
npx skills find "pdf editor"

# 安装技能（建议手动确认）
npx skills add <owner/repo@skill>
npx skills add steipete/summarize
```

### 搜索技巧

- 使用具体关键词而非泛泛词
- 包含功能+技术栈组合
- 尝试英文和关键词变体

---

## Cocoloop（国内推荐）

### 使用方式

浏览器访问：https://hub.cocoloop.cn/search?q=关键词

### 优势

- 国内 CDN 加速
- 预先安全审计
- 安装量+推荐率显示
- 中文界面

---

## GitHub 搜索

### 基本命令

```bash
# 搜索 OpenClaw skills
gh search repos "openclaw skill 关键词" --limit 10

# 搜索特定主题
gh search repos "topic:openclaw-skill" --limit 20

# 搜索特定作者
gh search repos "owner:username skill"
```

### 过滤选项

```bash
--limit 20       # 结果数量
--sort stars     # 按星数排序
--order desc     # 降序排列
```

---

## SkillsMP

### 使用方式

浏览器访问：https://skillsmp.com/zh

### 特点

- 纯中文界面
- 分类导航
- API 可用
- 社区评分

---

## ClawHub（备选）

### 安装 CLI

```bash
npm i -g clawhub
```

### 基本命令

```bash
# 搜索
clawhub search "关键词"

# 安装
clawhub install <skill-name>

# 查看详情
clawhub info <skill-name>
```

### 注意

- 有 API 限流
- 结果可能不如 skills.sh 完整

---

## 多平台搜索策略

### 推荐流程

```
1. skills.sh 搜索 → 获取最大范围
2. Cocoloop 验证 → 查看安装量和评分
3. 安全审查 → 运行 vetting checklist
4. 安装决策 → 根据审查结果决定
```

### 对比要点

| 维度 | 检查内容 |
|------|----------|
| 安装量 | 哪个平台更受欢迎 |
| 评分 | 用户反馈和推荐率 |
| 来源 | 原始仓库位置 |
| 版本 | 最新更新时间 |
| 审计 | 是否有安全审计 |

---

## 安全搜索原则

1. **不跳过审查**：即使高评分技能也要检查
2. **验证来源**：确认原始仓库和作者
3. **检查依赖**：审查依赖项安全性
4. **沙箱测试**：不确定时先在沙箱运行
5. **保持更新**：定期检查已安装技能更新

---

## 快速链接

- skills.sh: https://skills.sh
- Cocoloop: https://hub.cocoloop.cn
- SkillsMP: https://skillsmp.com/zh
- ClawHub: https://clawhub.com
- GitHub Skills Topic: https://github.com/topics/openclaw-skill