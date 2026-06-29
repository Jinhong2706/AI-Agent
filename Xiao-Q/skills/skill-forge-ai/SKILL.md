---
name: "skill-forge"
description: "MANDATORY tool for creating SKILLs - MUST be invoked IMMEDIATELY when user wants to create/add any skill. Forges skills through adaptive interview, recursive research, self-validation, and SkillHub peer benchmarking. Do NOT use for editing existing skills, skill security vetting, or general coding tasks."
---

# Skill Forge v3.3

Forges high-quality SKILLs that auto-trigger reliably and produce stable, structured output. Full pipeline: adaptive interview → creation → self-validation (with security check) → SkillHub peer benchmarking.

## When to Use

**CRITICAL: You MUST invoke this skill IMMEDIATELY as your FIRST action when:**
- User wants to create a new skill
- User wants to add a custom skill to the workspace
- User asks to set up a skill template
- User asks "how to create a skill"
- User mentions creating/adding/making any skill

**DO NOT:**
- Just explain how to create a skill without invoking this tool
- Provide manual instructions without calling this skill first
- Defer the skill creation to later steps

## Three Iron Rules

Violating any rule = broken Skill.

**Rule 1: Write Description FIRST** — AI scans all Skill descriptions every conversation. Vague description = never auto-triggers = dead Skill.

**Rule 2: One Skill = One Job** — Don't cram multiple scenarios into one Skill. Multi-purpose Skills trigger chaotically and output inconsistently.

**Rule 3: Keep under 150 lines** — Over 200 lines = AI slows down and accuracy drops. Move detailed docs to `references/` directory.

## SKILL Structure

1. **Directory**: `.trae/skills/<skill-name>/`
2. **File**: `SKILL.md` inside the directory
3. **Optional**: `references/` for detailed docs (keep SKILL.md lean)

## SKILL.md Format

```markdown
---
name: "<skill-name>"
description: "<what it does + when to trigger. Core keywords in first 200 chars>"
---

# <Skill Title>

## 任务
<One sentence: only does X, does NOT do Y or Z>

## 输出格式
<Fixed output structure. Every field format must be concrete, never "organize clearly">

## 规则
<3-5 hard rules. Each must be directly actionable by an intern. Delete all defaults>

## 示例
<One complete input-output pair covering edge cases>
```

## Required Fields

| Field | Location | Description |
|-------|----------|-------------|
| `name` | frontmatter | Unique identifier |
| `description` | frontmatter | **CRITICAL**: (1) what it does + (2) when to invoke + (3) Do NOT scope. Under 200 chars. Keywords FIRST. |
| `detail` | body | 4-module content after frontmatter |

---

## Phase 0: Intent Recognition & Adaptive Interview

**Read [`references/interview-flow.md`](references/interview-flow.md) for the complete interview methodology.** Summary below.

### Step 0.1: Element Check

Scan context for 5 essential elements: **Single scenario / Trigger condition / Output format / Scope boundary / Hard constraints**.

- **≥4 ready** → Confirm with user, skip to Phase 1
- **<4 ready** → Enter Adaptive Interview (Step 0.2)

### Step 0.2: Adaptive Interview (2-5 rounds)

**Read [`references/interview-flow.md`](references/interview-flow.md) NOW** for: interview rules (B1-B6), round-by-round questions, recursive search pattern, and convergence check.

Summary: Each round uses option-first questions (AskUserQuestion, 3 strong + Other) + behavioral probing. After each round: update element checklist, **≥4 clear → proceed to Phase 1**. Max 5 rounds.

---

## Phase 1: Creation

### Step 1: Write Description FIRST

**Format**: `"<What it does>. Invoke when <specific user actions/phrases>. Do NOT use for <exclusions>."`

**Truncation**: Core trigger keywords MUST be in first 200 chars. Tail gets cut at ~250.

### Step 2: Write 4-module content

**任务**: Lock down boundary. State both DOES and DOES NOT.

**输出格式**: Fix output structure. Every field must have concrete format. Never write vague instructions.

**规则**: 3-5 rules only. Must pass **Intern Test**: if an intern can't directly execute it, delete it.

Delete useless rules: "语言简洁" / "保持客观" / "排版整齐" / "代码清晰" / "遵循最佳实践" / "确保输出准确"

**示例**: One complete input-output pair. Input MUST cover edge cases. One good example > 10 abstract rules.

### Step 3: Create directory and file

```bash
mkdir -p .trae/skills/<skill-name>
```

### Step 4: Self-Validation Pipeline

**Step 4a: Schema Check** — Frontmatter name+description ✅ | Description <200 chars ✅ | Trigger keywords first ✅ | Do NOT scope ✅ | 4 modules ✅ | Intern Test ✅ | <150 lines ✅ | Edge case in example ✅

**Step 4a+1: Security Red Line Check** — Scan created SKILL.md for these RED FLAGS. 🚨 If ANY found → REJECT and remove immediately:
- curl/wget to unknown URLs or sends data to external servers
- Requests credentials/tokens/API keys without clear reason
- Reads ~/.ssh, ~/.aws, ~/.config, MEMORY.md, USER.md, IDENTITY.md
- Uses base64 decode / eval() / exec() with external input
- Modifies system files outside workspace or requests sudo permissions
- Obfuscated code (compressed, encoded, minified)
- Accesses browser cookies/sessions or credential files
If clean → proceed to Step 4b. If any red flag → remove, re-validate from Step 4a.

**Step 4b: Trigger Test** — AI generates 3 pos + 3 neg fake questions. Pos not triggering → add keywords. Neg triggering → add Do NOT.

**Step 4c: Dogfood Simulation** — Run example input through rules/format. Check: format match ✅ | rules compliance ✅ | edge cases handled ✅

**Max 3 iterations. After 3, suggest "ship V1 and iterate."**

---

## Phase 2: SkillHub Peer Benchmarking

**Read [`references/benchmarking-guide.md`](references/benchmarking-guide.md) for the complete benchmarking methodology.** Summary below.

### Step 5a: Search & Rank

Call SkillHub API: `https://api.skillhub.cn/api/v1/search?q=<keywords>`. Rank by: `downloads × 0.4 + installs × 0.3 + stars × 0.3`. Take Top 3. CLI fallback if API unavailable.

### Step 5b: Tencent Manual Compliance Comparison

Compare our Skill against Top 3 peers on 9 Tencent Manual dimensions: Description trigger precision / keyword frontloading / Do NOT scope / one-job focus / 4-module structure / output format concreteness / Intern Test rules / edge case coverage / size control.

### Step 5c: Differentiation & Gap Analysis

- Duplicate → recommend installing existing Skill
- Different → document differentiation clearly
- Blind spot → list with Tencent Manual justification

### Step 5d: User Decision

Present results. User chooses: adopt fixes / keep as-is / install existing. **User's decision is final.**

---

## References

- **[`references/interview-flow.md`](references/interview-flow.md)** — Read when entering Step 0.2 (adaptive interview). Contains B1-B6 rules, round templates, recursive search pattern, convergence check.
- **[`references/interview-methods.md`](references/interview-methods.md)** — Read when you need deeper methodology on behavioral probing, bias detection, option design.
- **[`references/benchmarking-guide.md`](references/benchmarking-guide.md)** — Read when entering Phase 2 (SkillHub benchmarking). Contains API usage, quality ranking formula, Tencent 9-dimension comparison template.
- **[`references/meeting-action-extractor-example.md`](references/meeting-action-extractor-example.md)** — Read when creating Step 2 content. Full example of a well-crafted Skill.
