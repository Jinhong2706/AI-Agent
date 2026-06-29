# Example Downstream Prompt

请严格基于我提供的以下三个文件继续扩展页面：
- `index.html`
- `design-style-spec.md`
- `design-tokens.json`

要求：
1. 必须沿用现有页面的颜色系统、字体层级、留白节奏、圆角体系、阴影逻辑、卡片语言、图像裁切方式和整体页面气质。
2. 允许根据新内容增减模块，但不得改成另一种模板风格。
3. 先读取 `design-style-spec.md` 理解设计意图，再读取 `design-tokens.json` 复用精确参数，最后参照 `index.html` 保持真实视觉表现。
4. 如果三者出现轻微冲突，以 `index.html` 的视觉表现为最终参照，以 `design-style-spec.md` 的禁改项为风格边界，以 `design-tokens.json` 为精确参数来源。
