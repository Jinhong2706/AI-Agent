---
name: design-lanhu
description: 将蓝湖（Lanhu）设计稿还原为目标框架的像素级组件代码
trigger: 用户提供蓝湖设计稿 URL，或要求还原/导出蓝湖设计图
---

# 蓝湖设计稿还原

将蓝湖（Lanhu）设计稿还原为目标框架代码，包含：获取 Schema JSON、提取 Design Tokens、下载图片资源，最终生成像素级还原的组件代码。

## 使用前提

- Python 3.10+，已安装 `requirements.txt` 依赖（`pip install -r requirements.txt`）
- 环境变量 `LANHU_COOKIE` 已设置，或在调用时通过 `--cookie` 传入

---

## 工作流

### STEP 1 — 列出设计图

```bash
python ${CLAUDE_SKILL_DIR}/scripts/fetch_lanhu.py --url "$LANHU_URL"
```

输出 JSON，包含 `designs` 数组，每项有 `index`（序号）和 `name`（完整名称）。

将列表展示给用户，请用户确认要还原的设计图序号或名称。

---

### STEP 2 — 获取数据

```bash
python ${CLAUDE_SKILL_DIR}/scripts/fetch_lanhu.py \
  --url "$LANHU_URL" \
  --design "$DESIGN_TARGET" \
  --download-images \
  --output-dir "$OUTPUT_DIR"
```

> **禁止主动添加 `--download-code`**。仅当用户明确要求下载官方参考代码时，才在命令末尾追加该标志（该操作耗时较长，且产出仅作结构参考，还原度提升有限）。

- `$DESIGN_TARGET`：序号（如 `1`）或完整名称（如 `首页`）
- `$OUTPUT_DIR`：输出目录，默认 `./lanhu_output`
- 产出文件：
  - `<名称>.schema.json`：图层树和样式数据，是还原代码的**唯一权威来源**
  - `<名称>.tokens.txt`：高风险属性（渐变/阴影/描边/圆角/透明度）
  - `<名称>.official.html`：蓝湖官方生成的 HTML（需加 `--download-code`）
  - `<名称>.official.css`：蓝湖官方生成的 CSS（需加 `--download-code`）
  - `<名称>.png`：设计图原图（仅用于视觉核查）
  - `assets/slices/img_N.png`：Schema 中引用的图片资源
  - `<名称>.image_mapping.json`：本地路径 ← 远程 URL 映射表

---

### STEP 3 — 探测项目环境

读取用户项目根目录下的配置文件来判断框架和样式方案：

| 文件 | 框架 |
|---|---|
| `package.json` 中有 `react` | React / Next.js |
| `package.json` 中有 `vue` | Vue / Nuxt |
| `pubspec.yaml` | Flutter |
| `build.gradle` / `AndroidManifest.xml` | Android |
| `Podfile` / `Package.swift` | iOS / SwiftUI |
| 无法判断 | 默认输出纯 HTML 单文件 |

同时识别样式方案：CSS Modules / Tailwind / SCSS / Styled Components / scoped style 等。

**移动端适配检查（Schema 尺寸 × 项目配置）：**

第一步：从 `<名称>.schema.json` 根节点读取 `designType` 和画板尺寸（`width` / `height`）：

| 判断依据 | 结论 |
|---|---|
| `designType: "mobile"` 或宽度 ≤ 768px | 移动端设计稿，需关注适配方案 |
| `designType: "pc"` 或宽度 > 768px | PC 端，通常无需移动适配 |

第二步：若为移动端设计稿，检查项目中是否已配置适配方案：

| 检查项 | 检查位置 |
|---|---|
| `postcss-pxtorem` / `lib-flexible` / `amfe-flexible` | `package.json` dependencies |
| `vw/vh` 单位或 `postcss-px-to-viewport` | `postcss.config.*` |
| `html { font-size: ... }` 或 `rem` 基准设置 | 全局 CSS / `main.*` / `App.*` |
| `<meta name="viewport" ...>` | `index.html` / 入口模板 |
| Tailwind `screens` 断点配置 | `tailwind.config.*` |

第三步：根据检查结果决定输出单位：

| 项目适配方案 | 代码输出单位 |
|---|---|
| `postcss-pxtorem` / `lib-flexible` | 直接输出 `px`，PostCSS 自动转换 |
| `postcss-px-to-viewport` | 直接输出 `px`，PostCSS 自动转换 |
| 手动 rem 方案（已设 html font-size） | 按基准换算输出 `rem`，换算公式：`px ÷ 基准值` |
| 无任何适配方案 | 输出 `px`，并在组件顶部注释提示项目缺少移动端适配配置 |

**DESIGN.md 设计系统继承（若存在）：**

若项目根目录存在 `DESIGN.md`（或项目文档中明确指定的、承担同一职责的设计说明文件），在解析 Schema、拆分组件与落盘代码前**必须先读取**，并在全流程遵守其中约定。其约束范围不仅限于「当前页的像素还原」，还包括**整个设计系统的延续与统一**，例如：设计令牌与主题、排版与字阶、间距与圆角等刻度、复用组件与变体约定、目录与文件组织、类名与 BEM/框架惯例、无障碍与交互规范等。产出须与项目既有设计体系一致，避免只做孤立页面而割裂系统规范。

