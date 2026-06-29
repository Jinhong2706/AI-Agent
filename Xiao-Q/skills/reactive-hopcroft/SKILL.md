---
name: reactive-hopcroft
description: >
  公众号文章生成 Skill。根据灵感主题和参考内容，分四步生成文章：
  1) 提取参考内容（支持微信公众号/普通网页）
  2) 标题选择（用户从3-5个选项中选择，标题指引文章方向）
  3) 生成文章初稿（使用 Prompt 模板，注入选定标题）
  4) 去除 AI 写作痕迹（Humanizer-zh 规范）
  
  特点：
  - 总是分步执行，用户有掌控感
  - 标题先行：用户选择的标题指引文章内容方向
  - 每步可干预（换链接、调风格、改结构、选择标题）
  - 支持断点恢复
  
  触发关键词：公众号文章、仿写文章、去 AI 味、humanize、文章生成、微信文章
---

# reactive-hopcroft

公众号文章生成工具 —— 四步工作流：提取 → **标题选择** → 生成 → 去味。

## 核心原则

**总是分步，透明给用户。**

无论参考内容长短，一律分四步执行，每步给用户反馈和控制权。

为什么：
- 用户有掌控感，知道进展
- 用户可在任一步骤干预（换链接、调整风格、修改要点、**选择标题**）
- 中间结果可审查，避免最终输出不符合预期
- **标题先行**：用户选择的标题指引文章内容方向
- 故障可恢复，哪步出问题从哪步重来

## 快速使用

### 标准流程

```
用户: 帮我写一篇关于"AI Agent 对职场的影响"的公众号文章，
      参考这篇 https://mp.weixin.qq.com/s/xxxx

Agent: ✓ 已提取参考内容（微信公众号「xxx」，3500 字）
       主题：AI Agent 对职场的影响
       
       生成标题选项...
       1. 你每天"省下来"的4小时，值1363元——但你把它浪费在复制粘贴上
       2. 一年白扔近9万：这笔账，90%的小老板从没算过
       3. 凌晨3点，他的"员工"还在自动回客户消息
       4. 真正聪明的小老板，从不急着招第一个真人
       5. 凌晨1点，第203条"在的，亲"——一个小老板的24小时
       
       请选择标题（输入数字1-5），或告诉我你的修改：

用户: 2

Agent: 已选择标题："一年白扔近9万：这笔账，90%的小老板从没算过"
       现在生成文章初稿...

Agent: ✓ 初稿已完成（2200 字）
       要点：① 隐性成本计算 ② 重复劳动识别 ③ 自动化替代方案
       需要去 AI 味吗？或者你先看看初稿？

用户: 先去 AI 味吧

Agent: ✓ 去 AI 味完成
       [输出最终文章]
```

### 用户控制点

**提取后**：
- "继续" → 进入**标题选择**步骤
- "换链接" → 重新提取
- "补充文本" → 追加参考内容

**标题选择后**：
- "继续" → 进入生成步骤（使用选定标题）
- "换一批" → 重新生成标题选项
- "自定义" → 用户提供自己的标题

**生成后**：
- "继续" → 进入去 AI 味步骤
- "调整风格" → 修改创作要求，重新生成
- "增减要点" → 补充或删除要点，重新生成
- "改结构" → 调整文章结构，重新生成
- "看看初稿" → 输出完整初稿供审查

**去味后**：
- "完成" → 输出最终文章
- "再改改" → 调整规则，重新去味
- "回到初稿" → 回到生成步骤重新调整

## 技术实现

### Step 1: 提取内容

```python
from skills.reactive_hopcroft.scripts.web_fetcher import fetch_web_content

title, content = fetch_web_content("https://mp.weixin.qq.com/s/xxxx")
# 保存到 workflows/reactive-hopcroft/data/01-extract.json
```

### Step 2: 标题选择

```python
# 基于提取内容和主题，生成 3-5 个标题选项
# 风格覆盖：痛点型、数字型、悬念型、反常识型、故事型

# 用户选择后，保存到 checkpoint
# 选定标题将作为文章生成的核心指引
```

**标题生成原则**：
- 基于提取内容的核心卖点和情感触发点
- 5种风格各1个：痛点型（直击焦虑）、数字型（数据冲击）、悬念型（好奇心）、反常识型（打破认知）、故事型（场景代入）
- 标题选定后，作为 `inspiration_theme` 的一部分注入文章生成 Prompt

### Step 3: 生成文章

```python
from jinja2 import Template

# 读取 Prompt 模板
with open("skills/reactive-hopcroft/references/article-prompt.md") as f:
    prompt_text = f.read()

# 提取 System Prompt 和 User Prompt 模板
system_prompt = extract_system_prompt(prompt_text)
user_template = extract_user_template(prompt_text)

# Jinja2 渲染（注入用户选择的标题）
user_prompt = Template(user_template).render(
    inspiration_theme="一年白扔近9万：这笔账，90%的小老板从没算过",  # 用户选定的标题
    reference_content=content,
    creation_requirements=extract_creation_requirements(prompt_text),
)

# 调用主 Agent 自身 LLM
draft = llm_generate(system_prompt=system_prompt, user_prompt=user_prompt)
# 保存到 workflows/reactive-hopcroft/data/03-draft.md
```

### Step 4: 去 AI 味

