#!/usr/bin/env python3
"""
init_skill.py — 新建 Skill 脚手架生成器
用法：python3 scripts/init_skill.py --name <skill-name> --template <basic|multi-scene|data-driven> [--platform workbuddy|openclaw|hermes|universal] [--dest <path>] [--channel lightweight|full] [--interactive]

v3.13.4: SKILL.md 模板新增「文件结构」委托声明 + README.md 自动生成树形结构（解决 create-validate 一致性缺陷）
v3.12.4: 新增 --interactive 对话式采访模式
v3.12.2: 模板从 data/templates/skill-md/ 文件加载，不再硬编码
v3.12.0: 默认自动检测平台，不再假定 WorkBuddy
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))
from scripts.platform import detect_platform

TODAY = datetime.now().strftime("%Y-%m-%d")
_TEMPLATES_DIR = SCRIPT_DIR.parent / "data" / "templates" / "skill-md"

# ── 平台 → 模板文件映射 ─────────────────────────────────────
# OC/HM/UV 的 multi-scene 复用 basic 模板（这些平台不区分模板类型）
_PLATFORM_TEMPLATE_FILES = {
    "workbuddy": {
        "basic": "basic-wb.md",
        "multi-scene": "multi-scene-wb.md",
        "data-driven": "data-driven-wb.md",
    },
    "openclaw": {
        "basic": "basic-oc.md",
        "multi-scene": "basic-oc.md",
        "data-driven": "data-driven-wb.md",  # TODO: 创建 data-driven-oc.md
    },
    "hermes": {
        "basic": "basic-hm.md",
        "multi-scene": "basic-hm.md",
        "data-driven": "data-driven-wb.md",  # TODO: 创建 data-driven-hm.md
    },
    "universal": {
        "basic": "basic-uv.md",
        "multi-scene": "basic-uv.md",
        "data-driven": "data-driven-wb.md",  # TODO: 创建 data-driven-uv.md
    },
}

# 平台 → 默认目标目录
PLATFORM_DEST_DIRS = {
    "workbuddy": "~/.workbuddy/skills/",
    "openclaw": "~/.openclaw/skills/",
    "hermes": "~/.hermes/skills/",
    "universal": "~/.agents/skills/",
}

# ── 采访模式默认值 ─────────────────────────────────────
_INTERACTIVE_DEFAULTS = {
    "template": "basic",
    "channel": "full",
    "platform": None,  # None = 自动检测
}


def _load_template(platform: str, template: str) -> str:
    """从 data/templates/skill-md/ 加载模板文件"""
    platform_map = _PLATFORM_TEMPLATE_FILES.get(platform)
    if platform_map is None:
        raise ValueError(f"不支持的平台: {platform}")
    filename = platform_map.get(template)
    if filename is None:
        supported = list(platform_map.keys())
        raise ValueError(f"平台 {platform} 不支持模板类型 '{template}'，可用: {supported}")
    filepath = _TEMPLATES_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"模板文件不存在: {filepath}")
    return filepath.read_text(encoding="utf-8")


def _fill_skill_md(name: str, display_name: str, desc: str, template: str, platform: str = None, triggers: list = None, author: str = None) -> str:
    """生成 SKILL.md 内容（安全替换，模板中的非占位 {..} 保留原样）

    如果提供了 triggers，会替换模板中的 `triggers: []` 为实际列表。
    如果提供了 author，在 scaffold 行后注入 author 字段。
    """
    if platform is None:
        platform = "universal"
    tmpl_str = _load_template(platform, template)
    # 使用逐键替换而非 str.format()，避免模板中的非占位 {..} 导致 KeyError
    for key, val in {"name": name, "display_name": display_name, "desc": desc}.items():
        tmpl_str = tmpl_str.replace("{" + key + "}", val)
    # 注入 triggers（如果提供）
    if triggers:
        trig_lines = "\n".join(f"  - {t}" for t in triggers)
        tmpl_str = tmpl_str.replace("triggers: []", f"triggers:\n{trig_lines}")
    # 注入 author（如果提供）
    if author:
        tmpl_str = tmpl_str.replace("scaffold: skill-creator-king", f"scaffold: skill-creator-king\nauthor: {author}")
    return tmpl_str


def _build_file_tree(skill_dir: Path) -> str:
    """扫描 skill 目录，生成树形结构字符串（用于 README.md）"""
    skill_dir = skill_dir.resolve()
    lines = [f"{skill_dir.name}/"]
    _walk_tree(skill_dir, skill_dir, lines, "")
    return "\n".join(lines)


def _walk_tree(base: Path, current: Path, lines: list, prefix: str):
    """递归构建树形结构"""
    entries = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    # 过滤 .gitkeep 和隐藏文件
    entries = [e for e in entries if e.name != ".gitkeep" and not e.name.startswith(".")]
    for i, entry in enumerate(entries):
        is_last = (i == len(entries) - 1)
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{entry.name}")
        if entry.is_dir():
            extension = "    " if is_last else "│   "
            _walk_tree(base, entry, lines, prefix + extension)


def _interactive_collect(existing_name: str = None) -> dict:
    """对话式采访模式：在终端逐步收集 skill 元信息。

    Returns:
        dict with keys: name, display_name, desc, triggers, template, platform, channel
    """
    print("🪷 Skill Creator King · 交互式采访")
    print("回答几个问题，生成的 skill 骨架会更丰满。\n")

    # Q1: 名称
    if existing_name:
        name = existing_name
        print(f"1. Skill 名称: {name} (已提供)")
    else:
        name = input("1. Skill 名称 (kebab-case，如 my-skill): ").strip()
        if not name:
            print("❌ 名称不能为空")
            sys.exit(1)
    display_name = name.replace("-", " ").title()

    # Q2: 一句话描述
    desc = input(f"2. 一句话描述它做什么 (回车用默认): ").strip()
    if not desc:
        desc = f"{display_name} — 自动生成的 Skill 骨架"

    # Q2a: Use when 场景采集（自动拼入 description 提升触发精度）
    print("\n💡 描述使用场景可以让 AI 更精准触发你的 skill")
    s1 = input("   场景1（用户说什么时会用到？回车跳过）: ").strip()
    s2 = input("   场景2（回车跳过）: ").strip()
    s3 = input("   场景3（回车跳过）: ").strip()
    use_scenarios = [s for s in [s1, s2, s3] if s]
    if use_scenarios:
        scenarios_str = "，".join(f"「{s}」" for s in use_scenarios)
        desc = f"{desc}。Use when {scenarios_str}。"

    # Q3: 触发词（可选，description 已含场景）
    raw_triggers = input("3. 触发词 (逗号分隔，如 '创建skill,新建skill'，回车跳过): ").strip()
    triggers = [t.strip() for t in raw_triggers.split(",") if t.strip()] if raw_triggers else []

    # Q4: 模板类型
    print("\n4. 模板类型:")
    print("   [1] basic — 单一入口，简单原则")
    print("   [2] multi-scene — 多场景路由，适合复杂工作流")
    print("   [3] data-driven — 数据驱动，含 config.yaml + sources.yaml")
    tmpl_map = {"1": "basic", "2": "multi-scene", "3": "data-driven"}
    tmpl_choice = input("   选 [1/2/3，默认 1]: ").strip()
    template = tmpl_map.get(tmpl_choice, "basic")

    # Q5: 平台
    plat_hint = input("5. 目标平台 [wb=WorkBuddy/oc=OpenClaw/hm=Hermes/uv=Universal，回车自动检测]: ").strip().lower()
    plat_map = {"wb": "workbuddy", "oc": "openclaw", "hm": "hermes", "uv": "universal"}
    platform = plat_map.get(plat_hint, None)  # None = 自动检测

    # Q6: 通道
    ch = input("6. 通道 [full/lightweight，默认 full]: ").strip().lower()
    channel = ch if ch in ("full", "lightweight") else "full"

    # Q7: 展示确认
    print("\n" + "─" * 40)
    print("📋 确认信息:")
    print(f"   名称: {name}")
    print(f"   描述: {desc}")
    print(f"   触发词: {triggers if triggers else '(无)'}")
    print(f"   模板: {template}")
    print(f"   平台: {platform or '自动检测'}")
    print(f"   通道: {channel}")
    print("─" * 40)
    ok = input("确认创建? [Y/n]: ").strip().lower()
    if ok and ok != "y":
        print("已取消。")
        sys.exit(0)

    # Q8: 署名（在确认后，不影响确认信息）
    author = input("\n8. 署名 (公众号/作者名，回车跳过): ").strip() or None

    return {
        "name": name,
        "display_name": display_name,
        "desc": desc,
        "triggers": triggers,
        "template": template,
        "platform": platform,
        "channel": channel,
        "author": author,
    }


def _run_creation_precheck(skill_dir: Path) -> list:
    """生成后反模式预检：在源头提醒已知陷阱，预防比修复便宜。
    
    Returns: 警告消息列表（空 = 无问题）
    """
    warnings = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return warnings
    content = skill_md.read_text(encoding="utf-8")

    # 1. 触发词过短或太泛
    import re as _re
    trig_match = _re.search(r"triggers:\s*\n((?:\s{2,}- .*\n?)*)", content)
    if trig_match:
        triggers_block = trig_match.group(1)
        generic_words = {"帮助", "帮我", "做", "搞", "弄", "来", "去", "改", "修", "查", "help", "do", "make"}
        for line in triggers_block.strip().split("\n"):
            t = line.strip().lstrip("- ").strip().strip('"').strip("'")
            if t and len(t) <= 2:
                warnings.append(f"触发词「{t}」太短（≤2字），容易被其他 skill 误触发")
            elif t and t in generic_words:
                warnings.append(f"触发词「{t}」是高频通用词，建议加限定（如「创建 skill」代替「创建」）")

    # 2. Instructions 段是否仍为模板占位
    body = content.split("---", 2)[-1] if content.count("---") >= 2 else content
    if "待补充" in body or "[第一步]" in body:
        warnings.append("Instructions 段仍含模板占位符（「待补充」/「[第一步]」），建完记得填充")

    # 3. 数据依赖段未填写
    if "数据依赖" in body and "不声明" in body:
        warnings.append("数据依赖段停留在占位状态，完成后应显式声明依赖（或标注「纯内置知识」）")

    # 4. 文件名大小写警告（跨平台坑）
    name = skill_dir.name
    if name != name.lower():
        warnings.append(f"Skill 目录名「{name}」含大写字母，建议全小写 kebab-case（跨平台兼容）")

    return warnings


def create_skill(name: str, template: str, dest: str, channel: str = "full", platform: str = None, triggers: list = None, desc_override: str = None, author: str = None):
    """创建 Skill 脚手架

    Args:
        name: kebab-case 名称
        template: basic/multi-scene/data-driven
        dest: 目标目录
        channel: full/lightweight
        platform: workbuddy/openclaw/hermes/universal
        triggers: 触发词列表（采访模式提供）
        desc_override: 自定义描述（采访模式提供）
        author: 署名（公众号/作者名，可选）
    """
    skill_dir = Path(dest).expanduser().resolve()
    skill_dir.mkdir(parents=True, exist_ok=True)

    display_name = name.replace("-", " ").title()
    desc = desc_override or f"{display_name} — 自动生成的 Skill 骨架"

    # SKILL.md
    skill_content = _fill_skill_md(name, display_name, desc, template, platform, triggers, author)
    (skill_dir / "SKILL.md").write_text(skill_content)

    # README.md（按 readme-standard.md 5 必须段落生成，版本号委托模式）
    trigger_list = "\n".join(f"- {t}" for t in triggers) if triggers else "- 待补充（例如：帮我做XX / create X）"
    readme_content = f"""# {display_name}