与 Schema 的关系：图层级的尺寸、颜色、定位等**具体数值**仍以 `.schema.json` 为唯一权威来源。`DESIGN.md` 负责在**视觉等价**前提下将实现映射到系统 token、既有基础组件与共享样式，并落实 Schema 无法单独表达的系统层规则。若二者在某属性上无法同时满足：优先遵循 `DESIGN.md` 中已写明的冲突处理；若无说明，则以 Schema 数值保证该屏还原度为准，并在答复中简要说明取舍。

---

### STEP 4 — 解析 Schema 并生成代码

读取 `<名称>.schema.json`，递归遍历图层树还原组件代码。

**权威优先级（严格遵守）：**
```
Schema JSON（.schema.json）  >  官方代码（.official.html/.css）  >  Design Tokens（.tokens.txt）  >  设计图原图（.png）
        唯一真相                      结构参考（可选）                      高风险属性补充                    仅目视核查
```

**官方代码的使用方式（若存在 .official.html / .official.css）：**
- **参考元素分组**：查看 `.official.html` 了解蓝湖如何将图层嵌套为 HTML 结构（哪些图层合并为一个容器）
- **参考 CSS 属性完整性**：对照 `.official.css` 检查是否有属性被自己遗漏
- **禁止直接复用**：官方代码使用泛型 class 名（`.group_4`, `.text_28`），不得复制粘贴到目标项目；所有 CSS 数值必须从 `schema.json` 取，不得从 `.official.css` 取（两者数值相同，但 schema 是唯一真相）

**图层类型 → HTML 标签映射：**

| type | 标签 |
|---|---|
| `lanhutext` | `<span>` |
| `lanhuimage` | `<img>` |
| `lanhubutton` | `<button>` |
| 其它 / 容器 | `<div>` |

**以设计图原图为基准，过滤多余叠加层：**

Schema JSON 中可能包含多个交互状态的图层（答题态、答对态、弹层等），但还原目标是**设计图原图（.png）所呈现的那一帧**。生成代码前必须先观察原图，只还原原图中实际可见的内容。

判断流程：
1. 打开 `<名称>.png`，记录原图中肉眼可见的元素。
2. 遍历 Schema 图层，凡图上看不到、或被其他层完全遮住的图层，**直接跳过，不生成任何代码**。
3. 若某层在 Schema 中存在但原图不可见（如被高 z-index 遮罩覆盖的底层内容），亦跳过。

**例外**：用户明确说明当前页面需要遮罩/弹层实现时，才还原对应叠加层。

**组件拆分策略（智能复用，避免过度拆分）：**
- 先按”页面级容器”生成主组件，再判断是否提取子组件；默认不拆分，满足条件才拆。
- 满足以下任一条件可拆分为可复用子组件：
  - 同一页面内出现 **2 次及以上** 的相同结构块（仅文案/图片不同）
  - 明显的 UI 模块：如卡片、列表项、导航栏、底部栏、弹窗、表单行
  - 具有明确业务边界，后续可能独立维护（如 `word-card`、`plan-item`）
- 禁止过度拆分：
  - 纯装饰层（单个背景块、单条分割线、单个图标容器）不要单独拆组件
  - 只出现一次且无复用价值的结构保持在当前组件内
  - 一个子组件内部元素少于 3 个且无交互语义时，优先不拆
- 拆分后要求：保持视觉还原不变，样式数值来源仍以 Schema 为准，不得因抽象导致样式丢失。

**类名语义化与 BEM 规范（CSS/SCSS 必须遵守）：**
- className 必须基于模块语义命名，不使用 `group_1`、`box2`、`text_3` 这类无语义名称。
- 使用 BEM：`block__element--modifier`
  - `block`：页面模块/业务块，如 `word-card`、`study-header`
  - `element`：模块内部元素，如 `word-card__title`、`word-card__image`
  - `modifier`：状态或变体，如 `word-card--active`、`word-card__tag--success`
- 命名规则：
  - 统一小写短横线（kebab-case）
  - 不包含表现词（如 `red`, `big`, `left`），优先业务语义词（如 `status`, `action`, `meta`）
  - 同一语义在全文件保持唯一命名，避免近义重复
- 若使用 CSS Modules/SCSS，也按 BEM 语义组织选择器；仅通过作用域机制隔离，不改变命名语义。

**CSS 属性规则（不得违反）：**
- 所有 CSS 数值**原样复用**，禁止修改、简化、四舍五入
- `rgba(255,115,10,1)` → 不能改为 `#FF730A`
- `linear-gradient(...)` → 不能退化为纯色
- `font-family` → 不能删减或重排 fallback 顺序
- 含 `display:flex` / `flexDirection` 的节点 → 输出 flex 布局
  - `flexDirection: column` → `flex-col` 类 或 `flex-direction: column`
  - `justifyContent: space-between` → `justify-between` 类
