---
name: html-ppt-generator
description: "Use this skill to generate PPT presentations from scratch. Triggers when user asks to create a PPT, presentation, slides, deck, \u5E7B\u706F\u7247, \u6F14\u793A\u6587\u7A3F, or any slide-based deliverable. Supports generating from a topic, an outline, or a source document (PDF/text). Produces HTML slides and converts to .pptx."
license: Proprietary
---

# HTML PPT Generator Skill

Generate professional PPT presentations through a 7-stage pipeline. Claude acts as the LLM for all stages, producing HTML slides that are converted to PPTX.

## Quick Reference

| Task | Guide |
|------|-------|
| Generate PPT from topic | Follow full 7-stage pipeline below |
| Generate PPT from document | Read doc first, then follow pipeline with doc as source |
| Generate PPT from outline | User provides outline, skip to Stage 2 with outline mode |

## Dependencies

Before starting, ensure dependencies are installed:
```bash
bash scripts/install_deps.sh
```

## Pipeline Overview

```
Stage 1: Understand Intent  (user query + optional doc -> AnalysisResult XML)
Stage 2: Content Outline    (intent analysis -> page-by-page outline XML)
Stage 3: Design Spec        (intent + outline -> design_request XML)
Stage 4-6: Per Page (serial):
  Stage 4: Page Guide        (outline page + design spec -> layout blueprint)
  Stage 5: Generate HTML     (page guide -> self-contained HTML file)
  Stage 6: Fix HTML          (self-review HTML -> fixed HTML file)
Stage 7: Convert to PPTX    (HTML directory -> .pptx file)
```

---

## Stage 1: Understand User Intent

Analyze the user's query and any attached documents. Output a structured XML analysis.

### Guidelines

You are a senior presentation strategist with 10 years of experience. Analyze the user's input through logical reasoning to restore their true intent.

**Priority rules:**
1. If user explicitly specifies topic, audience, goal, style, page count, or template -> strictly follow, never override
2. If not specified -> infer and recommend based on context

**Analysis dimensions:**
1. **User profile**: Industry, role, knowledge level
2. **Target audience**: Background, focus areas, knowledge level
3. **Core goal**: Education, reporting, fundraising, or showcase?
4. **Tone & style**: Language (formal/humorous/approachable), Visual (minimalist/tech/hand-drawn/retro)
5. **Page count**: If not specified, infer from topic complexity; if specified, strictly follow
6. **Generation mode**:
   - `FileGeneration`: User uploaded documents
   - `OutlineGeneration`: User provided a clear outline with titles and key points
   - `ThemeGeneration`: User only provided a topic and some requirements
7. **Search strategy**: `On` only for ThemeGeneration; `Off` for File/Outline modes

**Page count constraint (hard rule):**
When user explicitly specifies page count (e.g., "one page", "3 pages", "no more than 5"):
- This is a non-negotiable hard constraint
- Never suggest increasing/decreasing pages
- Never use hedging language like "suggest..." in Summary/WritingStrategy
- If content is too much, compress density or drop content, never exceed the limit

### Output Format

Output a single XML structure with root node `<AnalysisResult>`:

```xml
<AnalysisResult>
    <Summary>First-person description of understanding the user's needs.</Summary>
    <WritingStrategy>Detailed writing approach, logical structure, and content focus.</WritingStrategy>
    <fileName>Generated filename (no spaces, use underscores)</fileName>
    <ProjectOverview>
        <TopicName>Full topic name</TopicName>
        <TargetAudience>Target audience</TargetAudience>
        <PresentationGoal>Presentation goal</PresentationGoal>
        <VisualStyle>Visual style</VisualStyle>
        <EstimatedPages>Page count (integer)</EstimatedPages>
        <LanguageTone>Language style</LanguageTone>
        <UserProfiling>User profile inference</UserProfiling>
        <GenerationMode>FileGeneration/OutlineGeneration/ThemeGeneration</GenerationMode>
        <SearchStrategy>On/Off</SearchStrategy>
        <Keywords>keyword1,keyword2,keyword3</Keywords>
    </ProjectOverview>
</AnalysisResult>
```

---

## Stage 2: Generate Content Outline

Based on the intent analysis and source document (if any), design the presentation structure and generate a page-by-page outline.

### Guidelines

You are a top PPT content expert and information architect.

**Core principles:**
1. **Respect facts** - Strictly follow source documents. Never invent numbers, KPIs, dates, names, or contact info
2. **Charts over images** - No bitmap, illustration, or decorative images across the entire document
3. **Follow user intent** - Preserve source document hierarchy; if chaotic, restructure using SCQA model
4. **Purposeful visuals** - Visual elements must aid understanding, not just beautify
5. **Static slides** - No CSS animations, @keyframes, transitions, hover effects
6. **Focus** - Each page defines 1 core focal point (viewpoint/conclusion/key data)

