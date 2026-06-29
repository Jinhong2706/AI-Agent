#!/usr/bin/env python3
"""
文档管理器 - 管理已导入制度文档的全生命周期。

功能:
  - 列出所有已导入文档 (--list)
  - 删除指定文档 (--delete <doc_id>)
  - 更新/重新导入文档 (--update <doc_id> --input <new_file>)
  - 重建索引 (--rebuild)
  - 查看详细统计 (--stats --detail)
  - 导出文档信息 (--export)

用法:
  python doc_manager.py --list
  python doc_manager.py --delete a1b2c3d4
  python doc_manager.py --update a1b2c3d4 --input new_handbook.docx
  python doc_manager.py --rebuild
  python doc_manager.py --stats --detail
"""

import argparse
import json
import os
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"
REGISTRY_FILE = DATA_DIR / "docs_registry.json"
CHUNKS_DIR = DATA_DIR / "chunks"


# ============================================================
# 注册表操作
# ============================================================

def load_registry() -> dict:
    if REGISTRY_FILE.exists():
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"documents": {}, "updated_at": ""}


def save_registry(registry: dict):
    registry["updated_at"] = datetime.now().isoformat()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)


# ============================================================
# 列出文档
# ============================================================

def list_documents(detail: bool = False) -> list[dict]:
    registry = load_registry()
    docs = []
    for doc_id, entry in registry.get("documents", {}).items():
        doc_info = {
            "doc_id": doc_id,
            "name": entry.get("name", ""),
            "category": entry.get("category", ""),
            "file_type": entry.get("file_type", ""),
            "file_size": entry.get("file_size", 0),
            "chunks_count": entry.get("chunks_count", 0),
            "terms_count": entry.get("terms_count", 0),
            "imported_at": entry.get("imported_at", ""),
            "file_path": entry.get("file_path", ""),
            "index_file": entry.get("index_file", ""),
        }
        if detail:
            # 检查索引文件是否存在
            idx_file = entry.get("index_file", "")
            doc_info["index_exists"] = os.path.exists(idx_file) if idx_file else False
            doc_info["file_exists"] = os.path.exists(entry.get("file_path", ""))
        docs.append(doc_info)

    docs.sort(key=lambda d: d["imported_at"], reverse=True)
    return docs


def print_documents(docs: list[dict], detail: bool = False):
    if not docs:
        print("📭 暂无已导入文档")
        return

    print(f"\n📚 已导入文档列表 ({len(docs)} 份):")
    print("=" * 80)
    for d in docs:
        size_kb = d["file_size"] / 1024
        print(f"\n  ● 文档ID: {d['doc_id']}")
        print(f"    名称: {d['name']}")
        print(f"    分类: {d['category']} | 格式: {d['file_type']} | 大小: {size_kb:.1f} KB")
        print(f"    块数: {d['chunks_count']} | 词条数: {d['terms_count']}")
        print(f"    导入时间: {d['imported_at']}")
        if detail:
            idx_ok = "✅" if d.get("index_exists", True) else "❌"
            file_ok = "✅" if d.get("file_exists", True) else "❌"
            print(f"    索引文件: {idx_ok} | 原文文件: {file_ok}")
            if d.get("index_file"):
                print(f"    索引路径: {d['index_file']}")
    print("=" * 80)


# ============================================================
# 删除文档
# ============================================================

def delete_document(doc_id: str, force: bool = False) -> bool:
    registry = load_registry()
    docs = registry.get("documents", {})

    if doc_id not in docs:
        print(f"❌ 文档 ID 不存在: {doc_id}")
        print(f"   可用ID: {list(docs.keys())}")
        return False

    entry = docs[doc_id]
    doc_name = entry.get("name", doc_id)

    if not force:
        print(f"\n⚠️  确认删除文档: {doc_name} ({doc_id})")
        print(f"   此操作将删除索引文件，无法撤销。")
        confirm = input("   输入 'YES' 确认删除: ").strip()
        if confirm != "YES":
            print("   已取消删除。")
            return False

    # 删除索引文件
    index_file = entry.get("index_file", "")
    if index_file and os.path.exists(index_file):
        try:
            os.remove(index_file)
            print(f"   ✓ 已删除索引文件: {index_file}")
        except OSError as e:
            print(f"   ⚠️  删除索引文件失败: {e}")

    # 从注册表移除
    del docs[doc_id]
    save_registry(registry)
    print(f"✅ 文档已删除: {doc_name}")
    return True


