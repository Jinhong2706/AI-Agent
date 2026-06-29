#!/usr/bin/env python3
"""
将 fetch_news.py 抓取的 JSON 转为 Markdown 表格
表格列：时间 | 来源 | 排名 | 标题 | 热度 | 简介
"""

import json
import datetime

def render_markdown_table(news_list):
    """生成 Markdown 表格字符串"""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append(f"# 📰 每日热点新闻汇总\n")
    lines.append(f"> 生成时间：{now_str}\n")
    lines.append("| 时间 | 来源 | 排名 | 标题 | 热度 | 简介 |")
    lines.append("|------|------|------|------|------|------|")

    for item in news_list:
        title = str(item.get("标题", "")).replace("|", "｜").replace("\n", " ")
        intro = str(item.get("简介", "")).replace("|", "｜").replace("\n", " ")[:80]
        rank  = item.get("排名", "")
        heat  = item.get("热度", "")
        source = item.get("来源", "")
        time_  = item.get("时间", "")
        lines.append(f"| {time_} | {source} | {rank} | {title} | {heat} | {intro} |")

    return "\n".join(lines)


def main():
    input_path = "/tmp/daily_news.json"
    output_path = "/tmp/daily_news.md"

    with open(input_path, "r", encoding="utf-8") as f:
        news_list = json.load(f)

    md_content = render_markdown_table(news_list)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"✅ Markdown 表格已生成：{output_path}")
    print(f"   共 {len(news_list)} 条新闻")
    return output_path


if __name__ == "__main__":
    main()
