#!/usr/bin/env python3
"""
交互式浏览器脚本 - 支持点击、填表等交互操作
使用 Playwright + 系统 Chrome
"""

import sys
import argparse
import json
import time

def interactive_browse(url, actions=None, wait_time=30000):
    """
    交互式浏览网页
    
    Args:
        url: 目标URL
        actions: 要执行的操作列表，格式为:
            [
                {"type": "click", "selector": "#button-id"},
                {"type": "fill", "selector": "#input-id", "value": "text"},
                {"type": "screenshot", "path": "/tmp/screenshot.png"},
                {"type": "wait", "seconds": 2},
                {"type": "extract", "selector": ".content"}
            ]
        wait_time: 页面加载等待时间(ms)
    
    Returns:
        dict: 包含执行结果
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("错误: 未安装 Playwright", file=sys.stderr)
        return None
    
    result = {
        "url": url,
        "title": "",
        "actions_results": [],
        "error": None
    }
    
    try:
        with sync_playwright() as p:
            # 使用系统 Chrome
            print(f"正在启动 Chrome...", file=sys.stderr)
            browser = p.chromium.launch(
                headless=True,
                executable_path='/usr/local/bin/google-chrome',
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            page = browser.new_page()
            
            # 访问页面
            print(f"正在访问: {url}", file=sys.stderr)
            page.goto(url, wait_until="networkidle", timeout=wait_time)
            
            result["title"] = page.title()
            result["url"] = page.url
            
            # 执行操作序列
            if actions:
                for i, action in enumerate(actions):
                    action_type = action.get("type")
                    print(f"执行操作 {i+1}: {action_type}", file=sys.stderr)
                    
                    try:
                        if action_type == "click":
                            selector = action.get("selector")
                            page.click(selector, timeout=5000)
                            result["actions_results"].append({
                                "action": action_type,
                                "selector": selector,
                                "status": "success"
                            })
                            time.sleep(0.5)  # 等待页面响应
                            
                        elif action_type == "fill":
                            selector = action.get("selector")
                            value = action.get("value", "")
                            page.fill(selector, value, timeout=5000)
                            result["actions_results"].append({
                                "action": action_type,
                                "selector": selector,
                                "status": "success"
                            })
                            
                        elif action_type == "screenshot":
                            path = action.get("path", "/tmp/screenshot.png")
                            page.screenshot(path=path, full_page=True)
                            result["actions_results"].append({
                                "action": action_type,
                                "path": path,
                                "status": "success"
                            })
                            
                        elif action_type == "wait":
                            seconds = action.get("seconds", 1)
                            time.sleep(seconds)
                            result["actions_results"].append({
                                "action": action_type,
                                "seconds": seconds,
                                "status": "success"
                            })
                            
                        elif action_type == "extract":
                            selector = action.get("selector")
                            text = page.locator(selector).inner_text()
                            result["actions_results"].append({
                                "action": action_type,
                                "selector": selector,
                                "text": text,
                                "status": "success"
                            })
                            
                        elif action_type == "evaluate":
                            script = action.get("script")
                            eval_result = page.evaluate(script)
                            result["actions_results"].append({
                                "action": action_type,
                                "result": str(eval_result),
                                "status": "success"
                            })
                            
                    except Exception as e:
                        result["actions_results"].append({
                            "action": action_type,
                            "status": "failed",
                            "error": str(e)
                        })
                        print(f"操作失败: {str(e)}", file=sys.stderr)
            
            browser.close()
            
    except Exception as e:
        result["error"] = str(e)
        print(f"访问出错: {str(e)}", file=sys.stderr)
    
    return result

def main():
    parser = argparse.ArgumentParser(description="交互式浏览器 - 支持点击、填表等操作")
    parser.add_argument("url", help="要访问的URL")
    parser.add_argument("--actions", "-a", help="操作JSON字符串或文件路径（以@开头）")
    parser.add_argument("--wait", "-w", type=int, default=30000, help="页面加载等待时间(ms)")
    parser.add_argument("--output", "-o", help="输出JSON文件路径")
    
    args = parser.parse_args()
    
    # 解析操作
    actions = None
    if args.actions:
        if args.actions.startswith('@'):
            # 从文件读取
            with open(args.actions[1:], 'r', encoding='utf-8') as f:
                actions = json.load(f)
        else:
            # 直接解析JSON
            actions = json.loads(args.actions)
    
    # 执行
    result = interactive_browse(args.url, actions, args.wait)
    
    if result is None:
        sys.exit(1)
    
    # 输出结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"结果已保存到: {args.output}", file=sys.stderr)
    else:
        if result["error"]:
            print(f"错误: {result['error']}", file=sys.stderr)
            sys.exit(1)
        
        print(f"\n标题: {result['title']}")
        print(f"URL: {result['url']}")
        
        if result["actions_results"]:
            print(f"\n操作结果:")
            for i, action_result in enumerate(result["actions_results"]):
                print(f"  {i+1}. {action_result['action']}: {action_result['status']}")
                if action_result.get("error"):
                    print(f"     错误: {action_result['error']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
