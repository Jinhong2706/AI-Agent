# 成果卡片生成（Result Card）

> 融合自 darwin-skill 的 Result Card 概念，重写为 skill-assistant 品牌
>
> **触发时机**：仅在用户主动选择 `[2] 生成可视化成果卡片 PNG` 时执行。**默认不自动生成**——避免每次评测都消耗截图资源。

---

## 输出位置

| 来源 | 默认输出路径 |
|------|------|
| inspect 单 skill 报告 | `.skill-doctor/{skill-name}/inspect-card-{YYYYMMDD-HHMM}.png` |
| inspect batch_baseline | `.skill-doctor/_batch/baseline-card-{YYYYMMDD-HHMM}.png` |
| diagnose Step 5 优化收尾 | `.skill-doctor/{skill-name}/result-card-{YYYYMMDD-HHMM}.png` |

如目录不存在则自动创建。

---

## 三种数据模式

| mode | 显示什么 | 适用场景 |
|------|---------|---------|
| `single` | 仅当前评分 + 维度速览 + 关键发现 | inspect 一次性质检报告 |
| `iter` | 前后对比（含 delta badge + 维度涨跌） | diagnose 棘轮迭代收尾 |
| `hybrid` | 静态分 + 动态分双轨独立 + 综合判断 | inspect 的 hybrid 评测 |

---

## 调用流程（Agent 执行步骤）

### 1. 准备数据 JSON

把当前评测/优化数据写入临时 JSON 文件，例如 `.skill-doctor/{skill-name}/.card-data.json`：

```json
{
  "mode": "iter",
  "skill_name": "target-skill",
  "skill_id": ".cursor/skills/target-skill",
  "card_title": "Skill 进化报告",
  "card_mode": "Iteration",
  "date": "2026.04.28",
  "score_before": 72,
  "score_after": 87,
  "grade": "B+ 良好",
  "dims": [
    { "name": "指令", "from": 5, "to": 9, "weight": "hot" },
    { "name": "约束", "from": 5, "to": 8, "weight": "hot" },
    { "name": "冗余率", "from": 6, "to": 8, "weight": "warm" },
    { "name": "D0 知识增量", "from": 7, "to": 8 },
    { "name": "D1 元数据", "from": 6, "to": 8, "weight": "warm" },
    { "name": "D5 反模式", "from": 7, "to": 8 },
    { "name": "D7 渐进披露", "from": 7, "to": 7 },
    { "name": "D10 可验证", "from": 3, "to": 8, "weight": "hot" }
  ],
  "summary": [
    "补充了 NEVER 列表 + WHY，约束维度从 5 升到 8",
    "description 加入触发词与 WHEN，可发现性显著提升",
    "新建 test-prompts.json，从此可进入 diagnose 棘轮闭环"
  ],
  "footer_url": "iwiki.woa.com/p/4019623347",
  "footer_by": "Powered by skill-assistant"
}
```

### 2. 调用渲染脚本

```bash
node .cursor/skills/skill-assistant/scripts/render-card.mjs \
  .skill-doctor/{skill-name}/.card-data.json \
  .skill-doctor/{skill-name}/result-card-{timestamp}.png
```

脚本会自动：
1. 读取模板 `templates/result-card.html`
2. 替换 `data-field` 占位符
3. 用 Playwright 启动 Chromium，2x 高清截图（仅截 `.card` 元素）
4. macOS 上自动 `open` 打开图片

### 3. 反馈用户

```
✨ 成果卡片已生成

  文件：.skill-doctor/target-skill/result-card-20260428-1042.png
  尺寸：1800 × 1280 px（2x 高清）
  已自动打开。可上传到群里 / iWiki / 微信分享

→ [1] 生成另一种模式的卡片（single / hybrid）
  [2] 完成
```

---

## 数据字段映射规则

`data-field="xxx"` 占位符 ↔ JSON 字段：

| HTML data-field | JSON key | 说明 |
|---|---|---|
| `card-title` | `card_title` | 主标题（如"Skill 进化报告" / "质量评测卡片"） |
| `card-mode` | `card_mode` | 顶部 Mode Tag（如 "Iteration" / "Audit" / "Hybrid"） |
| `date` | `date` | 日期，格式 `YYYY.MM.DD` |
| `skill-name` | `skill_name` | Skill 名（卡片主标） |
| `skill-id` | `skill_id` | Skill 路径或 ID |
| `score-before` | `score_before` | 优化前分数（`single` 模式可省略） |
| `score-after` | `score_after` | 当前分数 |
| `score-delta` | 自动计算 | `score_after - score_before`，带正负号 |
| `grade` | `grade` | 等级文本（如"B+ 良好"） |
| `static-score/grade/note` | `static_*` | 仅 hybrid 模式 |
| `dynamic-score/grade/note` | `dynamic_*` | 仅 hybrid 模式 |
| `dim{1-8}-name/from/to/delta` | `dims[]` | 维度数组（最多 8 项） |
| `summary-{1-4}` | `summary[]` | 关键改进/发现（最多 4 条） |
| `footer-url` | `footer_url` | 底部右下链接 |
| `footer-by` | `footer_by` | 底部署名 |

---

## 维度配色（CSS class）

| 配色 weight 值 | 视觉效果 | 何时使用 |
|---|---|---|
| `hot`（默认涨幅 ≥ 3）| 靛蓝高亮 + 边框 | 突破性提升 / 单 skill 评分中的最低分维度 |
| `warm`（涨幅 1-2）| 浅紫底 | 中等改进 |
| 无 weight（涨幅 0 或负）| 灰底 | 持平或下降 |

`render-card.mjs` 不会自动判断 weight——由 Agent 在生成 JSON 时决定，遵循以下默认规则：
- `to - from >= 3` → `hot`
- `to - from in [1, 2]` → `warm`
- `to - from <= 0` → 不设置（用默认灰底）

---

## 异常处理

| 场景 | 处理 |
|------|------|
| Playwright 未安装 | 脚本退出码 1，提示安装命令；Agent 应建议用户先 `npm i -g playwright && npx playwright install chromium` |
| 模板文件丢失 | 脚本退出码 1；Agent 应提示重新安装 skill-assistant |
| 数据 JSON 字段不全 | 缺失字段保留模板默认占位符（不报错），但建议 Agent 在生成 JSON 时补齐核心字段 |
| 输出目录不存在 | Agent 自己负责 `mkdir -p`，脚本不创建目录 |
| 非 macOS 系统 | 跳过 `open` 自动打开，仅打印输出路径让用户手动查看 |

---

## NEVER 规则

- **NEVER 默认自动生成卡片** — 必须用户主动从菜单选择 `[2]`
- **NEVER 用 inspect static 模式的数据生成 hybrid 卡片** — 缺动态分会让卡片半空，应降级为 `single` 模式
- **NEVER 修改 templates/result-card.html 原文** — 渲染脚本用临时文件，保持模板可复用
- **NEVER 把卡片 PNG 提交到 Skill 的 git 仓库** — 输出到 `.skill-doctor/` 应被 `.gitignore` 排除
