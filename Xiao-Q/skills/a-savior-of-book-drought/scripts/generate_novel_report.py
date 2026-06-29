#!/usr/bin/env python3
"""
Novel Recommendation Report Generator
Read novels_data.json and generate an interactive HTML recommendation report.

Usage:
    python generate_novel_report.py --data novels_data.json --output ./novel_report
"""

import argparse
import json
import os
import sys
from pathlib import Path


def star_html(score, max_score=10):
    """Generate star rating HTML. Score is 0-10, displayed as 0-5 stars."""
    stars_5 = score / 2  # Convert 10-scale to 5-scale
    full = int(stars_5)
    half = 1 if stars_5 - full >= 0.3 else 0
    empty = 5 - full - half
    return ("*" * full) + ("+" * half) + ("-" * empty)


def generate_report(data, output_dir):
    """Generate the HTML report."""
    profile = data.get("user_profile", {})
    novels = data.get("novels", [])
    picks = data.get("picks", {})
    extras = data.get("extras", [])

    # Profile section
    profile_items = ""
    for key, label in [("genre", "Type"), ("taste", "Taste"), ("length", "Length"),
                        ("status", "Status"), ("reference", "Reference")]:
        val = profile.get(key, "")
        if val:
            profile_items += f'<div class="profile-tag"><span class="tag-label">{label}</span> {val}</div>'

    # Novel cards
    cards_html = ""
    for i, novel in enumerate(novels):
        rating = novel.get("rating", {})
        score = rating.get("score", 0)
        score_src = rating.get("source", "")
        score_count = rating.get("count", "")
        status_badge = "DONE" if novel.get("status", "") in ("complete", "completed") else "ONGOING"
        status_cls = "badge-done" if status_badge == "DONE" else "badge-ongoing"

        # Highlights
        hl_html = ""
        for h in novel.get("highlights", []):
            hl_html += f'<span class="hl-tag">{h}</span>'

        # Caveats
        cav_html = ""
        for c in novel.get("caveats", []):
            cav_html += f'<div class="caveat">[!] {c}</div>'

        # Reader quotes
        quotes_html = ""
        for q in novel.get("reader_quotes", []):
            quotes_html += f"""<blockquote class="reader-quote">
                <p>&ldquo;{q.get('text', '')}&rdquo;</p>
                <cite>-- {q.get('source', 'Reader')}</cite>
            </blockquote>"""

        # Read links
        links_html = ""
        for lnk in novel.get("read_links", []):
            links_html += f'<a href="{lnk.get("url", "#")}" class="read-link" target="_blank">{lnk.get("platform", "Read")}</a>'

        # Similar
        similar = ", ".join(novel.get("similar_to", []))

        cards_html += f"""
        <div class="novel-card" id="novel-{i}">
            <div class="novel-header">
                <div class="novel-cover" style="background: linear-gradient(135deg, hsl({(i*47)%360}, 35%, 35%), hsl({(i*47+40)%360}, 45%, 25%));">
                    <span class="cover-title">{novel.get('title', '')}</span>
                    <span class="cover-author">{novel.get('author', '')}</span>
                </div>
                <div class="novel-meta">
                    <h3 class="novel-title">{novel.get('title', '')}</h3>
                    <div class="novel-author">{novel.get('author', '')}</div>
                    <div class="novel-tags">
                        <span class="genre-tag">{novel.get('genre', '')}</span>
                        <span class="status-badge {status_cls}">{novel.get('status', '')}</span>
                        <span class="wc-tag">{novel.get('word_count', '')}</span>
                    </div>
                    <div class="novel-rating">
                        <span class="rating-score">{score}</span>
                        <span class="rating-source">{score_src}</span>
                        <span class="rating-count">{score_count}</span>
                    </div>
                    <p class="novel-synopsis">{novel.get('synopsis', '')}</p>
                </div>
            </div>
            <div class="novel-body">
                <p class="novel-desc">{novel.get('description', '')}</p>
                <div class="novel-highlights">{hl_html}</div>
                {cav_html}
                <div class="novel-reason"><b>Why this:</b> {novel.get('recommendation_reason', '')}</div>
                {f'<div class="novel-similar">Similar to: {similar}</div>' if similar else ''}
                <div class="novel-quotes">{quotes_html}</div>
                <div class="novel-links">{links_html}</div>
            </div>
        </div>"""

    # Picks section
    picks_html = ""
    for key, label, icon in [("most_exciting", "Most Exciting", "!"), ("most_brainy", "Most Brainy", "?"),
                               ("most_touching", "Most Touching", "~"), ("newest", "Newest Hit", "+"),
                               ("ultimate", "Ultimate Pick", "*")]:
        pick = picks.get(key, {})
        if pick:
            is_ultimate = key == "ultimate"
            cls = "pick-ultimate" if is_ultimate else "pick-normal"
            picks_html += f"""
            <div class="pick-card {cls}">
                <div class="pick-icon">[{icon}]</div>
                <div class="pick-label">{label}</div>
                <div class="pick-name">{pick.get('name', '')}</div>
                <div class="pick-reason">{pick.get('reason', '')}</div>
            </div>"""

    # Extras section
    extras_html = ""
    for ex in extras:
        extras_html += f'<div class="extra-item"><b>{ex.get("title", "")}</b> by {ex.get("author", "")} -- {ex.get("reason", "")}</div>'

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Novel Recommendations - {profile.get('genre', 'Books')}</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        background: #FBF8F4;
        font-family: 'Georgia', 'Noto Serif SC', 'Songti SC', serif;
        color: #3a3028;
        line-height: 1.8;
    }}
    .report-header {{
        background: linear-gradient(135deg, #4A3728, #2c1e14);
        color: #f5efe8;
        padding: 48px 32px;
        text-align: center;
    }}
    .report-header h1 {{
        font-size: 28px;
        font-weight: 400;
        letter-spacing: 3px;
        margin-bottom: 8px;
    }}
    .report-header p {{ font-size: 13px; opacity: 0.7; }}

    .section {{ max-width: 900px; margin: 24px auto; padding: 0 24px; }}
    .section-title {{
        font-size: 20px; font-weight: 600; margin: 32px 0 16px;
        padding-bottom: 8px; border-bottom: 2px solid #D4A76A;
        color: #4A3728;
    }}

    /* Profile */
    .profile-bar {{ display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }}
    .profile-tag {{
        background: #f0e8dc; padding: 6px 14px; border-radius: 20px; font-size: 13px;
        font-family: sans-serif;
    }}
    .tag-label {{ font-weight: 700; color: #8B6D4B; margin-right: 4px; }}

    /* Novel Cards */
    .novel-card {{
        background: #fff; border-radius: 10px; margin-bottom: 20px;
        box-shadow: 0 1px 4px rgba(74,55,40,0.08); overflow: hidden;
    }}
    .novel-header {{
        display: flex; gap: 20px; padding: 20px;
    }}
    .novel-cover {{
        width: 100px; min-height: 140px; border-radius: 6px; flex-shrink: 0;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        padding: 12px 8px; text-align: center;
    }}
    .cover-title {{ color: #fff; font-size: 14px; font-weight: 700; line-height: 1.3; }}
    .cover-author {{ color: rgba(255,255,255,0.6); font-size: 10px; margin-top: 6px; }}
    .novel-meta {{ flex: 1; }}
    .novel-title {{ font-size: 18px; color: #2c1e14; margin-bottom: 2px; }}
    .novel-author {{ font-size: 13px; color: #8B6D4B; margin-bottom: 8px; font-family: sans-serif; }}
    .novel-tags {{ display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 8px; font-family: sans-serif; }}
    .genre-tag {{ background: #e8ddd0; color: #6b5744; padding: 2px 10px; border-radius: 10px; font-size: 11px; }}
    .status-badge {{ padding: 2px 10px; border-radius: 10px; font-size: 11px; font-weight: 600; }}
    .badge-done {{ background: #d4edda; color: #2d6a4f; }}
    .badge-ongoing {{ background: #fff3cd; color: #856404; }}
    .wc-tag {{ color: #999; font-size: 11px; padding: 2px 0; }}
    .novel-rating {{ display: flex; align-items: baseline; gap: 8px; margin-bottom: 6px; font-family: sans-serif; }}
    .rating-score {{ font-size: 22px; font-weight: 700; color: #D4A76A; }}
    .rating-source {{ font-size: 12px; color: #999; }}
    .rating-count {{ font-size: 11px; color: #bbb; }}
    .novel-synopsis {{ font-size: 14px; color: #666; }}

    .novel-body {{ padding: 0 20px 20px; }}
    .novel-desc {{ font-size: 14px; color: #555; margin-bottom: 12px; }}
    .novel-highlights {{ display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; font-family: sans-serif; }}
    .hl-tag {{ background: #FFF8E7; color: #B8860B; padding: 3px 10px; border-radius: 10px; font-size: 11px; }}
    .caveat {{ font-size: 12px; color: #c0392b; margin-bottom: 6px; font-family: sans-serif; }}
    .novel-reason {{ font-size: 13px; color: #4A3728; background: #f9f3eb; padding: 10px 14px;
        border-radius: 6px; margin: 10px 0; border-left: 3px solid #D4A76A; font-family: sans-serif; }}
    .novel-similar {{ font-size: 12px; color: #999; margin-bottom: 8px; font-family: sans-serif; }}
    .reader-quote {{ border-left: 3px solid #e0d5c7; padding: 8px 14px; margin: 8px 0;
        background: #fdfbf8; border-radius: 0 6px 6px 0; font-style: italic; font-size: 13px; color: #666; }}
    .reader-quote cite {{ font-size: 11px; color: #aaa; font-style: normal; }}
    .novel-links {{ display: flex; gap: 8px; margin-top: 10px; font-family: sans-serif; }}
    .read-link {{ display: inline-block; padding: 5px 16px; background: #4A3728; color: #fff;
        border-radius: 16px; font-size: 12px; text-decoration: none; transition: background 0.2s; }}
    .read-link:hover {{ background: #6b5744; }}

    /* Picks */
    .picks-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }}
    .pick-card {{ background: #fff; border-radius: 10px; padding: 20px; text-align: center;
        box-shadow: 0 1px 4px rgba(74,55,40,0.08); }}
    .pick-icon {{ font-size: 20px; color: #D4A76A; font-weight: 700; margin-bottom: 4px; font-family: monospace; }}
    .pick-label {{ font-size: 11px; color: #999; text-transform: uppercase; letter-spacing: 1px; font-family: sans-serif; }}
    .pick-name {{ font-size: 16px; font-weight: 700; color: #2c1e14; margin: 6px 0; }}
    .pick-reason {{ font-size: 12px; color: #888; font-family: sans-serif; }}
    .pick-ultimate {{
        background: linear-gradient(135deg, #4A3728, #2c1e14);
        color: #f5efe8; grid-column: 1 / -1;
    }}
    .pick-ultimate .pick-label {{ color: #D4A76A; }}
    .pick-ultimate .pick-name {{ color: #fff; font-size: 22px; }}
    .pick-ultimate .pick-reason {{ color: #d4c4b0; }}
    .pick-ultimate .pick-icon {{ color: #D4A76A; }}

    /* Extras */
    .extra-item {{ padding: 8px 0; border-bottom: 1px solid #f0e8dc; font-size: 14px; font-family: sans-serif; }}

    .footer {{ text-align: center; padding: 30px; font-size: 11px; color: #ccc; font-family: sans-serif; }}

    @media (max-width: 600px) {{
        .novel-header {{ flex-direction: column; }}
        .novel-cover {{ width: 100%; min-height: 80px; }}
        .picks-grid {{ grid-template-columns: 1fr; }}
    }}
</style>
</head>
<body>

<div class="report-header">
    <h1>Novel Recommendations</h1>
    <p>{profile.get('genre', 'Books')} | {len(novels)} picks | Novel Finder</p>
</div>

<div class="section">
    <h2 class="section-title">Reading Profile</h2>
    <div class="profile-bar">{profile_items}</div>
</div>

<div class="section">
    <h2 class="section-title">Recommended Novels</h2>
    {cards_html}
</div>

<div class="section">
    <h2 class="section-title">Quick Picks</h2>
    <div class="picks-grid">{picks_html}</div>
</div>

{"<div class='section'><h2 class='section-title'>Also Consider</h2>" + extras_html + "</div>" if extras else ""}

<div class="footer">Generated by Novel Finder | Read on official platforms | No spoilers</div>

</body>
</html>"""

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    html_file = out_path / "novel_report.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[OK] Report generated: {html_file}")
    print(f"     Novels: {len(novels)}")
    return str(html_file)


def main():
    parser = argparse.ArgumentParser(description="Novel Recommendation Report Generator")
    parser.add_argument("--data", required=True, help="JSON data file path")
    parser.add_argument("--output", default="./novel_report", help="Output directory")
    args = parser.parse_args()

    if not os.path.exists(args.data):
        print(f"[ERROR] Data file not found: {args.data}")
        sys.exit(1)

    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)

    generate_report(data, args.output)


if __name__ == "__main__":
    main()