**Presentation structure types:**

Choose from narrative, logical, or modular based on the goal:
- **Narrative**: For pitches, sales, proposals, marketing. Has emotional arc building toward action
- **Logical**: For reports, analysis, tutorials. Well-organized with clear logical flow
- **Modular**: For teaching discrete units, product catalogs. Each module is self-sufficient

**Page roles**: cover, catalog (TOC), content, ending

**Page count logic:**
- Total pages <= 3: Skip cover, TOC, ending. All content pages
- Total pages > 3: Follow standard sequence: cover -> TOC -> content -> ending
- If user specifies content pages, total = specified + structural pages

**Visual guidelines:**
- No data/pure text -> No charts
- 1-2 key values -> Metric cards
- Category comparison -> Bar/column charts
- Trends/sequences -> Line/area charts
- Proportions -> Donut charts
- Multi-dimensional -> Tables
- **Forbidden layouts**: Center-ring, node-connection, network graphs, mind maps (hard to render in HTML)
- **No emoji** unless user explicitly requests them
- Use FontAwesome icons instead

**Layout:**
- Prefer left-right or top-bottom layouts
- Follow F-type or Z-type reading patterns
- Adjust density: too much content -> split pages; too little -> increase whitespace and font size

### Output Format

Output XML with root node `<ppt_outline>`:

```xml
<ppt_outline>
  <page number="1">
    <role>cover</role>
    <title>Main Title</title>
    <content>
      Center layout.
      Large title centered on page.
      Subtitle, presenter name, and date below.
    </content>
  </page>
  <page number="2">
    <role>catalog</role>
    <title>Table of Contents</title>
    <content>
      Left-right asymmetric layout (left 1/3, right 2/3).
      Left: "Contents" title with decorative line.
      Right: Numbered chapter list.
    </content>
  </page>
  <page number="3">
    <role>content</role>
    <title>Key Metrics Overview</title>
    <content>
      Left-text-right-chart layout.
      Left text area (40%): Key conclusion and bullet points.
      Right chart area (60%): Line chart showing growth trend with data source.
    </content>
  </page>
</ppt_outline>
```

---

## Stage 3: Design Specification

Generate a global visual design specification based on the user intent and content outline.

### Guidelines

You are a design expert specializing in slide visual architecture and UI systems.

**Principles:**
1. **CSS variable precision** - Use CSS variables to define visual styles, avoiding ambiguous descriptions
2. **Readability** - Color scheme must have sufficient contrast (WCAG 2.1 compliant)
3. **No naming conflicts** - Use `slide-` prefix for all class names to avoid conflicts with Tailwind CSS

**Design style rules:**
- If user specified a style -> strictly follow it
- If not specified -> infer from intent analysis
- If user mentions a company/organization -> consider their brand colors
- Describe in one concise sentence (< 20 words) a highly distinctive, visually stunning aesthetic
- **Forbidden adjectives**: "clean", "modern", "elegant", "minimalist", "soft", "refined"
- The aesthetic must be immediately recognizable, not generic corporate

**Color system:**
- Background, title, body text, and 1-2 accent colors with hex codes
- Must align with design style and slide content
- Limit to 3-4 colors total

**Typography:**
- Font stack strictly limited to: "SimSun", "SimHei", "Microsoft YaHei", "NSimSun", "KaiTi", "FangSong", "LiSu", "YouYuan", "STZhongsong", "serif", "sans-serif"
- Recommended sizes:
  - Cover: 64px / 32px / 20px
  - TOC: 48px / 28px / 16px
  - Content: 32px / 20px / 16px
  - Ending: 48px / 20px / 16px

### Output Format

Output XML with root node `<design_request>`:

```xml
<design_request>
  <design_style>
    High-contrast description of the visual aesthetic in one sentence.
  </design_style>
  <color_system>
    Background: #XXXXXX
    Primary: #XXXXXX
    Secondary: #XXXXXX
    Accent: #XXXXXX
  </color_system>
  <typography>
    Cover:
    - Title: FontFamily, 64px
    - Subtitle: FontFamily, 32px
    - Body: FontFamily, 20px

    TOC:
    - Title: FontFamily, 48px
    - Chapter title: FontFamily, 28px
    - Description: FontFamily, 16px

    Content:
    - Title: FontFamily, 32px
    - Subtitle: FontFamily, 20px
    - Body: FontFamily, 16px

    Ending:
    - Title: FontFamily, 48px
    - Body: FontFamily, 20px
    - Contact: FontFamily, 16px
  </typography>
</design_request>
```