```python
# 读取 Humanizer Prompt
with open("skills/reactive-hopcroft/references/humanizer-prompt.md") as f:
    prompt_text = f.read()

system_prompt = extract_system_prompt(prompt_text)
user_template = extract_user_template(prompt_text)

# 渲染
user_prompt = Template(user_template).render(draft_article=draft)

# 调用主 Agent 自身 LLM
final = llm_generate(system_prompt=system_prompt, user_prompt=user_prompt)
# 保存到 workflows/reactive-hopcroft/data/04-final.md
```

## 状态管理

### Checkpoint 文件

`workflows/reactive-hopcroft/state/checkpoint.json`:

```json
{
  "workflow_id": "reactive-hopcroft",
  "version": "1.0",
  "completed_nodes": ["extract", "title_select"],
  "current_node": "generate",
  "started_at": "2026-05-02T12:00:00Z",
  "updated_at": "2026-05-02T12:05:00Z",
  "user_inputs": {
    "theme": "AI Agent 对职场的影响",
    "reference_url": "https://mp.weixin.qq.com/s/xxxx",
    "selected_title": "一年白扔近9万：这笔账，90%的小老板从没算过"
  }
}
```

### 文件读取规则（重要）

主 Agent **严禁直接读取固定编号的文件**（如 `03-draft.md`）。

**正确做法**：
1. 先读取 `checkpoint.json` 获取 `current_node` 和 `completed_nodes`
2. 根据当前步骤，读取对应的文件：

| current_node | 读取文件 | 说明 |
|-------------|---------|------|
| `extract` | `data/01-extract.json` | 展示提取内容，等待用户确认 |
| `title_select` | `data/02-titles.json` | 展示标题选项，等待用户选择 |
| `generate` | `data/03-draft.md` | 展示文章初稿，等待用户反馈 |
| `humanize` | `data/04-final.md` | 展示最终文章，流程结束 |
| `done` | `data/04-final.md` | 流程已完成，展示最终结果 |

**错误示例**：
```python
# ❌ 错误：直接读取固定编号
draft = read("data/03-draft.md")  # 可能是上一次的文件！
```

**正确示例**：
```python
# ✅ 正确：先读 checkpoint，再决定读取哪个文件
cp = json.load(open("state/checkpoint.json"))
current = cp["current_node"]

if current == "generate":
    draft = read("data/03-draft.md")
elif current == "humanize" or current == "done":
    final = read("data/04-final.md")
```

### 强制 Checkpoint 更新规则（关键）

每个步骤完成后，**必须**更新 checkpoint.json。这是防止状态错乱的核心机制。

**更新时机**：
- 步骤成功完成后立即更新
- 文件保存后立即更新（不要等用户响应）
- 用户选择/确认后立即更新

**必须更新的字段**：
```json
{
  "completed_nodes": ["extract", "title_select", "generate"],
  "current_node": "humanize",
  "updated_at": "2026-05-02T13:30:00Z",
  "intermediate_files": {
    "extract": "data/01-extract.json",
    "title_select": "data/02-titles.json",
    "generate": "data/03-draft.md",
    "humanize": "data/04-final.md"
  }
}
```

**编号规则**：
| 步骤 | 文件编号 | 说明 |
|------|---------|------|
| extract | 01 | 第一个步骤 |
| title_select | 02 | 第二个步骤 |
| generate | 03 | 第三个步骤 |
| humanize | 04 | 第四个步骤 |

**严禁**：
- ❌ 复用旧编号（如新生成草稿仍用 `02-draft.md`）
- ❌ 跳过更新（如保存文件后忘记更新 checkpoint）
- ❌ 手动指定编号（必须通过步骤顺序自动确定）

**验证机制**：
每次读取文件前，先验证 `intermediate_files` 中记录的文件是否存在。如果不存在，说明状态已错乱，需要：
1. 报错提示用户
2. 提供重新开始或恢复选项
3. 记录错误日志

### 断点恢复

```
用户: 继续上次的文章

Agent: 检测到上次完成到"标题选择"步骤，已选定标题"一年白扔近9万..."
      现在继续生成文章初稿...
```

## 数据文件

| 文件 | 内容 | 用途 |
|------|------|------|
| `data/01-extract.json` | 提取的标题和正文 | 用户可确认内容 |
| `data/02-titles.json` | 生成的标题选项列表 | 用户选择标题 |
| `data/03-draft.md` | 文章初稿 | 用户可审查修改 |
| `data/04-final.md` | 最终文章 | 最终输出 |

## Prompt 配置

- `references/article-prompt.md` — 文章生成 Prompt（System + User 模板 + 创作要求）
- `references/humanizer-prompt.md` — Humanizer-zh 完整规范（24 类 AI 写作痕迹识别）

## 依赖

- `jinja2` — Prompt 模板渲染
- `requests` — 网页抓取
- `beautifulsoup4` + `lxml` — 网页解析

## 微信文章抓取

支持微信公众号文章链接（`mp.weixin.qq.com`），自动识别并提取：
- 标题：`h1#activity-name`
- 正文：`div#js_content` 内的段落文本

## 可选增强：配图

### 前提条件
- 需要配置 OPENAI_API_KEY 并安装 openai-image-gen 技能

### Step 5: 封面配图（可选）
如环境支持图片生成：
- 调用 openai-image-gen 技能
- 比例 2.35:1（1792x1024）
- 基于选定标题生成

### Step 6: 文章配图（可选）
如环境支持图片生成：
- 1-2张，基于文章关键场景
- 比例 16:9 或 1:1
