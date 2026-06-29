<div align="center">

# 🎯 DesignLanhu Skill | Pixel-Perfect Lanhu Agent Skill

**Schema is the single source of truth — turn Lanhu designs into maintainable, reviewable production UI**

**design-lanhu | Lanhu Agent Skill | design-to-code | Claude Code | Cursor Skills | pixel-perfect | Design Tokens | Lanhu Schema | DESIGN.md | design system**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Agent Skill](https://img.shields.io/badge/Agent%20Skill-Claude%20%2F%20Compatible-663399.svg)](https://github.com/tiandashu/design-lanhu-skill)
[![HTTPX](https://img.shields.io/badge/HTTPX-Async%20HTTP-009688.svg)](https://www.python-httpx.org/)
[![Lanhu](https://img.shields.io/badge/Platform-Lanhu-FF6A00.svg)](https://lanhuapp.com/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/tiandashu/design-lanhu-skill/pulls)
[![GitHub Stars](https://img.shields.io/github/stars/tiandashu/design-lanhu-skill?style=social)](https://github.com/tiandashu/design-lanhu-skill/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/tiandashu/design-lanhu-skill)](https://github.com/tiandashu/design-lanhu-skill/issues)
[![GitHub Release](https://img.shields.io/github/v/release/tiandashu/design-lanhu-skill?label=release)](https://github.com/tiandashu/design-lanhu-skill/releases)

[简体中文](README.md) | English

[Highlights](#-highlights) • [Features](#-features) • [Quick Start](#-quick-start) • [Usage](#-usage) • [DESIGN.md](#-designmd-design-system-inheritance) • [Artifacts](#-artifacts) • [Lanhu MCP](#-works-with-lanhu-mcp) • [Security](#-security--compliance) • [FAQ](#-faq)

</div>

---

## 🌟 Highlights

**DesignLanhu Skill** is a formal specification for **AI-driven delivery**: pull **Lanhu Schema**, **high-risk visual tokens**, and **slice assets** to your machine, then let an agent generate framework code under explicit engineering rules. This is not “vibe UI” — it is a **measurable, diffable, regression-friendly** pipeline.

🔥 **What makes it different**

- 📐 **Schema as SSOT**: All dimensions, colors, positioning, typography, and layout numbers come from `.schema.json`. Optional official HTML/CSS is for **structure and completeness checks only** — never a license to copy generic class names or “tweak” values.
- 🧩 **Six-stage closed loop**: List → fetch → detect stack & mobile adaptation → codegen from Schema → token gap-fill → **mandatory fidelity checklist** to curb model drift.
- 🎨 **Complex style playbook**: Multi-stop gradients, per-corner radii, stacked shadows, opacity + fills, `flexGap`, flex vs padding conflicts — all spelled out to preserve design semantics.
- 🏗️ **Engineering defaults**: Semantic **BEM**, disciplined component splitting, **local asset paths** (no Lanhu CDN URLs in business code) for reviewability and long-term maintenance.
- 📘 **DESIGN.md inheritance (optional)**: If the **target repo** root has `DESIGN.md` (or an equivalent doc your team names explicitly), the agent **must read it first** before parsing Schema and writing files, mapping implementation to tokens, theme, type scale, shared components, and file/layout conventions under **visual equivalence** — avoiding a one-off page that breaks the system.
- 🔌 **Skill-native, MCP-optional**: Drive everything from one Lanhu URL. Pair with the community [**Lanhu MCP Server**](https://github.com/dsphper/lanhu-mcp) when you need platform-wide collaboration; use this Skill to **land a screen inside your repo**.

🎯 **Best for**

- ✅ **Claude Code, Cursor**, and other clients that support Agent Skills and real-repo workflows.
- ✅ Teams on **React / Vue / Nuxt / Flutter / Android / iOS** who need outputs aligned with CSS Modules, Tailwind, SCSS, etc.
- ✅ Teams that **accept or reject work against Schema**, not guesswork.
- ✅ Repositories with a root **`DESIGN.md`** describing the design system, expecting new Lanhu screens to align with tokens, theme, and component rules.

🎯 **Problems it addresses**

- ❌ **Old way**: Screenshot guessing or copying generic exports — rounded numbers, flattened gradients, hot-linked assets.
- ✅ **New way**: Schema-driven values, token backup, PNG frame alignment, checklist-backed delivery.

---

## 📑 Table of contents

- [Highlights](#-highlights)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [DESIGN.md design system inheritance](#-designmd-design-system-inheritance)
- [Artifacts](#-artifacts)
- [Works with Lanhu MCP](#-works-with-lanhu-mcp)
- [Security & compliance](#-security--compliance)
- [FAQ](#-faq)
- [Disclaimer](#-disclaimer)
- [Keywords](#-keywords)

---

## ✨ Features

### 🎨 Design data acquisition

| Capability | Description |
|------------|-------------|
| Design listing | From a Lanhu stage URL, emit the `designs` list (index + full name) to lock scope |
| Schema fetch | Download layer tree + style JSON — **authoritative numbers** for codegen |
| Design Tokens digest | `.tokens.txt` highlights gradients, shadows, strokes, radii, opacity |
| Local assets | Slices + PNG preview with a local ↔ remote URL map |
| Official export (optional) | `--download-code` for Lanhu HTML/CSS — **reference only**; slower and not a Schema replacement |

### 🤖 Agent workflow (see `SKILL.md`)

- **Stack detection** via `package.json`, `pubspec.yaml`, native project files; fallback to single-file HTML.
- **Mobile adaptation** aligned with Schema `designType`, canvas size, and rem/vw/PostCSS setup.
- **Visibility filtering** against the PNG frame unless the user explicitly wants extra states/overlays.
- **Fidelity audit** after codegen — intentional platform differences vs bugs; if `DESIGN.md` exists, the checklist includes design-system inheritance (see below).

### 📘 DESIGN.md design system inheritance

When the **target project** (the repo where code is written) has **`DESIGN.md`** at the root, or another explicitly named doc with the same role, the agent **must read it before** parsing Schema, splitting components, and writing files, and must follow it end-to-end. Typical coverage:

| Area | Examples |
|------|----------|
| Tokens & theme | Palettes, semantic colors, dark mode, CSS variable naming |
| Type & scale | Type scale, line-height, spacing and radius steps |
| Components | Primitives, variants, when to extract subcomponents |
| Engineering | Folder layout, file naming, BEM/framework conventions, a11y & interaction rules |

**Division of labor vs Schema**

- **Per-layer concrete values** (size, color, position, font size, etc.) remain authoritative in **`.schema.json`**.
- **`DESIGN.md`** maps those values **under visual equivalence** onto design tokens, existing primitives, and shared styles, and encodes global rules Schema alone cannot express.

**Conflicts**

1. If `DESIGN.md` defines how to resolve conflicts → **follow it**.  
2. Otherwise → **prefer Schema for this screen’s fidelity**, and briefly explain the trade-off in the reply.

Full rules and checklist item 13 are in **`SKILL.md`** (STEP 3 / STEP 6).

---

## 🚀 Quick Start

### Requirements

- **Python 3.10+**
- A valid **Lanhu web session cookie** with access to the target project

### Install

```bash
git clone https://github.com/tiandashu/design-lanhu-skill.git
cd design-lanhu-skill
pip install -r requirements.txt
```

### Credentials (pick one)

```bash
export LANHU_COOKIE="your_lanhu_cookie_here"
```

Or copy `.env.example` to `.env`, or pass `--cookie` on the CLI.

> ⚠️ **Note**: Prefer a **vision-capable** model when using this Skill (PNG alignment and complex layouts). Pure text–only models may miss visual acceptance criteria.

### Option A — Claude Code / compatible Skill host (recommended)

1. Install this repo as a Skill (`SKILL.md` at the root).
2. Paste a Lanhu URL, e.g.  
   `https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx`
3. The host injects **`${CLAUDE_SKILL_DIR}`**; the agent runs  
   `${CLAUDE_SKILL_DIR}/scripts/fetch_lanhu.py`  
   through **STEP 1 → STEP 6**.

`SKILL.md` is the **normative** spec for flags, variables, and guardrails.

### Option B — CLI only

**List designs:**

```bash
python scripts/fetch_lanhu.py --url "https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx"
```

**Fetch one design (with images):**

```bash
python scripts/fetch_lanhu.py \
  --url "https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx" \
  --design "1" \
  --download-images \
  --output-dir ./lanhu_output
```

`--design` accepts an **index** or the design **full name**. Add `--download-code` only when explicitly requested.

---

## 📖 Usage

### Example prompt (Skill)

```
Use the design-lanhu skill to implement this screen. Lanhu URL:
https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx
Detect framework and styling from my repo automatically.
```

### Lanhu “design to code”

Enable Lanhu’s **design-to-code** when you want official exports for cross-check; **numbers still come from Schema**. If conversion fails, ask design to upgrade the plugin and re-upload — consistent with guidance in the [Lanhu MCP README](https://github.com/dsphper/lanhu-mcp/blob/main/README.md).

### Using DESIGN.md (recommended for design-system teams)

Keep **`DESIGN.md`** at the **app repo root** with tokens, theme, typography, reusable components, and engineering conventions. When you run this Skill, the agent picks it up and aligns new Lanhu screens with the existing system.

**Example prompt:**

```
Use the design-lanhu skill for this screen. Lanhu URL: …
Read DESIGN.md at the repo root first; prefer tokens and components defined there.
```

---

## 📦 Artifacts

Output directory: `--output-dir` (default `./lanhu_output`).

| File | Role |
|------|------|
| `<name>.schema.json` | **SSOT** for all measurements and style values |
| `<name>.tokens.txt` | High-risk visuals; fill only when Schema is clearly incomplete |
| `<name>.png` | Full frame; align “what is visible now” |
| `assets/slices/img_N.png` | Slices and raster assets |
| `<name>.image_mapping.json` | Local path ↔ remote URL |
| `<name>.official.html` / `.official.css` | Only with `--download-code` — **reference** |

> **Note:** The table above is **local output** from `fetch_lanhu.py`. **`DESIGN.md`** is not generated by the script; you maintain it in the target repo as the **project design-system spec**, which the Skill reads and follows.

---

## 🔗 Works with Lanhu MCP

| | DesignLanhu Skill (this repo) | [Lanhu MCP Server](https://github.com/dsphper/lanhu-mcp) |
|---|--------------------------------|--------------------------------------------------------|
| Shape | Agent Skill + local Python | MCP server + tools |
| Focus | **Pixel rules, multi-framework landing, audit loop** (optional **DESIGN.md** alignment) | Docs/design listing, analysis, team board, collaboration |
| MCP | Not required | Core |

They **complement** each other: MCP for org-wide Lanhu context; this Skill for **shipping a screen into a codebase**.

---

## 🔒 Security & compliance

- ⚠️ **Cookies are credentials** — never commit `.env` or secrets to a public repo.
- 🔐 **Least privilege** — use accounts with only the access you need; rotate cookies regularly.
- 📝 **Data stays local** by default — govern retention and backups per your policy.

---

## ❓ FAQ

<details>
<summary><b>Q: Cookie expired?</b></summary>

Log in again in the browser, copy a fresh `Cookie`, update env or `.env`.
</details>

<details>
<summary><b>Q: UI still doesn’t match?</b></summary>

Check in order: ① numbers from `.schema.json`; ② visible layers vs `.png`; ③ hard cases vs `.tokens.txt` and the checklist in `SKILL.md`.
</details>

<details>
<summary><b>Q: No React/Vue detected?</b></summary>

The Skill falls back to **single-file HTML** when the project type is unknown — see `SKILL.md`.
</details>

<details>
<summary><b>Q: With DESIGN.md, do colors and spacing follow the doc or Schema?</b></summary>

**Concrete layer values** still come from **`.schema.json`** so the screen matches Lanhu; **`DESIGN.md`** maps them under visual equivalence onto tokens, theme variables, and existing components. On conflict, follow conflict rules in `DESIGN.md` if any; otherwise prefer Schema for fidelity and explain the trade-off (see `SKILL.md`).
</details>

---

## ⚠️ Disclaimer

This project is a **third-party open-source skill and script**, **not** an official Lanhu product, and is not affiliated with Lanhu. Use is subject to [Lanhu](https://lanhuapp.com/) terms; ensure you have lawful access to target projects. Authors are not liable for account risk, data loss, or compliance issues arising from use. See the repository license file if present.

---

## 🏷️ Keywords

**English**: Lanhu skill | Lanhu design to code | Agent Skill | Claude Code | pixel-perfect UI | design schema | design tokens | DESIGN.md | design system documentation | token inheritance | frontend codegen | Cursor skills

**中文**: 蓝湖 Skill | 设计稿转代码 | 像素级还原 — see [README.md](README.md) for the full Chinese keyword block.

---

<p align="center">
  If this helps your team, consider starring ⭐️ the repo and sharing it.
</p>

<p align="center">
  <b>DesignLanhu Skill</b> — Schema-first, engineering-grade Lanhu delivery
</p>
