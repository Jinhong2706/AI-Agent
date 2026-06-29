#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
douyu_room_status.py - 查询斗鱼直播间状态（使用官方JSON接口）
用法: python3 douyu_room_status.py <房间号>
输出: JSON格式 {"room_id":"12345","nickname":"xxx","title":"xxx","is_live":true/false,"cate":"xxx","url":"..."}
"""

import sys
import json
import urllib.request
import urllib.error

def fetch_room_status(room_id):
    url = f"https://open.douyucdn.cn/api/RoomApi/room/{room_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": f"https://www.douyu.com/{room_id}",
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": f"请求失败: {e}"}

    if data.get("error") != 0:
        return {"error": f"接口返回错误: {data.get('data', {}).get('msg', '未知错误')}"}

    d = data.get("data", {})

    # room_status: "1"=直播中, "2"=未开播
    is_live = d.get("room_status", "2") == "1"

    result = {
        "room_id": room_id,
        "nickname": d.get("owner_name", ""),
        "title": d.get("room_name", ""),
        "is_live": is_live,
        "cate": d.get("cate_name", ""),
        "online": d.get("online", 0),
        "url": f"https://www.douyu.com/{room_id}",
    }

    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "缺少房间号参数"}, ensure_ascii=False))
        sys.exit(1)

    room_id = sys.argv[1].strip()
    result = fetch_room_status(room_id)
    print(json.dumps(result, ensure_ascii=False))
