#!/usr/bin/env python3
"""manifest.yaml 原子读写 helper

两个函数：
  * write_manifest_atomic(path, data) — 写到 .tmp + fsync + POSIX rename，断电安全
  * read_manifest_safe(path)         — 读 manifest，发现残留 .tmp 时提示用户

CLI：
  python manifest_io.py write <manifest.yaml> <data.json>   # 把 data.json 原子写到 manifest.yaml
  python manifest_io.py read  <manifest.yaml>               # 安全读，stdout 返回 yaml 内容；存在残留 .tmp 时打 stderr 警告

设计动机见 references/manifest-schema.md §atomic write。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:
    print("[manifest_io] 缺少 PyYAML，请 pip install pyyaml", file=sys.stderr)
    sys.exit(2)

# workspace 路径合法性校验（与 resolve_workspace.py 共用同一逻辑）
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from resolve_workspace import validate_workspace_path  # type: ignore  # noqa: E402
finally:
    if str(Path(__file__).parent) in sys.path:
        sys.path.remove(str(Path(__file__).parent))


def write_manifest_atomic(
    path: Path,
    data: dict,
    *,
    skip_workspace_validation: bool = False,
) -> None:
    """原子写 manifest：.tmp + fsync + rename。

    任何写 manifest 的入口（CLI / 主 Agent / 子脚本）都必须走这里。
    直接 path.write_text(...) 在 IDE 崩溃 / Ctrl-C / 断电时机会留下半截 yaml。

    写入前校验 data["workspace_root"] 路径合法性——
    防止"凭直觉建 <skill>-workspace/ 然后写 manifest"的事故复现。
    layout 从 data["preferences"]["workspace"]["layout"] 推断，缺省 sibling_of_skills_dir。
    设 skip_workspace_validation=True 可跳过（仅供单元测试）。
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    workspace_root = data.get("workspace_root")
    if workspace_root and not skip_workspace_validation:
        layout = (
            data.get("preferences", {})
            .get("workspace", {})
            .get("layout", "sibling_of_skills_dir")
        )
        ok, reason = validate_workspace_path(workspace_root, layout)
        if not ok:
            raise ValueError(
                f"[manifest_io] workspace_root 路径不合法，拒绝写入：\n"
                f"  path: {workspace_root}\n"
                f"  layout: {layout}\n"
                f"  reason: {reason}\n"
                f"  → 请用 `python3 scripts/resolve_workspace.py --skill <skill_path>` "
                f"重新解析后再写。"
            )

    tmp = path.with_suffix(path.suffix + ".tmp")  # manifest.yaml.tmp
    payload = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)

    with open(tmp, "w", encoding="utf-8") as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())

    tmp.replace(path)


def read_manifest_safe(path: Path, *, on_stale_tmp: str = "warn") -> dict | None:
    """安全读 manifest。

    on_stale_tmp:
      - "warn"  (默认): 残留 .tmp 时 stderr 警告但仍返回正常 manifest
      - "raise":        残留 .tmp 时抛 RuntimeError
      - "ignore":       静默忽略（不推荐，违反 NEVER 静默吃 .tmp 规则）
    """
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")

    if tmp.exists():
        msg = (
            f"[manifest_io] 检测到残留 {tmp.name}（上次写入未完成）。\n"
            f"  - {path.name} 是否存在: {path.exists()}\n"
            f"  - 选择: 是否要把 {tmp.name} 当作权威版本（要承担数据不完整的风险）？\n"
            "  → 直接由用户决定；本 helper 默认仍读 manifest.yaml，不静默吃 .tmp。"
        )
        if on_stale_tmp == "raise":
            raise RuntimeError(msg)
        if on_stale_tmp == "warn":
            print(msg, file=sys.stderr)

    if not path.exists():
        return None

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _cli() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub_w = sub.add_parser("write", help="原子写 manifest")
    sub_w.add_argument("path", type=Path)
    sub_w.add_argument("data_json", type=Path, help="JSON 文件（内容会作为 dict 写入 manifest）")

    sub_r = sub.add_parser("read", help="安全读 manifest")
    sub_r.add_argument("path", type=Path)
    sub_r.add_argument("--strict", action="store_true", help="残留 .tmp 时抛错而非警告")

    args = ap.parse_args()

    if args.cmd == "write":
        with open(args.data_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        write_manifest_atomic(args.path, data)
        print(f"[manifest_io] atomic write OK → {args.path}", file=sys.stderr)
        return 0

    if args.cmd == "read":
        data = read_manifest_safe(args.path, on_stale_tmp="raise" if args.strict else "warn")
        if data is None:
            print(f"[manifest_io] manifest 不存在: {args.path}", file=sys.stderr)
            return 1
        yaml.safe_dump(data, sys.stdout, allow_unicode=True, sort_keys=False)
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(_cli())