---

## Stage 4: Page Guide (Per Page)

For each page, generate a precise layout blueprint with pixel-level space budget.

### Guidelines

You are a PPT visual designer and frontend architect specializing in industrial-grade data visualization. Your task is to convert content into a precise "construction blueprint" within a fixed 1280 x 720px canvas. You must follow the "space budget first" principle.

**Canvas spec**: Absolutely fixed 1280px x 720px. No scrollbars allowed.

**Visual design rules:**
- No web UI styles: no rounded corners, no border-emphasized cards, no shadow boxes
- No CSS animations, @keyframes, transitions, hover effects
- Minimize card styles (they fragment the page). No cards on data visualization pages
- Apply colors consistently: use accent sparingly (titles, highlights, key data)
- Ensure visual hierarchy through color contrast
- Keep sufficient whitespace
- Max 2-3 palette colors per slide

**Layout strategy:**
- Unified full-page layout, no fragmentation
- Present only the most important information concisely
- Use typography and spacing to guide reader attention
- Containers should align with each other
- Use grid layout within containers to fill horizontal space
- Use `justify-evenly` to distribute elements

**Icon restrictions:**
- Only FontAwesome Free 6.4.0 icons allowed
- No emoji icons

**Image area handling:**
- No placeholder or external image src allowed
- If no image URL is provided in the outline, use pure CSS to build image areas (e.g., phone mockup with CSS borders and pseudo-elements)

**Chart restrictions:**
- All statistical charts must use ECharts library
- No CSS-drawn charts

### Workflow

1. **Component mapping**: Map all content points to components. 100% mapping, no omissions, no additions. Do NOT add headers/footers if they don't exist in the outline.

2. **Space budget subtraction method**:
   - Determine vertical stack component count (N)
   - Subtract fixed heights (header, footer, safe zones, (N-1) gaps) from 720px
   - Distribute remaining pixels by weight to components

3. **Overflow self-check**:
   - Height closure: Do all vertical values sum to 720px?
   - Content fit: Can the text fit in allocated height?
   - Gap verification: Are gaps deducted in the space budget and not double-counted?

### Output Format

Output two sections:

**1. Construction Checklist** - For each module:
```
[Module A]:
Size: Width Xpx x Height Ypx
Padding: p-Xpx
Visual config: (font size, background hex, border, z-index)

[Module B]:
(same format...)
```

**2. Implementation Notes** (use `slide-` prefix for all class names):
- Core variables: Only list globally reused variables (size/spacing/color)
- Key structure sketch: Skeleton-level HTML/CSS showing component/container relationships (max 1 minimal code block per component, no more than 5 lines)
- Illustration implementation details: Only for explicitly required visual elements

---

## Stage 5: Generate HTML (Per Page)

Generate a complete, self-contained HTML file for each page based on the page guide.

### Guidelines

You are a senior frontend engineer skilled in HTML/CSS, building PPT-aesthetic HTML pages (1280 x 720px) using Tailwind CSS, FontAwesome, and ECharts.

**Core principles:**
1. **Complete HTML** - Self-contained file with all CSS/JS inline (except CDN)
2. **Use `slide-container` as outer container** - No CSS outside it, no padding on it
3. **Fixed 1280 x 720px** - All elements must stay within bounds. Content outside this area becomes invisible in PPT
4. **No Google Fonts** - Never use fonts.googleapis.com

**Required CDN resources (use ONLY these):**
```html
<script src="https://qn.cache.wpscdn.cn/copilot-test/copilot-cdn/js/tailwindcss@3.4.17.js"></script>
<link href="https://qn.cache.wpscdn.cn/copilot-test/copilot-cdn/css/fontawesome-free@6.4.0.css" rel="stylesheet" />
<script src="https://qn.cache.wpscdn.cn/copilot-test/copilot-cdn/js/echarts@5.4.3.min.js"></script>
```

**WARNING: No other JS libraries or CDN resources allowed! Google Fonts, jQuery, Bootstrap, etc. will fail to load.**

**HTML requirements:**
- Use horizontal layout, always limit element heights
- Prefer Tailwind CSS classes over inline styles
- Always provide fixed pixel height/width for images (not percentage or flex)
- Reset all default margins/padding/list-style/text-decoration at the top:
```css
* {
  margin: 0;
  padding: 0;
  list-style: none;
  text-decoration: none;
  box-sizing: border-box;
}
```
- Use `slide-` prefix for class names to avoid Tailwind conflicts
- **Forbidden**: `padding-bottom` (use only `padding-top`), CSS on `body` tag, `overflow: hidden`, `position: absolute` on slide-container, inline SVG, non-existent image paths
- Handle Tailwind Preflight resets: use high-specificity selectors (`.slide-container h1 {}`) and `!important` for critical font sizes

