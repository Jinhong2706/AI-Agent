import json
import re
import sys
from collections import Counter

def parse_views(v):
    if v is None: return 0
    if isinstance(v, int): return v
    if isinstance(v, float): return int(v)
    if isinstance(v, str):
        v = v.replace('万', '*10000').replace('播放', '').strip()
        if '*' in v:
            try:
                parts = v.split('*')
                return int(float(parts[0]) * int(parts[1]))
            except: return 0
        try:
            return int(v)
        except:
            return 0
    return 0

def parse_duration(d):
    if not d: return 0
    parts = d.split(':')
    if len(parts) == 2: return int(parts[0]) * 60 + int(parts[1])
    if len(parts) == 3: return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0

def categorize(title):
    title = title.lower()
    # General AI Categories
    if 'claude' in title: return 'Claude/Anthropic'
    if 'deepseek' in title: return 'DeepSeek'
    if 'qwen' in title or '千问' in title: return 'Qwen/Ali'
    if 'openclaw' in title or '小龙虾' in title: return 'OpenClaw/Agent'
    if '本地' in title or 'local' in title or 'ollama' in title: return 'Local AI/Deploy'
    if '一人公司' in title or 'ai公司' in title: return 'Solopreneur/Agency'
    if '代码' in title or 'coding' in title or 'cursor' in title: return 'Coding/Development'
    if '免费' in title or '白嫖' in title or '0元' in title: return 'Free/Value-Driven'
    if '实测' in title or '评测' in title: return 'Benchmark/Review'
    return 'Other Tools/News'

def run_analysis(input_file):
    try:
        with open(input_file, 'r') as f:
            raw_data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return

    data = []
    for item in raw_data:
        if not item or 'title' not in item: continue
        title = item['title']
        views = parse_views(item.get('views', item.get('play', 0)))
        comments = parse_views(item.get('comments', item.get('comment', 0)))
        duration = parse_duration(item.get('duration', item.get('length', '0:00')))
        category = categorize(title)
        data.append({
            'title': title,
            'views': views,
            'comments': comments,
            'duration_sec': duration,
            'category': category,
            'date': item.get('date', item.get('created', ''))
        })

    # Analysis 1: Category Performance
    cat_stats = {}
    for r in data:
        cat = r['category']
        if cat not in cat_stats: cat_stats[cat] = {'count': 0, 'views': [], 'comments': [], 'durations': []}
        cat_stats[cat]['count'] += 1
        cat_stats[cat]['views'].append(r['views'])
        cat_stats[cat]['comments'].append(r['comments'])
        cat_stats[cat]['durations'].append(r['duration_sec'])

    cat_summary = []
    for cat, s in cat_stats.items():
        cat_summary.append({
            'category': cat,
            'count': s['count'],
            'avg_views': sum(s['views']) / s['count'],
            'avg_comments': sum(s['comments']) / s['count'],
            'avg_duration_min': (sum(s['durations']) / s['count']) / 60,
            'max_views': max(s['views'])
        })
    cat_summary.sort(key=lambda x: x['avg_views'], reverse=True)

    # Analysis 2: Keyword Frequency vs Views
    word_views = {}
    for r in data:
        # Simple word extraction
        words = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z0-9]+', r['title'])
        for w in set(words):
            if len(w) < 2: continue
            w = w.lower()
            if w not in word_views: word_views[w] = []
            word_views[w].append(r['views'])

    keyword_summary = []
    for w, vlist in word_views.items():
        if len(vlist) >= 2: # min 2 occurrences
            keyword_summary.append({
                'keyword': w,
                'count': len(vlist),
                'avg_views': sum(vlist) / len(vlist)
            })
    keyword_summary.sort(key=lambda x: x['avg_views'], reverse=True)

    # Analysis 3: Funnel Calculation
    total_views = sum(d['views'] for d in data)
    total_comments = sum(d['comments'] for d in data)
    avg_engagement = (total_comments / total_views * 100) if total_views > 0 else 0

    report_data = {
        'total_videos': len(data),
        'total_views': total_views,
        'total_comments': total_comments,
        'avg_engagement_rate': f"{avg_engagement:.4f}%",
        'category_summary': cat_summary,
        'keyword_summary': keyword_summary[:30],
        'top_10_videos': sorted(data, key=lambda x: x['views'], reverse=True)[:10]
    }

    print(json.dumps(report_data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_bilibili.py <json_file>")
    else:
        run_analysis(sys.argv[1])
