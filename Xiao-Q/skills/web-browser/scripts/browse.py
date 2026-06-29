#!/usr/bin/env python3
"""
完全增强版 Web Browser - 终极反检测版本 v4.1
新增：鼠标轨迹模拟、更完整指纹伪装、请求头完美伪装
"""

import sys
import argparse
import json
import time
import os
import random
from pathlib import Path

# Cookie 管理
COOKIE_FILE = Path.home() / ".web_browser_cookies.json"

# User-Agent 池
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0'
]

# 视口大小池
VIEWPORT_SIZES = [
    {'width': 1920, 'height': 1080},
    {'width': 1366, 'height': 768},
    {'width': 1536, 'height': 864},
    {'width': 1440, 'height': 900},
    {'width': 1280, 'height': 720}
]

def load_cookies():
    """加载保存的 cookies"""
    if COOKIE_FILE.exists():
        with open(COOKIE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_cookies(domain, cookies):
    """保存 cookies"""
    all_cookies = load_cookies()
    all_cookies[domain] = cookies
    with open(COOKIE_FILE, 'w') as f:
        json.dump(all_cookies, f, indent=2)

def get_random_user_agent():
    """随机返回一个 User-Agent"""
    return random.choice(USER_AGENTS)

def get_random_viewport():
    """随机返回一个视口大小"""
    return random.choice(VIEWPORT_SIZES)

def human_mouse_move(page, selector):
    """模拟人类鼠标移动轨迹（贝塞尔曲线）"""
    try:
        # 获取元素位置
        box = page.locator(selector).bounding_box()
        if not box:
            return
        
        # 起始位置（屏幕中心）
        start_x, start_y = 500, 300
        
        # 目标位置（元素中心）
        target_x = box['x'] + box['width'] / 2
        target_y = box['y'] + box['height'] / 2
        
        # 生成贝塞尔曲线控制点
        control_x = random.randint(min(start_x, int(target_x)), max(start_x, int(target_x)))
        control_y = random.randint(min(start_y, int(target_y)), max(start_y, int(target_y)))
        
        # 沿曲线移动（10步）
        for i in range(10):
            t = i / 9.0
            # 二次贝塞尔曲线
            x = (1-t)**2 * start_x + 2*(1-t)*t * control_x + t**2 * target_x
            y = (1-t)**2 * start_y + 2*(1-t)*t * control_y + t**2 * target_y
            page.mouse.move(x, y)
            time.sleep(random.uniform(0.01, 0.03))
        
        time.sleep(random.uniform(0.1, 0.3))
    except:
        pass

def setup_ultimate_stealth_scripts():
    """返回终极反检测脚本集合（增强版）"""
    return [
        # 1. 隐藏 webdriver
        """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        """,
        
        # 2. 伪装 plugins
        """
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                return [
                    {name: 'Chrome PDF Plugin', description: 'Portable Document Format', filename: 'internal-pdf-viewer'},
                    {name: 'Chrome PDF Viewer', description: '', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                    {name: 'Native Client', description: '', filename: 'internal-nacl-plugin'}
                ];
            }
        });
        """,
        
        # 3. 伪装 languages
        """
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en-US', 'en']
        });
        """,
        
        # 4. 覆盖 chrome 属性
        """
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
        """,
        
        # 5. 覆盖 permissions
        """
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        """,
        
        # 6. 覆盖 plugin detection
        """
        Object.defineProperty(navigator, 'maxTouchPoints', {
            get: () => 1
        });
        """,
        
        # 7. 删除 automation 标记
        """
        delete navigator.__proto__.webdriver;
        if (window.document.documentElement) {
            window.document.documentElement.setAttribute('webdriver', undefined);
        }
        """,
        
        # 8. 伪装 WebGL 指纹
        """
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Intel Inc.';
            }
            if (parameter === 37446) {
                return 'Intel(R) Iris(R) Graphics 6100';
            }
            return getParameter.apply(this, arguments);
        };
        """,
        
        # 9. Canvas 指纹干扰
        """
        const getImageData = CanvasRenderingContext2D.prototype.getImageData;
        CanvasRenderingContext2D.prototype.getImageData = function(sx, sy, sw, sh) {
            const imageData = getImageData.apply(this, arguments);
            for (let i = 0; i < imageData.data.length; i += 4) {
                imageData.data[i] += Math.floor(Math.random() * 10) - 5;
                imageData.data[i+1] += Math.floor(Math.random() * 10) - 5;
                imageData.data[i+2] += Math.floor(Math.random() * 10) - 5;
            }
            return imageData;
        };
        """,
        
        # 10. AudioContext 指纹干扰
        """
        const audioContext = window.AudioContext || window.webkitAudioContext;
        if (audioContext) {
            const originalGetChannelData = audioContext.prototype.getChannelData;
            audioContext.prototype.getChannelData = function() {
                const result = originalGetChannelData.apply(this, arguments);
                for (let i = 0; i < result.length; i++) {
                    result[i] += (Math.random() - 0.5) * 0.0001;
                }
                return result;
            };
        }
        """,
        
        # 11. 字体枚举干扰
        """
        const enumerateDevices = navigator.mediaDevices.enumerateDevices;
        navigator.mediaDevices.enumerateDevices = function() {
            return enumerateDevices.apply(this, arguments).then(devices => {
                return devices.filter(d => d.kind !== 'audioinput');
            });
        };
        """,
        
        # 12. 硬件并发数伪装
        """
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8
        });
        """,
        
        # 13. 内存伪装
        """
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8
        });
        """,
        
        # 14. Connection 伪装
        """
        Object.defineProperty(navigator, 'connection', {
            get: () => ({
                effectiveType: '4g',
                rtt: 50,
                downlink: 10
            })
        });
        """,
        
        # 15. 屏幕信息伪装
        """
        Object.defineProperty(window.screen, 'width', { get: () => 1920 });
        Object.defineProperty(window.screen, 'height', { get: () => 1080 });
        Object.defineProperty(window.screen, 'availWidth', { get: () => 1920 });
        Object.defineProperty(window.screen, 'availHeight', { get: () => 1040 });
        Object.defineProperty(window.screen, 'colorDepth', { get: () => 24 });
        Object.defineProperty(window.screen, 'pixelDepth', { get: () => 24 });
        """,
        
        # 16. 时区伪装
        """
        Object.defineProperty(Intl, 'DateTimeFormat', {
            get: () => function(locales, options) {
                options = options || {};
                options.timeZone = 'Asia/Shanghai';
                return new Intl.DateTimeFormat(locales, options);
            }
        });
        """
    ]

def smart_wait_for_content(page, timeout=30000):
    """智能等待内容加载"""
    start = time.time()
    
    # 等待网络空闲
    try:
        page.wait_for_load_state('networkidle', timeout=timeout//2)
    except:
        pass
    
    # 多次滚动触发懒加载
    for scroll_pos in [0, 1000, 2000, 3000, 5000, 10000]:
        page.evaluate(f'window.scrollTo(0, {scroll_pos})')
        time.sleep(0.3)
        if time.time() - start > timeout / 1000:
            break
    
    # 滚动到底部等待加载
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(2)
    
    # 滚动回顶部
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(1)

def browse_ultimate_enhanced(url, actions=None, viewport_size=None, save_cookies_domain=None, 
                            load_cookies_domain=None, use_random_ua=False, use_random_viewport=False):
    """
    终极增强版浏览 - 最强反检测 v4.1
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("错误: 未安装 Playwright", file=sys.stderr)
        return use_requests_fallback(url)
    
    result = {
        "url": url,
        "title": "",
        "final_url": "",
        "text": "",
        "html": "",
        "screenshot_path": None,
        "actions_results": [],
        "cookies": None,
        "error": None,
        "method": "playwright-ultimate-stealth-v4.1",
        "user_agent": None,
        "viewport": None
    }
    
    # 确定 User-Agent 和视口
    user_agent = get_random_user_agent() if use_random_ua else 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    viewport = get_random_viewport() if use_random_viewport else {'width': 1920, 'height': 1080}
    final_viewport = viewport_size or viewport
    
    result["user_agent"] = user_agent
    result["viewport"] = final_viewport
    
    try:
        with sync_playwright() as p:
            print("启动浏览器（终极反检测模式 v4.1）...", file=sys.stderr)
            
            # 尝试多种浏览器启动方式
            browser = None
            browser_args = [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--window-size=1920,1080',
                '--disable-extensions',
                '--disable-component-extensions-with-background-pages',
                '--disable-default-apps',
                '--disable-features=TranslateUI',
                '--disable-translate',
                '--hide-scrollbars'
            ]
            
            # 方式1: 系统 Chrome
            try:
                browser = p.chromium.launch(
                    headless=True,
                    executable_path='/usr/local/bin/google-chrome',
                    args=browser_args
                )
                print("✓ 使用系统 Chrome", file=sys.stderr)
            except Exception as e1:
                print(f"系统 Chrome 启动失败: {e1}", file=sys.stderr)
                
                # 方式2: Playwright 自带浏览器
                try:
                    browser = p.chromium.launch(
                        headless=True,
                        args=['--no-sandbox', '--disable-setuid-sandbox']
                    )
                    print("✓ 使用 Playwright 自带浏览器", file=sys.stderr)
                except Exception as e2:
                    print(f"Playwright 浏览器启动失败: {e2}", file=sys.stderr)
                    return use_requests_fallback(url)
            
            # 创建上下文
            context = browser.new_context(
                viewport=final_viewport,
                user_agent=user_agent,
                java_script_enabled=True,
                locale='zh-CN',
                timezone_id='Asia/Shanghai'
            )
            
            # 加载 cookies（如果指定）
            if load_cookies_domain:
                all_cookies = load_cookies()
                if load_cookies_domain in all_cookies:
                    cookies = all_cookies[load_cookies_domain]
                    context.add_cookies(cookies)
                    print(f"已加载 {len(cookies)} 个 cookies", file=sys.stderr)
            
            page = context.new_page()
            
            # 注入所有终极反检测脚本
            stealth_scripts = setup_ultimate_stealth_scripts()
            for script in stealth_scripts:
                try:
                    page.add_init_script(script)
                except:
                    pass
            
            # 访问页面
            print(f"访问: {url}", file=sys.stderr)
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # 智能等待页面加载
            smart_wait_for_content(page)
            
            # 获取页面信息
            result["title"] = page.title()
            result["final_url"] = page.url
            
            # 执行操作序列
            if actions:
                for i, action in enumerate(actions):
                    action_type = action.get("type")
                    print(f"操作 {i+1}: {action_type}", file=sys.stderr)
                    
                    try:
                        if action_type == "click":
                            selector = action.get("selector")
                            page.wait_for_selector(selector, timeout=5000)
                            # 模拟人类鼠标移动
                            human_mouse_move(page, selector)
                            page.click(selector)
                            result["actions_results"].append({"action": action_type, "status": "success"})
                            time.sleep(random.uniform(0.5, 1.5))
                            
                        elif action_type == "double_click":
                            selector = action.get("selector")
                            human_mouse_move(page, selector)
                            page.dblclick(selector, timeout=5000)
                            result["actions_results"].append({"action": action_type, "status": "success"})
                            
                        elif action_type == "right_click":
                            selector = action.get("selector")
                            human_mouse_move(page, selector)
                            page.click(selector, button="right")
                            result["actions_results"].append({"action": action_type, "status": "success"})
                            
                        elif action_type == "hover":
                            selector = action.get("selector")
                            human_mouse_move(page, selector)
                            page.hover(selector)
                            result["actions_results"].append({"action": action_type, "status": "success"})
                            
                        elif action_type == "fill":
                            selector = action.get("selector")
                            value = action.get("value", "")
                            page.fill(selector, value, timeout=5000)
                            result["actions_results"].append({"action": action_type, "status": "success"})
                            
                        elif action_type == "type":
                            selector = action.get("selector")
                            text = action.get("text", "")
                            # 模拟人类打字速度
                            for char in text:
                                page.type(selector, char, delay=random.randint(50, 150))
                            result["actions_results"].append({"action": action_type, "status": "success"})
                            
                        elif action_type == "keyboard":
                            key = action.get("key", "")
                            page.keyboard.press(key)
                            result["actions_results"].append({"action": action_type, "status": "success"})
                            
                        elif action_type == "drag":
                            source = action.get("source")
                            target = action.get("target")
                            page.drag_and_drop(source, target)
                            result["actions_results"].append({"action": action_type, "status": "success"})
                            
                        elif action_type == "screenshot":
                            path = action.get("path", "/tmp/screenshot.png")
                            full = action.get("full_page", True)
                            page.screenshot(path=path, full_page=full)
                            result["screenshot_path"] = path
                            result["actions_results"].append({"action": action_type, "path": path, "status": "success"})
                            
                        elif action_type == "wait":
                            seconds = action.get("seconds", 1)
                            time.sleep(seconds)
                            result["actions_results"].append({"action": action_type, "seconds": seconds, "status": "success"})
                            
                        elif action_type == "wait_for":
                            selector = action.get("selector")
                            timeout = action.get("timeout", 5000)
                            page.wait_for_selector(selector, timeout=timeout)
                            result["actions_results"].append({"action": action_type, "selector": selector, "status": "success"})
                            
                        elif action_type == "extract":
                            selector = action.get("selector")
                            try:
                                text = page.locator(selector).first.inner_text()
                            except:
                                text = page.locator(selector).inner_text()
                            result["actions_results"].append({"action": action_type, "text": text, "status": "success"})
                            
                        elif action_type == "evaluate":
                            script = action.get("script")
                            eval_result = page.evaluate(script)
                            result["actions_results"].append({"action": action_type, "result": str(eval_result), "status": "success"})
                            
                        elif action_type == "scroll_to":
                            x = action.get("x", 0)
                            y = action.get("y", 0)
                            page.evaluate(f"window.scrollTo({x}, {y})")
                            time.sleep(0.5)
                            result["actions_results"].append({"action": action_type, "status": "success"})
                            
                        elif action_type == "scroll_to_bottom":
                            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            time.sleep(2)
                            result["actions_results"].append({"action": action_type, "status": "success"})
                            
                        elif action_type == "scroll_to_top":
                            page.evaluate("window.scrollTo(0, 0)")
                            time.sleep(1)
                            result["actions_results"].append({"action": action_type, "status": "success"})
                            
                        elif action_type == "save_cookies":
                            cookies = context.cookies()
                            result["cookies"] = cookies
                            if save_cookies_domain:
                                save_cookies(save_cookies_domain, cookies)
                                print(f"已保存 {len(cookies)} 个 cookies", file=sys.stderr)
                            result["actions_results"].append({"action": action_type, "count": len(cookies), "status": "success"})
                            
                    except Exception as e:
                        result["actions_results"].append({"action": action_type, "status": "failed", "error": str(e)})
                        print(f"操作失败: {str(e)}", file=sys.stderr)
            
            # 默认截图（如果没有指定）
            if not result.get("screenshot_path") and not any(a.get("type") == "screenshot" for a in (actions or [])):
                screenshot_path = "/tmp/auto_screenshot.png"
                page.screenshot(path=screenshot_path, full_page=True)
                result["screenshot_path"] = screenshot_path
            
            # 提取文本和HTML
            try:
                result["text"] = page.inner_text("body")
            except:
                result["text"] = ""
            
            try:
                result["html"] = page.content()
            except:
                result["html"] = ""
            
            # 保存 cookies（如果指定）
            if save_cookies_domain:
                cookies = context.cookies()
                save_cookies(save_cookies_domain, cookies)
                result["cookies"] = cookies
                print(f"已保存 {len(cookies)} 个 cookies", file=sys.stderr)
            
            browser.close()
            
    except Exception as e:
        result["error"] = str(e)
        print(f"错误: {str(e)}", file=sys.stderr)
        return use_requests_fallback(url)
    
    return result

def use_requests_fallback(url):
    """使用 requests 作为备选方案"""
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        return None
    
    result = {
        "url": url,
        "title": "",
        "final_url": url,
        "text": "",
        "html": "",
        "screenshot_path": None,
        "actions_results": [],
        "cookies": None,
        "error": None,
        "method": "requests-fallback",
        "user_agent": None,
        "viewport": None
    }
    
    try:
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        response = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_tag = soup.find('title')
        result["title"] = title_tag.text if title_tag else ""
        
        for script in soup(["script", "style"]):
            script.decompose()
        result["text"] = soup.get_text(separator='\n', strip=True)
        result["html"] = str(soup)
        result["final_url"] = response.url
        
    except Exception as e:
        result["error"] = str(e)
    
    return result

def main():
    parser = argparse.ArgumentParser(description="终极增强版 Web Browser - 最强反检测 v4.1")
    parser.add_argument("url", help="要访问的URL")
    parser.add_argument("--actions", "-a", help="操作JSON或文件路径（@开头）")
    parser.add_argument("--viewport", "-v", help="视口大小，格式: 1920x1080")
    parser.add_argument("--save-cookies", "-sc", help="保存cookies到指定域名")
    parser.add_argument("--load-cookies", "-lc", help="从指定域名加载cookies")
    parser.add_argument("--random-ua", "-ru", action="store_true", help="使用随机User-Agent")
    parser.add_argument("--random-viewport", "-rv", action="store_true", help="使用随机视口大小")
    parser.add_argument("--output", "-o", help="输出JSON文件路径")
    
    args = parser.parse_args()
    
    # 解析视口大小
    viewport_size = None
    if args.viewport:
        w, h = map(int, args.viewport.split('x'))
        viewport_size = {'width': w, 'height': h}
    
    # 解析操作
    actions = None
    if args.actions:
        action_str = args.actions
        if action_str.startswith('@'):
            with open(action_str[1:], 'r', encoding='utf-8') as f:
                actions = json.load(f)
        elif os.path.exists(action_str):
            with open(action_str, 'r', encoding='utf-8') as f:
                actions = json.load(f)
        else:
            actions = json.loads(action_str)
    
    # 执行
    result = browse_ultimate_enhanced(
        url=args.url,
        actions=actions,
        viewport_size=viewport_size,
        save_cookies_domain=args.save_cookies,
        load_cookies_domain=args.load_cookies,
        use_random_ua=args.random_ua,
        use_random_viewport=args.random_viewport
    )
    
    if result is None:
        sys.exit(1)
    
    # 输出结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"结果已保存: {args.output}", file=sys.stderr)
    else:
        if result.get("error"):
            print(f"错误: {result['error']}", file=sys.stderr)
        
        print(f"\n标题: {result['title']}")
        print(f"URL: {result['final_url']}")
        print(f"方法: {result.get('method', 'unknown')}")
        
        if result.get("user_agent"):
            print(f"User-Agent: {result['user_agent'][:50]}...")
        
        if result.get("viewport"):
            print(f"视口: {result['viewport']}")
        
        if result.get("text"):
            print(f"\n内容预览:\n{result['text'][:300]}...")
        
        if result.get('screenshot_path'):
            print(f"\n截图: {result['screenshot_path']}")
        
        if result.get("cookies"):
            print(f"\nCookies: {len(result['cookies'])} 个")
        
        if result["actions_results"]:
            print(f"\n操作结果:")
            for i, ar in enumerate(result["actions_results"]):
                print(f"  {i+1}. {ar['action']}: {ar['status']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
