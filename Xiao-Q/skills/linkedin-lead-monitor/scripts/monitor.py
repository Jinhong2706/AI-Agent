#!/usr/bin/env python3
"""
LinkedIn 潜客监控 - 主监控逻辑（简化版）
负责浏览器自动化、数据采集、动态检测
"""

import sqlite3
import json
import os
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

DB_PATH = Path(__file__).parent.parent / 'data' / 'leads.db'
STATE_DIR = Path(__file__).parent.parent / 'data' / 'state'


class LinkedInMonitor:
    def __init__(self):
        self.email = os.getenv('LINKEDIN_EMAIL', '')
        self.password = os.getenv('LINKEDIN_PASSWORD', '')
        self.headless = os.getenv('HEADLESS', 'false').lower() == 'true'
        self.chrome_user_data = os.getenv('CHROME_USER_DATA', '')
        self.playwright = None
        self.browser = None
        self.page = None
    
    def start_browser(self):
        """启动浏览器 - 简化版：直接使用新浏览器 + 自动登录"""
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        
        print(f"[INFO] 启动浏览器...")
        
        self.playwright = sync_playwright().start()
        
        # 简单模式：新浏览器 + 持久化上下文
        print("[INFO] 使用持久化上下文启动浏览器...")
        profile_dir = str(STATE_DIR / 'linkedin-profile')
        print(f"[INFO] 配置文件：{profile_dir}")
        
        try:
            self.browser = self.playwright.chromium.launch_persistent_context(
                user_data_dir=profile_dir,
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
            self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()
            print("[OK] 浏览器启动成功")
            
            # 等待一下让页面加载
            time.sleep(2)
            
            # 检查是否已登录（不跳转，直接检查当前状态）
            print("[INFO] 检查登录状态...")
            try:
                self.page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=15000)
                time.sleep(2)  # 等待页面渲染
                
                if self.is_logged_in():
                    print("[OK] 已登录 LinkedIn（使用保存的会话）")
                    # 保存登录状态
                    self.save_storage()
                    return self.page
            except Exception as e:
                print(f"[INFO] 登录状态检查：{e}")
            
            # 未登录，尝试自动登录
            if self.email and self.password:
                print("[INFO] 执行自动登录...")
                if self.login():
                    print("[OK] 登录成功")
                    return self.page
            
            print("[WARN] 未登录，但继续执行...")
            return self.page
            
        except Exception as e:
            print(f"[ERROR] 浏览器启动失败：{e}")
            raise
    
    def is_logged_in(self) -> bool:
        """检查是否已登录 LinkedIn"""
        try:
            # 快速检查：直接访问 feed 页面
            self.page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=15000)
            
            # 多种检测方式
            # 1. 检查是否有 feed 页面元素
            feed_elem = self.page.query_selector('.feed-right-sidebar, .feed-left-sidebar')
            if feed_elem:
                print("[OK] 检测到已登录状态 (feed 页面)")
                return True
            
            # 2. 检查 URL 是否包含 /feed/
            current_url = self.page.url
            if '/feed/' in current_url:
                print("[OK] 检测到已登录状态 (URL)")
                return True
            
            # 3. 检查是否有登录用户头像
            avatar = self.page.query_selector('img[data-litms-control*="avatar"]')
            if avatar:
                print("[OK] 检测到已登录状态 (头像)")
                return True
            
            print("[INFO] 未检测到登录状态")
            return False
            
        except Exception as e:
            print(f"[INFO] 登录检测异常：{e}")
            return False
    
    def login(self) -> bool:
        """手动登录 LinkedIn - 打开登录页，等待用户手动完成"""
        try:
            print("[INFO] 打开 LinkedIn 登录页面...")
            print("[INFO] 请在浏览器中手动完成登录（30 秒内）")
            
            self.page.goto('https://www.linkedin.com/login', wait_until='domcontentloaded', timeout=30000)
            
            # 等待用户手动登录（最多 30 秒）
            for i in range(6):  # 30 秒，每 5 秒检查一次
                time.sleep(5)
                
                # 检查是否已登录
                if self.is_logged_in():
                    print("[OK] 检测到已登录")
                    # 保存登录状态
                    self.save_storage()
                    return True
                
                print(f"[INFO] 等待登录完成... ({(i+1)*5}s)")
            
            print("[WARN] 等待超时")
            return False
                
        except Exception as e:
            print(f"[ERROR] 登录异常：{e}")
            return False
    
    def save_storage(self):
        """保存登录状态到文件"""
        try:
            storage = self.page.context.storage_state()
            storage_path = STATE_DIR / 'storage.json'
            with open(storage_path, 'w', encoding='utf-8') as f:
                json.dump(storage, f, indent=2)
            print(f"[OK] 已保存登录状态到：{storage_path}")
        except Exception as e:
            print(f"[WARN] 保存登录状态失败：{e}")
    
    def check_profile(self, url: str) -> dict:
        """检查潜客主页，获取最新信息"""
        try:
            print(f"[INFO] 检查主页：{url}")
            
            # 使用更宽松的加载策略
            self.page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            # 等待页面加载（LinkedIn 可能较慢）
            print("[INFO] 等待页面加载...")
            time.sleep(5)
            
            # 调试：输出页面结构
            self.debug_page_content()
            
            # 使用 JavaScript 直接提取数据（更可靠）
            print("[INFO] 使用 JavaScript 提取数据...")
            
            try:
                # 执行 JavaScript 提取个人信息
                profile_data = self.page.evaluate('''() => {
                    const result = { name: '', headline: '', company: '', position: '' };
                    
                    // 尝试多种选择器获取姓名
                    const nameSelectors = [
                        'h1',
                        '.text-heading-xlarge',
                        '[class*="profile-name"]',
                        '#profile-content h1'
                    ];
                    for (const sel of nameSelectors) {
                        const el = document.querySelector(sel);
                        if (el && el.textContent.trim()) {
                            result.name = el.textContent.trim();
                            break;
                        }
                    }
                    
                    // 获取职位/标题
                    const headlineSelectors = [
                        '.text-body-medium',
                        '.text-body-small',
                        '[class*="headline"]',
                        'div[class*="title"]'
                    ];
                    for (const sel of headlineSelectors) {
                        const el = document.querySelector(sel);
                        if (el && el.textContent.trim()) {
                            result.headline = el.textContent.trim();
                            break;
                        }
                    }
                    
                    // 获取公司信息
                    const companyLink = document.querySelector('a[href*="/company/"]');
                    if (companyLink) {
                        result.company = companyLink.textContent.trim();
                    }
                    
                    // 从 headline 中提取职位（通常格式：职位 at 公司）
                    if (result.headline) {
                        const parts = result.headline.split(' at ');
                        if (parts.length >= 2) {
                            result.position = parts[0];
                            if (!result.company) result.company = parts[1];
                        }
                    }
                    
                    return result;
                }''')
                
                print(f"[OK] JavaScript 提取结果：{profile_data}")
                
                result = {
                    'name': profile_data.get('name') or '未知',
                    'headline': profile_data.get('headline') or '未知',
                    'company': profile_data.get('company') or '未知',
                    'position': profile_data.get('position') or '未知',
                    'checked_at': datetime.now().isoformat()
                }
                
            except Exception as e:
                print(f"[WARN] JavaScript 提取失败：{e}")
                result = {
                    'name': '未知',
                    'headline': '未知',
                    'company': '未知',
                    'position': '未知',
                    'checked_at': datetime.now().isoformat()
                }
            
            print(f"[OK] 获取到信息：{result}")
            return result
            
        except Exception as e:
            print(f"[ERROR] 检查主页失败 {url}: {e}")
            return None
    
    def check_activities(self, url: str) -> list:
        """检查潜客动态 - 从个人主页直接抓取最新动态"""
        activities = []
        
        try:
            print(f"[INFO] 检查动态：{url}")
            
            # 已经在个人主页，直接查找动态部分
            # 使用用户提供的选择器：#profile-content > div > div.scaffold-layout... > main > section
            activity_section = self.page.query_selector('#profile-content main section')
            
            if not activity_section:
                print("[WARN] 未找到动态区域，尝试访问动态页面...")
                # 备用方案：访问动态页面
                activity_url = url.rstrip('/') + '/recent-activity/all/'
                print(f"[INFO] 访问：{activity_url}")
                self.page.goto(activity_url, wait_until='domcontentloaded', timeout=60000)
                time.sleep(5)
            
            # 使用 JavaScript 提取动态列表
            print("[INFO] 使用 JavaScript 提取动态...")
            
            try:
                posts_data = self.page.evaluate('''() => {
                    const posts = [];
                    
                    // 简单方案：获取 main 区域内的所有有内容的 div
                    const main = document.querySelector('main');
                    if (!main) return posts;
                    
                    const allDivs = main.querySelectorAll('div');
                    
                    for (const div of allDivs) {
                        const text = div.textContent.trim();
                        
                        // 清理文本
                        let cleanText = text
                            .replace(/• 已关注/g, '')
                            .replace(/查看资料/g, '')
                            .replace(/\\s+/g, ' ')
                            .trim();
                        
                        // 过滤：长度适中，包含中文字符（说明是有意义的内容）
                        if (cleanText.length > 50 && cleanText.length < 500) {
                            // 检查是否包含中文字符
                            const hasChinese = /[\\u4e00-\\u9fa5]/.test(cleanText);
                            if (hasChinese) {
                                // 检查是否重复
                                const isDuplicate = posts.some(p => p.content === cleanText);
                                if (!isDuplicate) {
                                    posts.push({
                                        content: cleanText,
                                        type: 'post'
                                    });
                                }
                            }
                        }
                        
                        // 只取前 5 条
                        if (posts.length >= 5) break;
                    }
                    
                    return posts;
                }''')
                
                if posts_data:
                    for i, post in enumerate(posts_data[:5], 1):
                        activities.append({
                            'content': post.get('content', '')[:500],
                            'timestamp': '',
                            'type': post.get('type', 'post')
                        })
                        print(f"  {i}. [{post.get('type', 'post')}] {post.get('content', '')[:100]}...")
                    
                    print(f"[OK] 获取到 {len(activities)} 条动态")
                else:
                    print("[WARN] 未找到动态内容")
                
            except Exception as e:
                print(f"[WARN] JavaScript 提取失败：{e}")
            
        except Exception as e:
            print(f"[ERROR] 检查动态失败：{e}")
        
        return activities
    
    def safe_extract_text(self, selector: str) -> str:
        """安全提取文本"""
        try:
            # 尝试多种选择器
            selectors = selector.split(',') if ',' in selector else [selector]
            for sel in selectors:
                element = self.page.query_selector(sel.strip())
                if element:
                    text = element.inner_text().strip()
                    if text:
                        return text
            return ''
        except Exception as e:
            return ''
    
    def debug_page_content(self):
        """调试：输出页面主要内容结构"""
        try:
            # 获取页面标题
            title = self.page.title()
            print(f"[DEBUG] 页面标题：{title}")
            
            # 获取所有 h1 标签
            h1s = self.page.query_selector_all('h1')
            if h1s:
                print(f"[DEBUG] H1 标签：{[h.inner_text().strip() for h in h1s[:3]]}")
            else:
                print("[DEBUG] 未找到 H1 标签")
            
            # 获取 URL
            print(f"[DEBUG] 当前 URL: {self.page.url}")
            
            # 获取 body 的 HTML 长度
            html = self.page.content()
            print(f"[DEBUG] HTML 长度：{len(html)}")
            
            # 保存截图
            screenshot_path = STATE_DIR / 'debug-screenshot.png'
            self.page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"[DEBUG] 截图已保存：{screenshot_path}")
            
        except Exception as e:
            print(f"[DEBUG] 错误：{e}")
    
    def safe_extract_timestamp(self, element) -> str:
        """安全提取时间戳"""
        try:
            time_elem = element.query_selector('time')
            if time_elem:
                return time_elem.get_attribute('datetime', '')
            return ''
        except:
            return ''
    
    def classify_activity(self, content: str) -> str:
        """分类动态类型"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['joined', 'started', 'new role', 'excited to announce']):
            return 'job_change'
        elif any(word in content_lower for word in ['excited', 'announce', 'launch', 'funding']):
            return 'company_update'
        elif any(word in content_lower for word in ['article', 'post', 'thought', 'sharing']):
            return 'post'
        else:
            return 'interaction'
    
    def close(self):
        """关闭浏览器"""
        try:
            if self.browser:
                # 持久化上下文不需要关闭
                if hasattr(self.browser, 'close'):
                    self.browser.close()
            if self.playwright:
                self.playwright.stop()
            print("[OK] 浏览器已关闭")
        except Exception as e:
            print(f"[WARN] 关闭浏览器失败：{e}")


def run_check(lead_name: str = ''):
    """执行检查"""
    from notify import NotificationManager
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取潜客列表
    if lead_name:
        cursor.execute('SELECT id, name, linkedin_url, company, position FROM leads WHERE name = ?', (lead_name,))
    else:
        cursor.execute('SELECT id, name, linkedin_url, company, position, priority FROM leads')
    
    leads = cursor.fetchall()
    
    if not leads:
        print("[INFO] 暂无潜客需要检查")
        return
    
    monitor = LinkedInMonitor()
    notifier = NotificationManager()
    
    try:
        monitor.start_browser()
        
        for lead in leads:
            lead_id, name, url, company, position = lead[:5]
            priority = lead[5] if len(lead) > 5 else 'medium'
            
            print(f"\n{'='*60}")
            print(f"检查潜客：{name}")
            print(f"URL: {url}")
            print(f"{'='*60}")
            
            # 检查主页信息
            profile = monitor.check_profile(url)
            
            # 检查动态
            activities = monitor.check_activities(url)
            
            # 如果有动态，生成报告并发送
            if activities:
                print(f"\n[结果] 发现 {len(activities)} 条动态")
                for i, act in enumerate(activities[:5], 1):
                    print(f"  {i}. [{act['type']}] {act['content'][:100]}...")
                
                # 准备潜客信息
                lead_info = {
                    'name': name,
                    'company': company or (profile.get('company') if profile else '未知') or '未知',
                    'position': position or (profile.get('position') if profile else '未知') or '未知',
                    'linkedin_url': url,
                    'priority': priority
                }
                
                # 去重：过滤已存在的动态
                new_activities = []
                for act in activities:
                    cursor.execute('SELECT id FROM activities WHERE lead_id = ? AND content = ?', 
                                   (lead_id, act['content'][:500]))
                    if not cursor.fetchone():
                        new_activities.append(act)
                
                if new_activities:
                    print(f"\n[推送] 发送 LinkedIn 动态报告（{len(new_activities)} 条新动态）...")
                    notifier.send_dynamic_report(name, new_activities, lead_info)
                    
                    # 保存新动态到数据库
                    for act in new_activities:
                        cursor.execute('''
                            INSERT INTO activities (lead_id, activity_type, content, opportunity_score, opportunity_level, notified)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (lead_id, act['type'], act['content'][:500], 50, 'medium', 0))
                    conn.commit()
                else:
                    print(f"\n[INFO] 无新动态（所有内容已存在）")
            
            # 等待一下，避免触发风控
            time.sleep(3)
    
    finally:
        monitor.close()
        conn.close()
        print(f"\n[OK] 检查完成")


if __name__ == '__main__':
    lead_name = sys.argv[1] if len(sys.argv) > 1 else ''
    run_check(lead_name)
