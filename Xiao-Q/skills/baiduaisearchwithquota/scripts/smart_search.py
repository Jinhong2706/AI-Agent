#!/usr/bin/env python3
"""
智能搜索调度器 - 根据优先级自动选择最佳 API
优先级：
1. 深度智能搜索 (100次/天) - 最强 AI 总结，默认首选
2. 高性能版智能搜索 (100次/天) - 快速响应
3. 百度搜索 (50次/天) - 传统搜索结果，兜底用
4. 百度百科 (50次/天) - 概念查询
调度规则：配额用到 85% 就切换到下一个 API
"""

import sys
import json
import os
import requests


# 配额计数器（实际生产环境应持久化到文件）
QUOTA = {
    # 深度智能搜索 - 免费100次/天（最强，优先使用）
    "chat_completions": {"limit": 100, "used": 0, "name": "深度智能搜索"},
    # 高性能版智能搜索 - 免费100次/天
    "smart_search_pro": {"limit": 100, "used": 0, "name": "高性能版智能搜索"},
    # 百度搜索 - 免费50次/天（兜底用）
    "smart_search": {"limit": 50, "used": 0, "name": "百度搜索"},
    # 百科 - 免费50次/天
    "baike_content": {"limit": 50, "used": 0, "name": "百度百科（详情）"},
    "baike_search": {"limit": 50, "used": 0, "name": "百度百科（搜索）"},
    # 热榜不纳入调度器，单独处理
}

# 配额安全阈值：用到 85% 就切换到下一个 API
QUOTA_THRESHOLD = 0.85


def get_api_key():
    api_key = os.getenv("BAIDU_API_KEY")
    if not api_key:
        # 尝试从 .env 文件加载
        env_file = os.path.expanduser("~/.openclaw/gateway.env")
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    if line.strip().startswith("BAIDU_API_KEY"):
                        api_key = line.split("=")[1].strip().strip('"')
                        break
    if not api_key:
        raise Exception("BAIDU_API_KEY not set")
    return api_key


def smart_search(query: str, force_api: str = None, **kwargs):
    """
    智能搜索 - 根据优先级自动选择 API
    
    Args:
        query: 搜索关键词
        force_api: 强制使用某个 API (可选)
        **kwargs: 传递给底层 API 的额外参数
            - deep_search: bool  深度搜索（默认 True，仅 chat_completions 有效）
            - reasoning: bool    开启推理模式（默认 False，仅 chat_completions 有效）
            - recency: str       时间过滤 (day/week/month/year)
            - resource_types: list 资源类型 (image/video/web)
            - top_k: int         返回结果数量（默认 10）
    
    示例:
        smart_search("北京天气")                          # 默认
        smart_search("最新AI新闻", recency="week")        # 一周内
        smart_search("什么是量子计算", reasoning=True)      # 开启推理
        smart_search("科技图片", resource_types=["image"]) # 带图片结果
    """
    api_key = get_api_key()
    
    # 如果指定了强制使用的 API
    if force_api:
        return _call_api(api_key, force_api, query, **kwargs)
    
    # 智能调度：按优先级尝试（深度智能搜索 → 高性能版 → 百度搜索）
    apis_order = ["chat_completions", "smart_search_pro", "smart_search"]
    
    for api_name in apis_order:
        quota = QUOTA[api_name]
        
        # 检查配额是否用完
        if quota["used"] >= quota["limit"]:
            print(f"[调度] {quota['name']} 配额已用完 ({quota['used']}/{quota['limit']})，跳过")
            continue
        
        # 配额达到 85% 时切换到下一个 API（更安全，避免用到 100% 后收费）
        remaining = quota["limit"] - quota["used"]
        if remaining <= quota["limit"] * (1 - QUOTA_THRESHOLD):
            print(f"[调度] {quota['name']} 配额剩余 {remaining} 次 (15%)，切换到下一个 API...")
            continue
        
        try:
            result = _call_api(api_key, api_name, query, **kwargs)
            QUOTA[api_name]["used"] += 1
            print(f"[调度] 使用 {quota['name']} (已用 {QUOTA[api_name]['used']}/{quota['limit']})")
            return result
        except Exception as e:
            print(f"[调度] {quota['name']} 失败: {e}")
            continue
    
    raise Exception("所有 API 均不可用或配额已用完")