# ============================================================
# 更新文档
# ============================================================

def update_document(doc_id: str, new_file_path: str, new_name: str = "") -> bool:
    """重新导入文档，保留 doc_id，更新索引"""
    if not os.path.exists(new_file_path):
        print(f"❌ 文件不存在: {new_file_path}")
        return False

    registry = load_registry()
    docs = registry.get("documents", {})

    if doc_id not in docs:
        print(f"❌ 文档 ID 不存在: {doc_id}")
        return False

    old_entry = docs[doc_id]
    category = old_entry.get("category", "其他制度")
    name = new_name or old_entry.get("name", Path(new_file_path).stem)

    print(f"🔄 更新文档: {name} ({doc_id})")
    print(f"   旧文件: {old_entry.get('file_path', 'N/A')}")
    print(f"   新文件: {new_file_path}")

    # 删除旧索引文件
    old_index = old_entry.get("index_file", "")
    if old_index and os.path.exists(old_index):
        try:
            os.remove(old_index)
            print(f"   ✓ 已删除旧索引")
        except OSError as e:
            print(f"   ⚠️  删除旧索引失败: {e}")

    # 重新导入
    try:
        from doc_importer import import_document
        result = import_document(new_file_path, category, name)
        # import_document 会用新 doc_id，我们需要用旧的
        # 所以手动替换 doc_id
        new_doc_id = result["doc_id"]
        new_registry = load_registry()

        # 把新导入的移到旧 ID 下
        if new_doc_id in new_registry["documents"]:
            new_entry = new_registry["documents"].pop(new_doc_id)
            new_entry["doc_id"] = doc_id
            new_registry["documents"][doc_id] = new_entry
            save_registry(new_registry)

        print(f"✅ 文档更新完成! 块数: {result['chunks']}, 词条数: {result['terms']}")
        return True
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        return False


# ============================================================
# 重建索引
# ============================================================

def rebuild_index(verbose: bool = False) -> dict:
    """重新为所有文档建立索引（用于 jieba 词典更新等情况）"""
    registry = load_registry()
    docs = registry.get("documents", {})

    if not docs:
        print("📭 无已导入文档，无需重建索引")
        return {"rebuilt": 0, "failed": 0}

    print(f"\n🔧 开始重建索引... (共 {len(docs)} 份文档)")
    print("=" * 60)

    rebuilt = 0
    failed = 0
    results = []

    for doc_id, entry in docs.items():
        name = entry.get("name", doc_id)
        file_path = entry.get("file_path", "")
        category = entry.get("category", "其他制度")

        if not file_path or not os.path.exists(file_path):
            print(f"  ⚠️  跳过 {name}: 原文文件不存在 ({file_path})")
            failed += 1
            continue

        if verbose:
            print(f"  ● 处理: {name}...")

        try:
            # 删除旧索引
            old_idx = entry.get("index_file", "")
            if old_idx and os.path.exists(old_idx):
                os.remove(old_idx)

            # 重新导入
            from doc_importer import import_document
            result = import_document(file_path, category, name)

            # 更新 doc_id 保持一致
            new_doc_id = result["doc_id"]
            new_registry = load_registry()
            if new_doc_id in new_registry["documents"]:
                new_entry = new_registry["documents"].pop(new_doc_id)
                new_entry["doc_id"] = doc_id
                new_registry["documents"][doc_id] = new_entry
                save_registry(new_registry)

            rebuilt += 1
            results.append({"doc_id": doc_id, "name": name, "status": "ok",
                            "chunks": result["chunks"], "terms": result["terms"]})
            if verbose:
                print(f"    ✓ 完成: {result['chunks']} 块, {result['terms']} 词条")

        except Exception as e:
            failed += 1
            results.append({"doc_id": doc_id, "name": name, "status": "error", "error": str(e)})
            if verbose:
                print(f"    ❌ 失败: {e}")

    print("=" * 60)
    print(f"✅ 重建完成: 成功 {rebuilt}, 失败 {failed}")

    return {"rebuilt": rebuilt, "failed": failed, "details": results}


# ============================================================
# 统计信息
# ============================================================

