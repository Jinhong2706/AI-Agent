#!/usr/bin/env python3
"""
热榜查询脚本 - 每天每个平台只查询一次
记录每日查询状态，重启后也不再重复查询
"""

import sys
import json
import os
import requests
from datetime import datetime

# 热榜 type 映射
TRENDING_TYPES = {
    "weibo": 2,        # 微博热榜
    "toutiao": 3,      # 头条热榜
    "zhihu": 7,        # 知乎热榜
    "douyin": 6,       # 抖音热榜
    "bilibili": 8,     # B站热榜
    "baidu": 4,        # 百度热榜
    "tieba": 9,        # 贴吧热议榜
    "kuaishou": 10,    # 快手热榜
    "xhs": 14,         # 小红书热榜
}

TRENDING_NAMES = {
    "weibo": "微博",
    "toutiao": "头条",
    "zhihu": "知乎",
    "douyin": "抖音",
    "bilibili": "B站",
    "baidu": "百度",
    "tieba": "贴吧",
    "kuaishou": "快手",
    "xhs": "小红书",
}

# 状态文件
STATE_DIR = os.path.expanduser("~/.openclaw/workspace/memory")
STATE_FILE = os.path.join(STATE_DIR, "trending_state.json")
VERTICAL_FILE = os.path.join(STATE_DIR, "vertical_trending_state.json")
BAIDU_TRENDING_FILE = os.path.join(STATE_DIR, "baidu_trending_state.json")

# 百度热搜 tabs
BAIDU_TABS = {
    "livelihood": "民生",
    "finance": "财经",
    "society": "社会",
    "entertainment": "娱乐",
    "tech": "科技",
    "sports": "体育",
    "food": "美食",
    "car": "汽车",
    "game": "游戏",
    "edu": "教育",
}


def get_api_key():
    """获取 API Key"""
    env_file = os.path.expanduser("~/.openclaw/gateway.env")
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                if line.strip().startswith("BAIDU_API_KEY"):
                    return line.split("=")[1].strip().strip('"')
    raise Exception("BAIDU_API_KEY not set")


def get_trending(api_key, platform):
    """获取通用热榜"""
    type_id = TRENDING_TYPES.get(platform, 6)
    url = "https://qianfan.baidubce.com/v2/tools/trending_lists/medium"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    params = {"type": type_id}
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    results = response.json()
    
    if "data" not in results:
        raise Exception(f"热榜查询失败: {results}")
    
    items = results.get("data", [])
    return [{"title": item.get("title"), "hot": item.get("hot")} for item in items]