def _call_api(api_key, api_name, query, **kwargs):
    """调用指定的 API，传递额外参数"""
    
    if api_name == "chat_completions":
        return _chat_completions(api_key, query, **kwargs)
    elif api_name == "smart_search":
        return _smart_search(api_key, query, **kwargs)
    elif api_name == "web_search":
        return _smart_search(api_key, query, **kwargs)
    elif api_name == "smart_search_pro":
        return _smart_search_pro(api_key, query, **kwargs)
    elif api_name == "baidu_search":
        return _baidu_search(api_key, query)
    elif api_name == "baike":
        return _baike_content(api_key, query)
    elif api_name == "baike_search":
        return _baike_search(api_key, query)
    elif api_name in ["zhihu", "bilibili", "weibo", "xhs", "kuaishou"]:
        return _trending(api_key, api_name, query)
    else:
        raise ValueError(f"Unknown API: {api_name}")


def _chat_completions(api_key, query, **kwargs):
    """
    深度智能搜索（chat/completions）- 最强 API
    
    支持的额外参数（通过 kwargs）:
    - deep_search: bool  深度搜索（默认 True）
    - reasoning: bool   开启推理模式（默认 False）
    - recency: str      时间过滤 (day/week/month/year)
    - resource_types: list 资源类型 (image/video/web)
    """
    url = "https://qianfan.baidubce.com/v2/ai_search/chat/completions"
    headers = {
        "X-Appbuilder-Authorization": f"Bearer {api_key}",
        "X-Appbuilder-From": "openclaw",
        "Content-Type": "application/json"
    }
    
    # 构建请求参数
    payload = {
        "messages": [{"content": query, "role": "user"}],
        "stream": False,
        "model": "ernie-3.5-8k",  # 官方推荐模型
        "instruction": "##",
        "enable_corner_markers": True,
        "enable_deep_search": kwargs.get("deep_search", True),
        "enable_reasoning": kwargs.get("reasoning", False),
    }
    
    # 时间过滤
    recency = kwargs.get("recency")
    if recency:
        payload["search_recency_filter"] = recency
    
    # 资源类型过滤
    resource_types = kwargs.get("resource_types")
    if resource_types:
        top_k = kwargs.get("top_k", 4)
        payload["resource_type_filter"] = [
            {"type": rt, "top_k": top_k} for rt in resource_types
        ]
    else:
        # 默认 web 结果
        payload["resource_type_filter"] = [{"type": "web", "top_k": 10}]
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    results = response.json()
    
    if "code" in results:
        raise Exception(results.get("message", "Unknown error"))
    
    choices = results.get("choices", [])
    if choices:
        content = choices[0].get("message", {}).get("content", "")
        # 同时返回 references 供引用
        references = results.get("references", [])
        return {"content": content, "references": references}
    return ""


