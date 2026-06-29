# 智能推荐策略模板

## 角色判定表

综合已安装 skill 组合和工作区特征推断用户角色。角色搜索词为候选池，排除已被已安装 skill 覆盖的关键词。

| 角色 | 典型 skill 组合 | 工作区特征 | 角色搜索词候选池 | 能力缺口方向 |
|------|---------------|-----------|----------------|-------------|
| 产品经理 | `pptx`+`docx`+`brainstorming` | `.md`/`.docx` 为主 | `product manager`, `prd`, `roadmap` | 竞品分析、用户调研、项目管理 |
| 前端开发 | `ui-*`+`frontend-*`+测试类 | `.tsx`/`.vue`+`package.json` | `frontend`, `react`, `vue` | 测试、部署、设计系统 |
| 后端开发 | `api-*`+`docker-*`+`mock-*` | `.py`/`.go`/`.java`+框架配置 | `backend`, `api`, 具体框架名 | 测试、文档、监控 |
| 全栈开发 | 前后端 skill 混合 | 前后端代码共存 | `fullstack`, 主技术栈名 | 部署、CI/CD、测试 |
| 数据分析师 | `csv-*`+`echarts`+`xlsx` | `.csv`/`.xlsx`/`.sql` 为主 | `data analysis`, `analytics` | 可视化、数据库、BI |
| 设计师 | `ui-*`+`frontend-design` | `.figma`/`.sketch`/设计资产 | `design`, `ui`, `figma` | 原型、动效、图标 |
| 内容创作者 | `writing-*`+`pptx`+`pdf` | `.md`/`.docx` 为主 | `writing`, `content`, `blog` | SEO、发布、排版 |
| 学生/学习者 | `tutor*`+`learning-*` | 多样化文件 | `learning`, `study`, `tutor` | 笔记、知识管理、练习 |

信号不足时标注"通用用户"，跳过角色搜索词。

## Skill → 画像映射表

| 已安装 Skill 模式 | 领域 | 用户倾向 | 搭配推荐词 |
|------------------|------|---------|-----------|
| `ui-*`, `frontend-*`, `css-*` | UI/前端 | 视觉质量 | `component`, `design system`, `testing` |
| `pdf`, `docx`, `pptx`, `xlsx` | 文档处理 | 效率导向 | `report`, `template`, `automation` |
| `csv-*`, `data-*`, `echarts` | 数据分析 | 数据驱动 | `dashboard`, `visualization`, `database` |
| `api-*`, `rest-*`, `graphql-*` | API 开发 | 服务端能力 | `testing`, `documentation`, `mock` |
| `test-*`, `jest-*`, `cypress-*` | 测试 | 质量可靠性 | `ci`, `coverage`, `code review` |
| `docker-*`, `k8s-*`, `deploy-*` | 运维/部署 | 交付稳定性 | `monitoring`, `logging`, `security` |
| `git-*`, `pr-*`, `code-review-*` | 代码协作 | 团队协作 | `documentation`, `automation`, `ci` |
| `skill-writer`, `skill-creator` | Skill 开发 | 工具链构建 | `prompt engineering`, `mcp`, `agent` |

> `skill-assistant` 不作为推荐依据。

### 角色过滤

同一 skill 被不同角色使用时搭配方向不同：
- 产品经理装了 `ui-ux-pro-max` → 搭配 `prototype`, `usability`
- 前端开发装了 `ui-ux-pro-max` → 搭配 `component`, `testing`

## 工作区文件 → 场景推断

### 代码项目

| 文件特征 | 场景 | 推荐方向 |
|---------|------|---------|
| `package.json` + `.tsx` | React 前端 | `react`, `ui`, `testing` |
| `package.json` + `.vue` | Vue 前端 | `vue`, `ui`, `component` |
| `requirements.txt` + `.py` | Python 项目 | `python`, `testing`, `data` |
| `go.mod` + `.go` | Go 项目 | `go`, `api`, `testing` |
| `Dockerfile` | 容器化项目 | `docker`, `deploy`, `ci` |

### 非代码场景

| 文件特征 | 场景 | 推荐方向 |
|---------|------|---------|
| `.md` 为主 | 文档/写作 | `writing`, `documentation`, `notes` |
| `.docx`, `.pptx`, `.pdf` 为主 | 办公文档 | `document`, `template`, `report` |
| `.xlsx`, `.csv` 为主 | 数据分析 | `data`, `visualization`, `dashboard` |

## 项目业务领域推断

按优先级推断：

1. **README.md 项目定位**（P0）
2. **AI 记忆中的项目描述**（P1）
3. **目录名关键词**（P2）
4. **依赖文件**（P3）

> **核心原则**：README.md 告诉你"做什么业务"，目录名和依赖只告诉你"用了什么技术"。冲突时以 README 为准。

### 目录名 → 领域映射

| 目录名关键词 | 业务领域 | 领域搜索词 |
|------------|---------|-----------|
| `agent/`, `skills/`, `prompts/` | AI Agent/LLM | `rag`, `prompt engineering`, `mcp` |
| `auth/`, `login/`, `users/` | 用户系统 | `authentication`, `user management` |
| `payment/`, `billing/` | 支付/交易 | `payment`, `stripe`, `billing` |
| `cart/`, `products/`, `orders/` | 电商 | `ecommerce`, `shop`, `product` |
| `cms/`, `posts/`, `blog/` | 内容管理 | `cms`, `blog`, `content` |
| `chat/`, `messages/` | 即时通讯 | `chat`, `realtime`, `websocket` |
| `ml/`, `models/`, `training/` | 机器学习 | `ml`, `model`, `data science` |
| `infra/`, `terraform/`, `k8s/` | DevOps | `devops`, `infrastructure`, `deploy` |

## 推荐排序规则

1. **业务领域匹配**（权重 6）
2. **角色缺口匹配**（权重 5）
3. **强信号匹配**（权重 4）
4. **记忆驱动**（权重 3）
5. **场景驱动**（权重 2）
6. **热门补充**（权重 1）

## 反模式（禁止）

- ❌ 推荐已安装的 skill
- ❌ 无理由推荐
- ❌ 读取工作区文件内容推断（仅扫描目录和扩展名）
- ❌ 推荐 `skill-assistant` 自身
- ❌ 用自然语言长句作为 CLI 搜索词
- ❌ 忽略工作区特征只搜泛化词
- ❌ 预设用户是开发者
- ❌ 代码项目只推基建（测试、CI），忽略业务领域
- ❌ 用技术栈推断覆盖 README 的业务定位
