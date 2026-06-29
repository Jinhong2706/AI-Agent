#!/usr/bin/env python3
"""Basic validator for design-style-spec.md."""
from __future__ import annotations

import sys
from pathlib import Path

REQUIRED_HEADINGS = [
    "## 1. 项目概述",
    "## 2. 风格锁定摘要",
    "## 3. 版式系统",
    "## 4. 颜色系统",
    "## 5. 字体系统",
    "## 6. 圆角 / 边框 / 阴影 / 质感系统",
    "## 7. 组件清单与状态规则",
    "## 8. 图像 / 图标 / 插画规则",
    "## 9. 响应式与内容伸缩规则",
    "## 10. 后续 Skill 强约束指令",
    "## 11. 高置信 / 推断项说明",
]


def fail(msg: str) -> None:
    print(f"[FAIL] {msg}")
    sys.exit(1)


def main() -> None:
    if len(sys.argv) != 2:
        fail("Usage: validate_style_spec.py <design-style-spec.md>")

    path = Path(sys.argv[1])
    if not path.exists():
        fail(f"File not found: {path}")

    text = path.read_text(encoding="utf-8", errors="ignore")
    missing = [heading for heading in REQUIRED_HEADINGS if heading not in text]
    if missing:
        fail("Missing headings: " + ", ".join(missing))

    for keyword in ["Must Keep", "May Adapt", "Must Not Do"]:
        if keyword not in text:
            fail(f"Missing strong constraint block: {keyword}")

    print("[PASS] Style spec passes basic checks.")


if __name__ == "__main__":
    main()