def _smart_search(api_key, query, **kwargs):
    """
    百度搜索 - 纯搜索结果列表
    
    支持的额外参数:
    - recency: str      时间过滤 (week/month/semiyear/year)
    - site: str        站点过滤
    - safe_search: bool  安全搜索
    - top_k: int       结果数量（默认10，最大50）
    """
    url = "https://qianfan.baidubce.com/v2/ai_search/web_search"
    headers = {
        "X-Appbuilder-Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    top_k = kwargs.get("top_k", 10)
    
    payload = {
        "messages": [{"content": query, "role": "user"}],
        "edition": "standard",
        "search_source": "baidu_search_v2",
        "resource_type_filter": [{"type": "web", "top_k": top_k}],
    }
    
    # 时间过滤
    recency = kwargs.get("recency")
    if recency:
        payload["search_recency_filter"] = recency
    
    # 站点过滤
    site = kwargs.get("site")
    if site:
        payload["search_filter"] = {"match": {"site": [site]}}
    
    # 安全搜索
    if kwargs.get("safe_search"):
        payload["safe_search"] = True
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    results = response.json()
    
    if "code" in results:
        raise Exception(results.get("message", "Unknown error"))
    
    datas = results.get("references", [])
    # 移除 snippet 字段
    for item in datas:
        item.pop("snippet", None)
    return datas


def _smart_search_pro(api_key, query, **kwargs):
    """
    高性能版智能搜索生成 - 响应快速
    
    支持的额外参数（通过 kwargs）:
    - recency: str      时间过滤 (day/week/month/year)
    - resource_types: list 资源类型 (image/video/web)
    """
    url = "https://qianfan.baidubce.com/v2/ai_search/web_summary"
    headers = {
        "X-Appbuilder-Authorization": f"Bearer {api_key}",
        "X-Appbuilder-From": "openclaw",
        "Content-Type": "application/json"
    }
    
    # 构建请求参数
    payload = {
        "instruction": "你是一个专业、简洁的AI助手，用中文回答用户问题。",
        "messages": [{"role": "user", "content": query}],
        "stream": False,
        "model": "non_thinking"
    }
    
    # 资源类型过滤
    resource_types = kwargs.get("resource_types")
    if resource_types:
        top_k = kwargs.get("top_k", 4)
        payload["resource_type_filter"] = [
            {"type": rt, "top_k": top_k} for rt in resource_types
        ]
    else:
        payload["resource_type_filter"] = [{"type": "web", "top_k": 10}]
    
    # 时间过滤
    recency = kwargs.get("recency")
    if recency:
        payload["search_recency_filter"] = recency
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    results = response.json()
    
    if "error" in results:
        raise Exception(results["error"].get("message", "Unknown error"))
    
    choices = results.get("choices", [])
    if choices:
        return choices[0].get("message", {}).get("content", "")
    return ""


def _baidu_search(api_key, query):
    """传统百度搜索（作为兜底）"""
    # 使用智能搜索的标准模式
    url = "https://qianfan.baidubce.com/v2/ai_search/web_search"
    headers = {
        "X-Appbuilder-Authorization": f"Bearer {api_key}",
        "X-Appbuilder-From": "openclaw",
        "Content-Type": "application/json"
    }
    payload = {
        "messages": [{"content": query, "role": "user"}],
        "edition": "lite",  # 轻量版
        "search_source": "baidu_search_v2",
        "resource_type_filter": [{"type": "web", "top_k": 10}],
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    results = response.json()
    
    if "code" in results:
        raise Exception(results.get("message", "Unknown error"))
    
    datas = results.get("references", [])
    for item in datas:
        item.pop("snippet", None)
    return datas


def _baike_content(api_key, query):
    """百度百科词条详情 - 专用 API"""
    url = "https://appbuilder.baidu.com/v2/baike/lemma/get_content"
    headers = {
        "X-Appbuilder-Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    params = {
        "search_type": "lemmaTitle",
        "search_key": query
    }
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    results = response.json()
    
    if "request_id" not in results:
        raise Exception(f"百度百科查询失败: {results}")
    
    result = results.get("result", {})
    return {
        "lemma_id": result.get("lemma_id"),
        "title": result.get("lemma_title"),
        "description": result.get("lemma_desc"),
        "summary": result.get("summary"),
        "url": result.get("url")
    }


def _baike_search(api_key, query):
    """百度百科词条搜索 - 专用 API"""
    url = "https://appbuilder.baidu.com/v2/baike/lemma/get_list_by_title"
    headers = {
        "X-Appbuilder-Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    params = {"lemma_title": query}
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    results = response.json()
    
    if "request_id" not in results:
        raise Exception(f"百度百科搜索失败: {results}")
    
    items = results.get("result", [])
    return [{"lemma_id": item.get("lemma_id"),
             "title": item.get("lemma_title"),
             "description": item.get("lemma_desc"),
             "url": item.get("url")} for item in items]


# 热榜 type 映射（每个 type 每天 1 次，共 10 次）
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


def _trending(api_key, api_name, query):
    """热榜榜单查询"""
    type_id = TRENDING_TYPES.get(api_name, 2)
    url = "https://qianfan.baidubce.com/v2/tools/trending_lists/medium"
    headers = {
        "X-Appbuilder-Authorization": f"Bearer {api_key}",
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


def get_quota_status():
    """获取当前配额状态"""
    return {
        name: {"used": data["used"], "limit": data["limit"], "name": data["name"]}
        for name, data in QUOTA.items()
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python smart_search.py '<query>' [--force api]")
        print("")
        print("Args:")
        print("  query          搜索关键词")
        print("  --force api    强制使用指定API (smart_search, smart_search_pro, baike, baidu_search)")
        print("")
        print("Example:")
        print("  python smart_search.py '如何做兼职'")
        print("  python smart_search.py '什么是量子计算' --force smart_search_pro")
        sys.exit(1)
    
    # 解析参数
    args = sys.argv[1:]
    force_api = None
    
    if "--force" in args:
        idx = args.index("--force")
        if idx + 1 < len(args):
            force_api = args[idx + 1]
            args = args[:idx] + args[idx + 2:]
    
    query = " ".join(args)
    
    try:
        result = smart_search(query, force_api)
        
        # 格式化输出
        if isinstance(result, dict):
            # 智能搜索返回（带 summary）
            if "content" in result and "references" in result:
                content = result.get("content", "")
                refs = result.get("references", [])
                
                # 构建来源映射（用于替换 [1][2] 这样的引用）
                ref_map = {}
                for ref in refs[:15]:
                    idx = ref.get("id", 0)
                    title = ref.get("title", "")
                    source = ref.get("web_anchor", "")
                    url = ref.get("url", "")
                    if source and url:
                        ref_map[idx] = f"🔗 [{source}]({url})"
                    elif source:
                        ref_map[idx] = f"📰 {source}"
                
                # 替换内容中的引用编号 [1][2] 为实际来源
                import re
                def replace_ref(match):
                    idx = int(match.group(1))
                    return ref_map.get(idx, f"[{idx}]")
                
                content = re.sub(r'\[(\d+)\]', replace_ref, content)
                
                print(f"\n📊 搜索「{query}」结果：\n")
                print(content)
                print("\n" + "=" * 50)
            
            # 普通搜索返回（data 数组）
            elif "data" in result:
                items = result["data"]
                print(f"\n📊 搜索「{query}」共 {len(items)} 条结果：\n")
                for i, item in enumerate(items[:20], 1):
                    title = item.get("title", "")
                    content = item.get("content", "")
                    date = item.get("date", "")
                    source = item.get("web_anchor", "")
                    
                    if content and len(content) > 80:
                        content = content[:80] + "..."
                    
                    print(f"【{i}】{title}")
                    if content:
                        print(f"    {content}")
                    if date or source:
                        print(f"    📅 {date} | 📰 {source}")
                    print()
            else:
                print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 打印配额状态
        print("\n--- 配额状态（本地计数，仅供参考）---")
        status = get_quota_status()
        for k, v in status.items():
            print(f"{v['name']}: {v['used']}/{v['limit']}")
        
        # 提醒用户以百度后台为准
        print("\n⚠️ 重要提醒：")
        print("   百度计算调用次数的方式与实际可能有差异")
        print("   请以千帆后台实际用量为准：https://console.bce.baidu.com/qianfan/")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)