def load_state():
    """加载查询状态"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_state(state):
    """保存查询状态"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def load_vertical_state():
    """加载垂类热榜查询状态"""
    if os.path.exists(VERTICAL_FILE):
        with open(VERTICAL_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_vertical_state(state):
    """保存垂类热榜查询状态"""
    with open(VERTICAL_FILE, 'w') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_vertical_trending(api_key, category, platform="抖音", days=7):
    """获取垂类热榜"""
    url = "https://qianfan.baidubce.com/v2/tools/trending_lists/vertical"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "type": category,
        "mediaType": platform,
        "timeRange": days
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    results = response.json()
    
    if "data" not in results:
        raise Exception(f"垂类热榜查询失败: {results}")
    
    items = results.get("data", [])
    return [{"title": item.get("title"), "hot": item.get("hotNum") or item.get("hot")} for item in items]


# === 百度热搜相关函数 ===

def load_baidu_trending_state():
    """加载百度热搜查询状态"""
    if os.path.exists(BAIDU_TRENDING_FILE):
        with open(BAIDU_TRENDING_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_baidu_trending_state(state):
    """保存百度热搜查询状态"""
    with open(BAIDU_TRENDING_FILE, 'w') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_baidu_trending(api_key, tab="livelihood"):
    """获取百度热搜"""
    url = "https://qianfan.baidubce.com/v2/tools/baidu_trending"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    params = {"tab": tab}
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    results = response.json()
    
    if "data" not in results:
        raise Exception(f"百度热搜查询失败: {results}")
    
    items = results.get("data", [])
    return [{"title": item.get("word"), "hot": item.get("hotScore")} for item in items if item.get("word")]


def main():
    if len(sys.argv) < 2:
        print("Usage: python trending.py <platform> [category]")
        print("")
        print("通用热榜:")
        print(f"  python trending.py <platform>")
        print(f"  Available: {', '.join(TRENDING_TYPES.keys())}")
        print("")
        print("垂类热榜:")
        print(f"  python trending.py vertical <category> [platform]")
        print(f"  Categories: 汽车, 美食, ...")
        print(f"  Platforms: 抖音, 微博, 百度, ...")
        sys.exit(1)
    
    today = datetime.now().strftime("%Y-%m-%d")
    api_key = get_api_key()
    
    # 垂类热榜模式
    if sys.argv[1] == "vertical":
        category = sys.argv[2] if len(sys.argv) > 2 else "汽车"
        platform = sys.argv[3] if len(sys.argv) > 3 else "抖音"
        key = f"{category}_{platform}"
        
        state = load_vertical_state()
        
        # 每天热榜查询总计不超过8次（通用+垂类+百度热搜）
        # 统一计数器：读取所有状态文件
        total_count = 0
        
        # 通用热榜
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE) as f:
                s = json.load(f)
                total_count += s.get(today, {}).get("count", 0)
        
        # 垂类热榜
        if os.path.exists(VERTICAL_FILE):
            with open(VERTICAL_FILE) as f:
                s = json.load(f)
                total_count += s.get(today, {}).get("count", 0)
        
        # 百度热搜
        if os.path.exists(BAIDU_TRENDING_FILE):
            with open(BAIDU_TRENDING_FILE) as f:
                s = json.load(f)
                total_count += s.get(today, {}).get("count", 0)
        
        if total_count >= 8:
            print(f"[{today}] 热榜查询今日已达8次上限（通用+垂类+百度热搜）")
            print("请明天再试")
            sys.exit(0)
        
        # 检查是否已查询
        if today in state and key in state[today].get("queries", {}):
            print(f"[{today}] {category}热榜({platform}) 今日已查询，不再重复")
            print(f"如需重新查询，请删除: rm {VERTICAL_FILE}")
            sys.exit(0)
        
        try:
            results = get_vertical_trending(api_key, category, platform)
            
            # 记录查询状态
            if today not in state:
                state[today] = {"count": 0, "queries": {}}
            state[today]["count"] = state[today].get("count", 0) + 1
            state[today]["queries"] = state[today].get("queries", {})
            state[today]["queries"][key] = {
                "time": datetime.now().isoformat(),
                "count": len(results)
            }
            save_vertical_state(state)
            
            print(f"=== {category}热榜({platform}) ({today}) ===")
            for i, item in enumerate(results[:10], 1):
                print(f"{i}. {item['title']} (热度: {item['hot']})")
            
            print(f"\n[已记录] 今日查询 {state[today]['count']}/8 次")
            
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
        return
    
    # 百度热搜模式
    if sys.argv[1] == "baidu" or sys.argv[1] in BAIDU_TABS:
        tab = sys.argv[1] if sys.argv[1] in BAIDU_TABS else (sys.argv[2] if len(sys.argv) > 2 else "livelihood")
        if tab not in BAIDU_TABS:
            tab = "livelihood"
        
        tab_name = BAIDU_TABS.get(tab, tab)
        
        state = load_baidu_trending_state()
        
        # 每天最多8次（统一限制）
        if today in state and state[today].get("count", 0) >= 8:
            print(f"[{today}] 百度{tab_name}热搜 今日已达8次上限，无法继续查询")
            sys.exit(0)
        
        # 检查是否已查询
        if today in state and tab in state[today].get("queries", {}):
            print(f"[{today}] 百度{tab_name}热搜 今日已查询，不再重复")
            print(f"如需重新查询，请删除: rm {BAIDU_TRENDING_FILE}")
            sys.exit(0)
        
        try:
            results = get_baidu_trending(api_key, tab)
            
            # 记录状态
            if today not in state:
                state[today] = {"count": 0, "queries": {}}
            state[today]["count"] = state[today].get("count", 0) + 1
            state[today]["queries"] = state[today].get("queries", {})
            state[today]["queries"][tab] = {
                "time": datetime.now().isoformat(),
                "count": len(results)
            }
            save_baidu_trending_state(state)
            
            print(f"=== 百度{tab_name}热搜 ({today}) ===")
            for i, item in enumerate(results[:10], 1):
                print(f"{i}. {item['title']} (热度: {item['hot']})")
            
            print(f"\n[已记录] 今日查询 {state[today]['count']}/8 次")
            
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
        return
    
    # 通用热榜模式
    platform = sys.argv[1].lower()
    if platform not in TRENDING_TYPES:
        print(f"Error: Unknown platform '{platform}'")
        print(f"Available: {', '.join(TRENDING_TYPES.keys())}")
        sys.exit(1)
    
    # 检查是否已查询
    state = load_state()
    state.setdefault(today, {})
    
    if platform in state[today]:
        print(f"[{today}] {TRENDING_NAMES[platform]}热榜 今日已查询，不再重复")
        print("如需重新查询，请删除状态文件:")
        print(f"  rm {STATE_FILE}")
        sys.exit(0)
    
    try:
        results = get_trending(api_key, platform)
        
        # 记录查询状态
        state[today][platform] = {
            "time": datetime.now().isoformat(),
            "count": len(results)
        }
        save_state(state)
        
        # 输出结果
        print(f"=== {TRENDING_NAMES[platform]}热榜 ({today}) ===")
        for i, item in enumerate(results[:10], 1):
            print(f"{i}. {item['title']} (热度: {item['hot']})")
        
        print(f"\n[已记录] 今日不再重复查询")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()