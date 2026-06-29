# html-replica-style-lock-skill

一个可直接上传 GitHub 的完整 Skill 仓库。

它的目标不是“把网页复刻成一个大概差不多的 HTML”，而是：

1. 当用户输入 **网址** 或上传 **网页截图** 时，输出一个 **高保真、可编辑、可运行的 `index.html`**
2. 同时输出一份 **`design-style-spec.md`**，把风格意图、版式逻辑、组件规则、禁改项写清楚
3. 再输出一份 **`design-tokens.json`**，把颜色、字体、尺寸、间距、圆角、阴影、组件参数等做成结构化令牌
4. 最后明确建议用户：把这三份结果交给 `frontend-skill` / `frontend-slides` 一类页面生成 Skill，继续做更多页面，并严格锁定风格

这套 Skill 的核心不是“多输出文件”，而是让 **后续 Skill 真正能继承风格，而不是重新猜风格**。

---

## 适用场景

- 通过 URL 拆解真实网页并复刻为单文件 HTML
- 通过网页截图逆向出高保真可编辑 HTML
- 从截图/网页中抽取可机器复用的设计风格规范
- 将结果交给 `frontend-skill` 继续扩页
- 将结果交给基于 `frontend-slides` 的页面/演示生成 Skill，保持视觉一致

---

## 默认输入

### 1）输入网址

```bash
/use html-replica-style-lock https://example.com
```

### 2）上传截图

```bash
/use html-replica-style-lock
# 然后附上网页截图
```

### 3）同时给网址 + 截图

```bash
/use html-replica-style-lock https://example.com
# 同时附上截图，要求以截图视觉为准
```

---

## 默认输出

除非用户明确要求其他格式，否则每次只输出：

1. `index.html`
2. `design-style-spec.md`
3. `design-tokens.json`
4. 一段推荐语：建议把这三份文件交给 `frontend-skill` / `frontend-slides` 严格锁定风格继续扩页

> 不默认输出 `ppt-style-guide.md`、`reconstruction-notes.md`、截图分析报告、额外 JSON 等冗余文件。

---

## 仓库结构

```text
html-replica-style-lock-skill/
├── .gitignore
├── README.md
├── SKILL.md
├── references/
│   ├── source_prompt_cn.md
│   ├── reverse_engineering_framework.md
│   ├── style_lock_principles.md
│   ├── downstream_handoff_protocol.md
│   ├── design_style_spec_contract.md
│   └── design_tokens_contract.md
├── templates/
│   ├── design-style-spec-template.md
│   ├── design-tokens-template.json
│   ├── replica-page-template.html
│   └── downstream-handoff-message-template.md
├── scripts/
│   ├── validate_html_output.py
│   ├── validate_style_spec.py
│   └── validate_design_tokens.py
└── examples/
    ├── example_requests.md
    ├── example_output_structure.md
    └── example_frontend_handoff_prompt.md
```

---

## 为什么这版更适合“风格完美继承”

只给 HTML 不够，因为后续 Skill 很容易：

- 把颜色“差不多”改掉
- 把字体层级换成自己默认模板
- 把留白和节奏做坏
- 把高级灰做成廉价营销风
- 把极简界面做成科技炫技页

所以这版强制使用两层规范：

### 1）`design-style-spec.md`：表达 **设计意图与风格约束**
它负责告诉后续 Skill：
- 这个页面为什么长这样
- 哪些视觉特征是不可变锚点
- 哪些内容可以扩展
- 哪些错误绝对不能犯

### 2）`design-tokens.json`：表达 **机器可直接复用的精确参数**
它负责告诉后续 Skill：
- 颜色值是多少
- 字号、行高、字重是多少
- 卡片圆角和阴影怎么配
- 间距与容器宽度怎么配
- 按钮、标签、导航等组件的关键参数是什么

这两个文件一起输出，后续 Skill 才最不容易跑偏。

---

## 最佳工作流

推荐你这样串联：

1. 用 `html-replica-style-lock` 输入网址或截图
2. 拿到 `index.html`、`design-style-spec.md`、`design-tokens.json`
3. 把这三份文件交给 `frontend-skill`
4. 明确要求：**严格锁定现有风格，不得自作主张替换风格语言**
5. 如果需要演示页面或多页排版，再交给基于 `frontend-slides` 的 Skill 继续做页面

---

## 安装方式

把整个目录放入你的 Skills 目录，例如：

```bash
skills/html-replica-style-lock-skill/
```

确保 `SKILL.md` 在根目录。

---

## 设计目标

这套 Skill 不是为了“生成更多东西”，而是为了做出一个：

- **高保真 HTML 基准页**
- **高约束风格规范**
- **高精度设计令牌**

后续页面要想和用户期望高度一致，必须以这三份结果为基准继续扩展，而不是重新从图片或描述猜风格。