def show_stats(detail: bool = False):
    registry = load_registry()
    docs = registry.get("documents", {})

    if not docs:
        print("📭 暂无已导入文档")
        return

    total_docs = len(docs)
    total_chunks = sum(d.get("chunks_count", 0) for d in docs.values())
    total_terms = sum(d.get("terms_count", 0) for d in docs.values())
    total_size = sum(d.get("file_size", 0) for d in docs.values())

    # 分类统计
    cat_stats = defaultdict(lambda: {"count": 0, "chunks": 0, "size": 0})
    for d in docs.values():
        cat = d.get("category", "其他制度")
        cat_stats[cat]["count"] += 1
        cat_stats[cat]["chunks"] += d.get("chunks_count", 0)
        cat_stats[cat]["size"] += d.get("file_size", 0)

    # 格式统计
    type_stats = defaultdict(int)
    for d in docs.values():
        type_stats[d.get("file_type", "unknown")] += 1

    print(f"\n📊 索引统计详情")
    print("=" * 70)
    print(f"  文档总数: {total_docs}")
    print(f"  总块数: {total_chunks}")
    print(f"  总词条数: {total_terms}")
    print(f"  总文件大小: {total_size / 1024:.1f} KB")
    print(f"  最后更新: {registry.get('updated_at', 'N/A')}")

    print(f"\n  分类分布:")
    for cat, stats in sorted(cat_stats.items(), key=lambda x: -x[1]["count"]):
        print(f"    {cat}: {stats['count']} 份, {stats['chunks']} 块, {stats['size']/1024:.1f}KB")

    print(f"\n  格式分布:")
    for fmt, cnt in sorted(type_stats.items(), key=lambda x: -x[1]):
        print(f"    {fmt}: {cnt} 份")

    if detail:
        print(f"\n  索引健康度:")
        idx_ok = sum(1 for d in docs.values() if d.get("index_file") and os.path.exists(d.get("index_file", "")))
        file_ok = sum(1 for d in docs.values() if d.get("file_path") and os.path.exists(d.get("file_path", "")))
        print(f"    索引文件完整: {idx_ok}/{total_docs}")
        print(f"    原文文件存在: {file_ok}/{total_docs}")
        integrity = (idx_ok + file_ok) / (2 * total_docs) * 100 if total_docs else 0
        print(f"    整体完整度: {integrity:.1f}%")

    print("=" * 70)


# ============================================================
# 导出文档信息
# ============================================================

def export_registry(output_file: str) -> bool:
    """导出注册表为 JSON 文件"""
    registry = load_registry()
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    print(f"✅ 注册表已导出到: {output_file}")
    return True


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="员工手册文档管理器")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", "-l", action="store_true", help="列出所有已导入文档")
    group.add_argument("--delete", "-d", metavar="DOC_ID", help="删除指定文档")
    group.add_argument("--update", "-u", metavar="DOC_ID", help="更新指定文档 (需配合 --input)")
    group.add_argument("--rebuild", "-r", action="store_true", help="重建所有文档的索引")
    group.add_argument("--stats", "-s", action="store_true", help="显示统计信息")

    parser.add_argument("--input", "-i", help="更新/导入时使用的文件路径")
    parser.add_argument("--name", "-n", help="更新时指定新名称")
    parser.add_argument("--detail", "-D", action="store_true", help="显示详细信息")
    parser.add_argument("--force", "-f", action="store_true", help="跳过确认提示")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--export", "-e", metavar="OUTPUT", help="导出注册表")
    parser.add_argument("--output", "-o", help="输出结果为 JSON")

    args = parser.parse_args()

    result = {}

    if args.list:
        docs = list_documents(args.detail)
        print_documents(docs, args.detail)
        result = {"documents": docs, "count": len(docs)}

    elif args.delete:
        success = delete_document(args.delete, args.force)
        result = {"deleted": args.delete, "success": success}

    elif args.update:
        if not args.input:
            print("❌ 更新文档需要提供 --input <文件路径>")
            parser.print_help()
            return
        success = update_document(args.update, args.input, args.name or "")
        result = {"updated": args.update, "success": success}

    elif args.rebuild:
        rebuild_result = rebuild_index(args.verbose)
        result = rebuild_result

    elif args.stats:
        show_stats(args.detail)
        result = {"action": "stats", "status": "ok"}

    if args.export:
        export_registry(args.export)

    # 输出 JSON
    if args.output and result:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"📁 结果已保存到: {args.output}")

    # 给调用方输出 JSON
    if not args.output and result:
        print(f"\n[JSON_RESULT] {json.dumps(result, ensure_ascii=False)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
    main()
