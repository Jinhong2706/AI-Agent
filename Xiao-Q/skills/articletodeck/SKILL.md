---
name: article-to-deck
description: 把任意文章或文档内容转换成精美的全屏翻页 HTML 演示文件（幻灯片风格）。当用户发来一篇文章、文档链接、Markdown 内容、或粘贴的文本，并且希望生成演示用的 HTML 时触发。支持任意内容来源：iWiki 链接、KM 链接、本地文件路径、直接粘贴的文本。生成的 HTML 文件保存到本地工作区，并通过企微直接发送给用户。触发词示例：帮我把这篇文章做成PPT、转成演示文档、生成HTML幻灯片、做个演示、转成可以演示的格式、article to deck、make a slide。
---

# Article to Deck

把任意文章内容转换成可直接演示的全屏翻页 HTML 文件。

## 核心流程

### Step 1：读取内容

根据用户提供的内容形式：

- **iWiki 链接 / docid** → 用 `mcporter call iwiki.getDocument` 获取正文
- **KM 链接** → 用 `mcporter call km.show-article` 获取摘要，再用浏览器 skill 抓正文
- **本地文件路径** → 用 `read` 工具读取
- **直接粘贴的文本** → 直接使用，无需额外读取

### Step 2：分析结构，规划分页

把文章内容拆成若干「页」，每页一个主题。规则：

- 每个一级标题（#）或主要章节 → 独立一页
- 章节内容量大 → 可拆成多页（以「承上启下」方式过渡）
- 引子/总结/结语 → 各占一页
- 总页数建议 6-15 页，太少内容单薄，太多演示疲劳

每页需要确定：
1. **页面标签**（左侧导航简短标识，2-4 字）
2. **页面标题**（大标题，显示在页面主体）
3. **内容类型**（正文、列表、对比表格、卡片组、流程步骤、代码块、引言等）
4. **是否需要装饰色块/光晕**

### Step 3：生成 HTML

读取模板文件：`assets/deck-template.html`（本 skill 目录下）

基于模板替换占位符，生成完整 HTML：

- `{{TITLE}}` → 文章标题
- `{{SUBTITLE}}` → 副标题或来源信息
- `{{SLIDES_HTML}}` → 所有 `<section>` 页面的 HTML 拼接
- `{{NAV_DATA}}` → 导航数据 JSON，格式 `[['标签','页面名称'], ...]`

**页面内容构建规则（字体最小 12px，所有尺寸用 clamp/vw/vh）：**

```html
<!-- 标准页框架 -->
<section>
  <div class="glow" style="width:35vw;height:35vw;background:var(--accent);top:-10vh;right:-5vw;"></div>
  <div class="si">
    <div class="tag">章节标识 · 小标签</div>
    <h2 class="ht">主标题 <span class="gtext">关键词高亮</span></h2>
    <!-- 内容区域 -->
  </div>
</section>
```

**常用内容组件（选择最适合内容的形式）：**

| 内容类型 | 使用的 class | 适用场景 |
|---------|------------|---------|
| 要点列表 | `<ul class="pl"><li>` | 并列要点、特性介绍 |
| 对比表格 | `<table class="md-table">` | 优劣对比、方案比较 |
| 卡片组 | `<div class="cg c2/c3"><div class="card">` | 多个并列概念 |
| 流程步骤 | `<div class="fl"><div class="fi"><div class="fd">1</div>` | 操作步骤、流程 |
| 引言金句 | `<div class="qblock">` | 核心观点、引用 |
| 代码示例 | `<div class="cb">` | 代码、命令、示例 |
| 正文段落 | `<p class="bp">` | 说明性文字 |
| 两列布局 | `<div class="cg c2">` | 左右并排内容 |

**视觉规律：**
- 每页只做一件事，不要塞太多内容
- 主标题用 `.gtext` 高亮关键词（渐变色）
- `.tag` 标识章节归属（如「第一章 · 背景」）
- 装饰光晕（`.glow`）增加层次感，位置每页错开

### Step 4：保存文件并发送

1. 将生成的完整 HTML 写入工作区：
   ```
   C:\Users\Administrator\.openclaw\workspace\<文件名>.html
   ```
   文件名：取文章标题的关键词，用连字符连接（如 `okr-deck.html`）

2. 通过企微直接发送文件给用户：
   ```
   MEDIA: C:\Users\Administrator\.openclaw\workspace\<文件名>.html
   ```

3. 附上说明：文件名、页数、演示快捷键（滚轮/方向键翻页，F11全屏，右上角切换背景色）

## 质量检查清单

生成完成前确认：
- [ ] 所有字体 ≥ 12px（用 `clamp(12px, ...)` 而非固定小字号）
- [ ] 页数在合理范围（6-15页）
- [ ] 每页有明确标题和结构
- [ ] 导航数据（`NAV_DATA`）与实际页数一致
- [ ] HTML 语法正确，无未闭合标签

## 模板位置

`assets/deck-template.html`（相对于本 SKILL.md 所在目录）

读取方式：用 `read` 工具加载，替换占位符后写入新文件。