- **固定尺寸 + flex 居中容器禁止同时输出 padding**：节点同时满足「有固定 `width`/`height`」+「`display:flex` + `align-items:center` + `justify-content:center`」时，若 Schema 中还有 `padding`，在 `box-sizing:border-box` 下该 padding 会压缩内容区导致文案变形——此时忽略 padding，以 flex 居中作为唯一对齐手段。

**复杂属性专项规则（不得违反）：**
- **多段渐变**：`gradient.colorStops` 有多个 stop 时，必须逐个输出，禁止合并或省略任意一段
  - 示例：`linear-gradient(135deg, rgba(255,100,0,1) 0%, rgba(200,50,0,1) 50%, rgba(150,0,0,1) 100%)`
- **非均匀圆角**：`radius` 是数组（如 `[8, 8, 0, 0]`）时，输出 `border-radius: 8px 8px 0px 0px`（顺序：top-left top-right bottom-right bottom-left）；不得简化为单值
- **叠加阴影**：节点有多个 shadow 对象时，全部输出为 CSS 多值：`box-shadow: 0 2px 4px rgba(...), inset 0 1px 2px rgba(...)`；不得只取第一个
- **opacity + 填充叠加**：节点同时有 `opacity < 100` 和渐变/图片填充时：
  - CSS/HTML：在外层容器加 `opacity: 0.N`，不得把透明度混入颜色值
  - Flutter/SwiftUI：用平台 `Opacity` 组件包裹，不得修改 `LinearGradient` 参数
- **flex gap**：容器节点有 `flexGap` 字段时，输出 `gap: Npx`（或平台等价：Flutter `SizedBox(height/width: N)`，SwiftUI `.spacing(N)`）；不得忽略

**平台单位换算（仅单位，数值不变）：**

| CSS | Flutter | SwiftUI | Android Compose |
|---|---|---|---|
| `px` | 逻辑像素 | `pt` | `dp`（字号用 `sp`） |
| `rgba()` | `Color.fromRGBO()` | `Color(red:green:blue:opacity:)` | `Color(r,g,b,a)` |
| `linear-gradient` | `LinearGradient` | `LinearGradient` | `Brush.linearGradient` |
| `overflow:hidden` | `ClipRect/ClipRRect` | `.clipped()` | `clip()` |
| `position:absolute left/top` | `Stack + Positioned` | `.offset()` | `Modifier.offset()` |

**图片路径：**
- 代码中图片路径使用本地路径（`./assets/slices/img_N.png`）
- 按目标框架格式适配：
  - React/Vue → `import img from '@/assets/slices/img_N.png'`
  - Flutter → `AssetImage('assets/images/img_N.png')`
  - 纯 HTML → `<img src="./assets/slices/img_N.png">`
- 禁止在代码中使用蓝湖 CDN 远程 URL

---

### STEP 5 — 补充 Design Tokens

读取 `<名称>.tokens.txt`，只在 Schema CSS 中**明显缺失**某属性时才补充，不覆盖 Schema 已有值。

重点关注：复杂渐变填充、多层阴影、多边非均匀圆角。

---

### STEP 6 — 还原度核查（不得跳过）

代码生成完成后，逐属性对照 Schema JSON 核查以下 13 项：

1. **尺寸约束**：固定 `height` 不得变成 `min-height` / wrap
2. **裁剪**：`overflow:hidden` 必须在目标平台同步裁剪
3. **颜色值**：`rgba(r,g,b,a)` 转换后数值不得偏移
4. **渐变**：不得退化为纯色；多段渐变所有 color-stop 必须全部输出
5. **绝对定位**：`left`/`top` 坐标值必须原样映射
6. **字体**：`family`、`weight`、`size` 三者全部还原
7. **间距**：每个方向 `margin`/`padding` 数值不得改动；`flexGap` 必须输出为 `gap`
8. **图片资源**：不得被 SVG / CSS 形状 / emoji / 占位图替换
9. **元素完整性**：可见元素必须全部出现在代码中
10. **无远程 URL**：代码中无蓝湖 CDN 地址残留
11. **复杂属性完整性**：非均匀圆角输出 4 值、多层阴影全部保留、opacity 节点未将透明度混入颜色值
12. **组件与命名**：组件拆分不过度且具复用价值；CSS/SCSS 类名语义化并符合 BEM
13. **DESIGN.md（若存在）**：已按文档继承设计系统（令牌、主题、排版刻度、复用组件与目录/命名等），而非仅做单页孤立还原

对每处差异明确说明是「有意的平台适配」还是「错误偏差」，错误偏差必须立即修正。

---

## 变量说明

| 变量 | 说明 |
|---|---|
| `${CLAUDE_SKILL_DIR}` | 由 Claude Code 运行时自动注入，指向本 skill 的 `skill.md` 所在目录的绝对路径 |
| `$LANHU_URL` | 蓝湖设计稿 URL，格式：`https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx` |
| `$DESIGN_TARGET` | 设计图序号或完整名称 |
| `$OUTPUT_DIR` | 数据输出目录（默认 `./lanhu_output`） |
