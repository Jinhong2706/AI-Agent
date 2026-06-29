#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
输出格式化辅助脚本 - 统一处理新闻输出格式
"""

import json
import sys
from pathlib import Path

def format_news_as_markdown(news_data, limit=30):
    """将新闻数据格式化为 Markdown"""
    from newsnow import SOURCES
    
    lines = ["# 📰 今日新闻聚合\n"]
    for sid, data in news_data.items():
        name = SOURCES.get(sid, {}).get("name", sid)
        if "error" in data:
            lines.append(f"## ❌ {name}\n\n> 错误: {data['error']}\n")
            continue
        lines.append(f"## ✅ {name} ({sid})")
        for idx, item in enumerate(data.get("items", [])[:limit], 1):
            title = item.get("title", "(无标题)")
            url = item.get("url", "")
            pub_date = item.get("pubDate") or item.get("extra", {}).get("date", "")
            lines.append(f"{idx}. **{title}**")
            if url:
                lines.append(f"   🔗 [链接]({url})")
            if pub_date:
                lines.append(f"   🕐 {pub_date}")
            lines.append("")
    return "\n".join(lines)

def format_news_as_text(news_data, limit=30):
    """将新闻数据格式化为纯文本"""
    from newsnow import SOURCES
    
    lines = []
    for sid, data in news_data.items():
        name = SOURCES.get(sid, {}).get("name", sid)
        if "error" in data:
            lines.append(f"[{name}]  ❌ ERR: {data['error']}")
            continue
        icon = "📦" if data.get("status") == "cache" else "✅"
        lines.append(f"\n{icon} {name} ({sid}) - {len(data.get('items', []))} 条")
        lines.append("─" * 50)
        for idx, item in enumerate(data.get("items", [])[:limit], 1):
            title = item.get("title", "(无标题)")
            url = item.get("url", "")
            pub_date = item.get("pubDate") or item.get("extra", {}).get("date", "")
            line = f"  {idx:2}. {title}"
            if url:
                line += f"\n      🔗 {url}"
            if pub_date:
                line += f"\n      🕐 {pub_date}"
            lines.append(line)
    return "\n".join(lines)

if __name__ == "__main__":
    # 从 stdin 读取 JSON 数据
    input_data = json.loads(sys.stdin.read())
    output_format = sys.argv[1] if len(sys.argv) > 1 else "markdown"
    
    if output_format == "markdown":
        print(format_news_as_markdown(input_data))
    elif output_format == "text":
        print(format_news_as_text(input_data))
    else:
        print(json.dumps(input_data, ensure_ascii=False, indent=2))
