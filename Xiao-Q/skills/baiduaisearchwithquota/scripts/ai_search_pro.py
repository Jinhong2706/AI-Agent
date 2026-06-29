#!/usr/bin/env python3
"""
智能搜索生成高性能版 - 百度AI搜索
API文档: https://cloud.baidu.com/doc/qianfan/s/Kmiy99ziv
端点: POST https://qianfan.baidubce.com/v2/ai_search/web_summary
免费额度: 100次/天
"""

import sys
import json
import requests
import os


def ai_search_pro(api_key, query: str, stream: bool = False, top_k: int = 10):
    """高性能版智能搜索生成"""
    url = "https://qianfan.baidubce.com/v2/ai_search/web_summary"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Appbuilder-From": "openclaw",
        "Content-Type": "application/json"
    }
    
    payload = {
        "instruction": "你是一个专业、简洁的AI助手，用中文回答用户问题。",
        "messages": [{"role": "user", "content": query}],
        "stream": stream,
        "resource_type_filter": [{"type": "web", "top_k": top_k}],
        "model": "non_thinking"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    results = response.json()
    
    if "error" in results:
        raise Exception(results["error"].get("message", "Unknown error"))
    
    # 提取内容
    if stream:
        return results  # 流式响应需要特殊处理
    else:
        choices = results.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "")
        return ""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ai_search_pro.py '<query>'")
        print("Example: python ai_search_pro.py '什么是量子计算'")
        sys.exit(1)
    
    query = sys.argv[1]
    
    # 从命令行参数或环境变量获取API Key
    api_key = os.getenv("BAIDU_API_KEY")
    if not api_key:
        print("Error: BAIDU_API_KEY not set")
        sys.exit(1)
    
    try:
        result = ai_search_pro(api_key, query)
        print(result)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)