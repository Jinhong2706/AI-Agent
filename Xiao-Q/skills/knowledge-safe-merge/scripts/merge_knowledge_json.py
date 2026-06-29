#!/usr/bin/env python3
import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path


def is_non_empty_string(value):
    return isinstance(value, str) and value.strip() != ""


def make_article_id(article):
    seed = "|".join([
        str(article.get("title", "")).strip(),
        str(article.get("date", "")).strip(),
        str(article.get("content", "")).strip(),
        str(article.get("catId", "")).strip(),
    ])
    return "a" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]


def normalize_category(category, index):
    category = category if isinstance(category, dict) else {}
    return {
        "id": str(category.get("id", index + 1)).strip() or str(index + 1),
        "name": str(category.get("name", f"分类{index + 1}")).strip() or f"分类{index + 1}",
        "desc": str(category.get("desc", "")).strip(),
        "icon": str(category.get("icon", "📚")).strip() or "📚",
    }


def normalize_article(article):
    if not isinstance(article, dict):
        return None

    normalized = dict(article)
    title = str(normalized.get("title", "")).strip()
    content = str(normalized.get("content", "")).strip()

    if not title or not content:
        return None

    normalized["title"] = title
    normalized["content"] = content
    normalized["date"] = str(normalized.get("date", "")).strip()
    normalized["catId"] = str(normalized.get("catId", "1")).strip() or "1"

    raw_id = normalized.get("id", "")
    normalized["id"] = str(raw_id).strip() if raw_id is not None else ""
    if not normalized["id"]:
        normalized["id"] = make_article_id(normalized)

    return normalized


def normalize_data(raw_data, fallback_categories=None):
    if not isinstance(raw_data, dict):
        raise ValueError("JSON 根对象必须是 object")

    fallback_categories = fallback_categories or []

    categories = raw_data.get("categories")
    if isinstance(categories, list) and categories:
        normalized_categories = [normalize_category(item, index) for index, item in enumerate(categories)]
    else:
        normalized_categories = [normalize_category(item, index) for index, item in enumerate(fallback_categories)]

    articles = raw_data.get("articles")
    if not isinstance(articles, list):
        articles = []

    normalized_articles = [item for item in (normalize_article(article) for article in articles) if item]

    return {
        "categories": normalized_categories,
        "articles": normalized_articles,
    }


def build_title_date_key(article):
    return f"title:{article.get('title', '')}|date:{article.get('date', '')}"


def comparable_article(article):
    return json.dumps(article, ensure_ascii=False, sort_keys=True)


def sort_articles(articles):
    return sorted(
        articles,
        key=lambda item: (
            item.get("date", ""),
            item.get("id", ""),
        ),
        reverse=True,
    )


def merge_knowledge_data(current_data, incoming_data):
    merged_articles = [dict(article) for article in current_data["articles"]]

    def rebuild_indexes():
        by_id = {}
        by_title_date = {}
        for index, article in enumerate(merged_articles):
            by_id[article.get("id", "")] = index
            by_title_date[build_title_date_key(article)] = index
        return by_id, by_title_date

    by_id, by_title_date = rebuild_indexes()
    added = 0
    updated = 0
    unchanged = 0

    for incoming_article in incoming_data["articles"]:
        id_index = by_id.get(incoming_article.get("id", ""))
        title_date_index = by_title_date.get(build_title_date_key(incoming_article))
        match_index = id_index if id_index is not None else title_date_index

        if match_index is None:
            merged_articles.append(dict(incoming_article))
            by_id, by_title_date = rebuild_indexes()
            added += 1
            continue

        existing_article = merged_articles[match_index]
        next_article = dict(existing_article)
        next_article.update(incoming_article)
        next_article["id"] = existing_article.get("id") or incoming_article.get("id")

        if comparable_article(existing_article) == comparable_article(next_article):
            unchanged += 1
            continue

        merged_articles[match_index] = next_article
        by_id, by_title_date = rebuild_indexes()
        updated += 1

    merged_categories = incoming_data["categories"] if incoming_data["categories"] else current_data["categories"]

    return {
        "data": {
            "categories": merged_categories,
            "articles": sort_articles(merged_articles),
        },
        "summary": {
            "added": added,
            "updated": updated,
            "unchanged": unchanged,
            "total": len(merged_articles),
        },
    }


def read_json(path):
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path, data):
    target_path = Path(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def timestamp_now():
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def backup_file(path, backup_dir=None):
    source = Path(path)
    if not source.exists():
        return None

    target_dir = Path(backup_dir) if backup_dir else source.parent / ".knowledge-backups"
    target_dir.mkdir(parents=True, exist_ok=True)
    backup_path = target_dir / f"{source.stem}.{timestamp_now()}{source.suffix}"
    shutil.copy2(source, backup_path)
    return backup_path


def parse_args():
    parser = argparse.ArgumentParser(description="安全合并知识库/内容库 JSON，默认保留历史文章。")
    parser.add_argument("--current", required=True, help="当前正式数据源 JSON 路径")
    parser.add_argument("--incoming", required=True, help="待导入的新 JSON 路径")
    parser.add_argument("--output", help="输出 JSON 路径；默认覆盖 current")
    parser.add_argument("--mirror", help="可选：同步写入镜像文件路径")
    parser.add_argument("--backup-dir", help="可选：备份目录路径")
    parser.add_argument("--dry-run", action="store_true", help="仅预演，不写文件")
    return parser.parse_args()


def main():
    args = parse_args()
    current_path = Path(args.current).resolve()
    incoming_path = Path(args.incoming).resolve()
    output_path = Path(args.output).resolve() if args.output else current_path
    mirror_path = Path(args.mirror).resolve() if args.mirror else None

    current_raw = read_json(current_path)
    incoming_raw = read_json(incoming_path)

    current_data = normalize_data(current_raw, current_raw.get("categories", []))
    incoming_data = normalize_data(incoming_raw, current_data.get("categories", []))

    if not incoming_data["articles"]:
        raise ValueError("待导入文件中没有可合并的 articles 数据")

    result = merge_knowledge_data(current_data, incoming_data)

    print(f"当前数据源: {current_path}")
    print(f"导入文件: {incoming_path}")
    print(f"输出文件: {output_path}")
    if mirror_path:
        print(f"镜像文件: {mirror_path}")
    print(f"新增: {result['summary']['added']} 篇")
    print(f"更新: {result['summary']['updated']} 篇")
    print(f"未变化: {result['summary']['unchanged']} 篇")
    print(f"合并后总数: {result['summary']['total']} 篇")

    if args.dry_run:
        print("模式: dry-run（未写入文件）")
        return

    backup_path = backup_file(current_path, args.backup_dir)
    write_json(output_path, result["data"])

    if mirror_path:
        write_json(mirror_path, result["data"])

    if backup_path:
        print(f"备份文件: {backup_path}")
    print("已完成正式写入")


if __name__ == "__main__":
    main()