> {desc}

## 这是什么

{desc}

## 快速开始

直接对 AI 说触发词即可。无需安装依赖、无需配置。

## 触发方式

{trigger_list}

## 核心能力

- 待补充（每条一个动词开头，说明能做什么）

## 适合谁

- 待补充（描述目标用户画像和使用场景）

## 边界与注意事项

- 待补充（不适用场景、已知限制、依赖前提）

## 资源引用

- [SKILL.md](./SKILL.md) — 完整工作流定义与指令
- [CHANGELOG.md](./CHANGELOG.md) — 版本变更记录

---
平台: {platform or 'auto-detect'}
当前版本见 [SKILL.md](./SKILL.md) frontmatter 或 [CHANGELOG.md](./CHANGELOG.md)。
"""
    (skill_dir / "README.md").write_text(readme_content)

    # CHANGELOG.md
    (skill_dir / "CHANGELOG.md").write_text(
        f"# Changelog\n\n## [0.1.0] - {TODAY}\n\n### Added\n- 初始版本\n"
    )

    # .gitignore — 排除缓存/编译产物/系统文件，同时也是 skillhub-publish 打包白名单
    (skill_dir / ".gitignore").write_text(
        "# Python\n"
        "__pycache__/\n"
        "*.pyc\n"
        ".pytest_cache/\n"
        "\n"
        "# 运行时缓存\n"
        "_cache/\n"
        "\n"
        "# 用户私有数据 / 日志\n"
        "*.jsonl\n"
        "\n"
        "# macOS\n"
        ".DS_Store\n"
        "\n"
        "# Skill 元数据（非发布内容）\n"
        ".skillignore\n"
    )

    # .consistency.yml — 自定义一致性规则（空模板，需要时自行填写）
    (skill_dir / ".consistency.yml").write_text(
        "# .consistency.yml — 自定义一致性规则（可选）\n"
        "# SCK validate 运行时自动加载。规则仅在实际填写后生效。\n"
        "#\n"
        "# 规则类型：\n"
        "#   count_match:       磁盘文件数 = 文档声明数\n"
        "#   cross_reference:   磁盘实体名是否在文档指定段落中出现\n"
        "#   content_count:     源文件内容匹配次数 = 文档声明数\n"
        "#\n"
        "# 详见 SCK 文档或参考科技公众号写作 skill\n"
        "#\n"
        "# custom_rules:\n"
        "#   - type: count_match\n"
        "#     source: \"references/items/*.md\"\n"
        "#     target: \"SKILL.md\"\n"
        "#     match: '(\\d+)'\n"
    )

    # 完整通道：额外生成 DESIGN（合并 WHAT+HOW，v3.14 架构决定）
    if channel == "full":
        (skill_dir / "DESIGN.md").write_text(
            f"# DESIGN.md — {display_name}\n\n"
            f"> 需求规格 + 架构决策。v1 重点：先把 WHAT 写清楚，HOW 可以渐进。\n\n"
            f"版本: 0.1.0\n\n"
            f"## 核心需求（P0 = v1 必做，P1 = v2 考虑）\n\n"
            f"### REQ-001: [一句话描述用户能做什么]\n\n"
            f"**优先级**：[P0/P1]\n"
            f"**验证标准**：[你怎么知道这个功能做好了？给出可检查的标准]\n"
            f"**数据依赖**：[这个需求需要什么数据？本地？网络？API？]\n\n"
            f"### REQ-002: [待定义]\n\n"
            f"---\n\n"
            f"## 非功能需求（按重要性排前 3）\n\n"
            f"| NFR | 约束项 | 目标值 | 原因 |\n"
            f"|-----|--------|--------|------|\n"
            f"| NFR-001 | Token 预算 | L0:200 L1:1100 L2:5000 hard_cap:10000 | 🔒 必须实测，不能猜 |\n"
            f"| NFR-002 | 响应风格 | [中文/英文/简洁/详细/技术向/通俗] | |\n"
            f"| NFR-003 | 安全边界 | [允许的操作 / 禁止的操作] | |\n\n"
            f"---\n\n"
            f"## 架构决策记录\n\n"
            f"### ADR-001: 模板选择\n\n"
            f"**背景**：需要在 basic / multi-scene / data-driven 中选一个。\n"
            f"**决策**：选择 [___] 模板。\n"
            f"**理由**：[___]\n"
            f"**后果**：[这个选择带来的影响——能做什么、不能做什么]\n\n"
            f"### ADR-002: 降级路径\n\n"
            f"**背景**：[什么可能失败？]\n"
            f"**决策**：[失败时如何降级？]\n"
            f"**理由**：[为什么选这个降级方式？]\n"
            f"**❗不可回退**：[是/否。如果降级有数据丢失风险，必须标记]\n"
        )

    # 创建目录（轻量通道跳过，仅 SKILL.md + CHANGELOG.md）
    if channel != "lightweight":
        for d in ["scripts", "references", "tests"]:
            (skill_dir / d).mkdir(exist_ok=True)
            (skill_dir / d / ".gitkeep").touch()

    if template in ("data-driven", "multi-scene"):
        (skill_dir / "data").mkdir(exist_ok=True)
        (skill_dir / "data" / ".gitkeep").touch()

    # 配置和数据源文件
    if template == "data-driven":
        (skill_dir / "config.yaml").write_text(
            "# 配置文件\n# 可调参数与阈值\n"
        )
        (skill_dir / "data" / "sources.yaml").write_text(
            "# 数据源声明\n# 格式见 sources.template.yaml\n"
        )

    # README.md 追加文件树（所有文件创建完毕后生成，确保与实际一致）
    tree = _build_file_tree(skill_dir)
    readme_path = skill_dir / "README.md"
    if readme_path.exists():
        existing = readme_path.read_text(encoding="utf-8")
        readme_path.write_text(existing + f"\n## 文件结构\n\n```\n{tree}\n```\n")

    # ── 反模式预检 ──
    precheck_warnings = _run_creation_precheck(skill_dir)
    if precheck_warnings:
        result = {"success": True, "skill_dir": str(skill_dir), "platform": platform or "auto-detect",
                  "warnings": precheck_warnings}
        print("\n⚠️  生成预检提醒：", file=sys.stderr)
        for w in precheck_warnings:
            print(f"  • {w}", file=sys.stderr)
        return result

    return {"success": True, "skill_dir": str(skill_dir), "platform": platform or "auto-detect"}


def main():
    parser = argparse.ArgumentParser(description="新建 Skill 脚手架")
    parser.add_argument("--name", default=None, help="Skill 名称（kebab-case）。--interactive 模式下可选。")
    parser.add_argument("--template", default="basic", choices=["basic", "multi-scene", "data-driven"],
                        help="Skill 模板类型")
    parser.add_argument("--platform", default=None, choices=["workbuddy", "openclaw", "hermes", "universal"],
                        help="目标平台（默认自动检测）")
    parser.add_argument("--dest", default=None,
                        help="目标目录（默认按平台自动选择）")
    parser.add_argument("--channel", default="full", choices=["lightweight", "full"],
                        help="生成模式（lightweight 仅核心文件）")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--interactive", action="store_true",
                        help="对话式采访模式：逐步询问 skill 描述、触发词、模板、平台等信息")
    parser.add_argument("--author", default=None,
                        help="署名（公众号/作者名），非交互模式使用")

    args = parser.parse_args()

    # ── 交互式采访模式 ──
    if args.interactive:
        info = _interactive_collect(existing_name=args.name)
        # 采访结果覆盖命令行参数
        name = info["name"]
        template = info["template"]
        platform = info["platform"]
        channel = info["channel"]
        triggers = info["triggers"]
        desc_override = info["desc"]
        author = info.get("author")
    else:
        # 非交互模式：name 必需
        if not args.name:
            parser.error("--name 是必需的（或使用 --interactive 进入采访模式）")
        name = args.name
        template = args.template
        platform = args.platform
        channel = args.channel
        triggers = None
        desc_override = None
        author = args.author

    # 自动检测平台
    if platform is None:
        platform = detect_platform(Path.cwd())

    # 路径穿越防护：拒绝含 ../ 或以 / 开头的名称
    if ".." in name or name.startswith("/"):
        print("❌ 非法名称: Skill 名称不能包含 '..' 或以 '/' 开头", file=sys.stderr)
        sys.exit(1)

    # 默认目标目录
    dest = args.dest
    if dest is None:
        base = PLATFORM_DEST_DIRS.get(platform, PLATFORM_DEST_DIRS["universal"])
        dest = str(Path(base).expanduser() / name)

    result = create_skill(name, template, dest, channel, platform, triggers=triggers, desc_override=desc_override, author=author)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"✅ Skill 已创建: {result['skill_dir']}")
        print(f"   平台: {result['platform']}")
        print(f"   模板: {template}")
        print(f"   通道: {channel}")
        if triggers:
            print(f"   触发词: {', '.join(triggers)}")
        if author:
            print(f"   署名: {author}")


if __name__ == "__main__":
    main()