**Visual design:**
- No web UI styles (rounded cards, border emphasis, shadow boxes)
- No CSS animations, @keyframes, transitions, hover effects
- Minimize card styles; forbidden on data visualization pages
- Use accent color sparingly (titles, highlights, key data)
- Max 2-3 palette colors per slide
- Maintain sufficient whitespace

**ECharts:**
- Wrap chart containers in a div with explicit pixel dimensions: `<div id="chartContainer" style="width: 600px; height: 400px;"></div>`
- Max 1 chart per column
- Use palette-derived harmonious colors
- Only use verifiable data; never fabricate numbers
- No radar charts
- No vertical stacking of charts/images

**Tailwind CSS limitations:**
- Used only as pre-compiled utility collection
- No JIT compiler, no tailwind.config, no `text/tailwindcss` style blocks, no `@layer`/`@apply`, no arbitrary non-default classes

**Content quality:**
- All content must be verifiable
- All numerical data from reliable references
- No subjective assessments presented as factual data
- Cite data sources for all charts and statistics

### Output

Write a complete HTML file using the Write tool. File should be named `page_N.html` where N is the page number. Output ONLY the HTML code, no markdown or explanations.

---

## Stage 6: Fix HTML (Per Page)

Self-review the generated HTML and fix any issues found.

### Guidelines

You are an HTML PPT Page Repair Engine. Your role is to precisely fix problems, NOT redesign the page. You are highly sensitive to the Minimal Change Principle.

**Self-review checklist** (review the HTML code you just generated):
1. Does all content fit within 1280x720px? Any overflow?
2. Are all vertical heights summing correctly? Any elements pushed out?
3. Are containers properly sized with no content clipping?
4. Do text blocks fit in their allocated space?
5. Are there any elements overlapping?
6. Are all CDN resources correct (only the 3 allowed)?
7. Is `slide-container` present with no padding?
8. Are class names using `slide-` prefix?
9. Is the CSS reset block present?
10. No forbidden patterns (animations, Google Fonts, inline SVG, padding-bottom)?

**Fix rules (hard constraints):**
- Only modify the minimum code necessary to fix issues
- No new features, no new components
- Do not delete content not explicitly required to be deleted
- Do not change page semantic hierarchy
- Do not introduce style rules not in the design spec
- Do not rephrase or rearrange content unless explicitly needed
- If something wasn't flagged as a problem -> keep it as-is

**Output:** Read the HTML file, review it, and if fixes are needed, use the Edit tool to apply minimal changes. If no issues found, move to the next page.

---

## Stage 7: Convert to PPTX

Convert all HTML files to a single PPTX presentation.

### Command

```bash
python scripts/html_to_ppt.py <html_directory> -o <output.pptx>
```

This will:
1. Find all `page_*.html` files in the directory
2. Render each to PNG using Playwright (headless Chromium)
3. Auto-scale slide content to fit viewport
4. Assemble all PNGs into a 16:9 PPTX presentation

### Output

Return the path to the generated `.pptx` file to the user.

---

## Complete Workflow Example

When the user asks to create a PPT:

1. **Install deps** (first time only): `bash scripts/install_deps.sh`
2. **Create temp directory**: `mkdir -p /tmp/ppt_generation/html_pages`
3. **Stage 1**: Analyze user intent -> output `<AnalysisResult>` XML
4. **Stage 2**: Generate content outline -> output `<ppt_outline>` XML
5. **Stage 3**: Create design spec -> output `<design_request>` XML
6. **For each page** (serial, page 1 through N):
   - **Stage 4**: Generate page guide (construction checklist + implementation notes)
   - **Stage 5**: Write HTML file to `/tmp/ppt_generation/html_pages/page_N.html`
   - **Stage 6**: Self-review and fix the HTML if needed
7. **Stage 7**: Run conversion:
   ```bash
   python scripts/html_to_ppt.py /tmp/ppt_generation/html_pages -o /tmp/ppt_generation/output.pptx
   ```
8. Return the PPTX path to the user

## Notes

- The HTML-to-PPTX conversion method (`scripts/html_to_ppt.py`) is modular and can be replaced with a better method later
- The Fix HTML stage currently uses code-level self-review; it can be upgraded to visual audit (screenshot + vision model) later
- For template/style references, see [templates.md](./templates.md)
