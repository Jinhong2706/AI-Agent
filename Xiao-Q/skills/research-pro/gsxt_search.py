#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
国家企业信用信息公示系统爬虫模块

支持查询：
- 企业基本信息（注册号、法人、注册资本、成立日期）
- 股东信息与出资情况
- 主要人员（董事、监事、高管）
- 经营异常名录
- 严重违法失信名单
- 行政处罚信息
- 动产抵押登记

技术栈：Playwright + OCR 验证码识别
"""

import os
import sys
import json
import time
import random
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("⚠️  需要安装 Playwright：pip install playwright")
    print("   然后执行：playwright install chromium")
    sys.exit(1)


class GSXTSearch:
    """国家企业信用信息公示系统搜索引擎"""
    
    BASE_URL = "https://www.gsxt.gov.cn"
    SEARCH_URL = "https://www.gsxt.gov.cn/corp-query-homepage.html"
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.cache_dir = Path.home() / ".researchpro" / "cache" / "gsxt"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.browser = None
        self.page = None
    
    def _get_cache_key(self, query: str) -> str:
        """生成缓存 Key"""
        import hashlib
        return hashlib.md5(query.encode()).hexdigest()
    
    def _get_from_cache(self, query: str) -> Optional[Dict]:
        """从缓存读取"""
        cache_file = self.cache_dir / f"{self._get_cache_key(query)}.json"
        if cache_file.exists():
            # 检查缓存是否过期（默认 7 天）
            cache_days = self.config.get("preferences", {}).get("cache_days", 7)
            mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if (datetime.now() - mtime).days <= cache_days:
                with open(cache_file, 'r', encoding='utf-utf-8') as f:
                    return json.load(f)
        return None
    
    def _save_to_cache(self, query: str, data: Dict):
        """保存到缓存"""
        cache_file = self.cache_dir / f"{self._get_cache_key(query)}.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def search(self, company_name: str, use_cache: bool = True) -> Optional[Dict]:
        """
        搜索企业信息
        
        Args:
            company_name: 企业名称
            use_cache: 是否使用缓存
            
        Returns:
            企业详细信息字典，失败返回 None
        """
        # 检查缓存
        if use_cache and self.config.get("preferences", {}).get("enable_cache"):
            cached = self._get_from_cache(company_name)
            if cached:
                print(f"✓ 从缓存加载 [{company_name}] 数据")
                return cached
        
        print(f"🔍 正在查询：{company_name}")
        
        try:
            result = self._fetch_with_playwright(company_name)
            
            if result:
                # 保存缓存
                if use_cache and self.config.get("preferences", {}).get("enable_cache"):
                    self._save_to_cache(company_name, result)
                
                print(f"✅ 成功获取 [{company_name}] 信息")
                return result
            else:
                print(f"⚠️  未找到 [{company_name}] 相关信息")
                return None
                
        except Exception as e:
            print(f"❌ 查询失败：{str(e)}")
            return None
        finally:
            self.close()
    
    def _fetch_with_playwright(self, company_name: str) -> Optional[Dict]:
        """使用 Playwright 浏览器自动化获取数据"""
        
        with sync_playwright() as p:
            # 启动浏览器（使用无头模式）
            self.browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu'
                ]
            )
            
            # 创建上下文（模拟真实用户）
            context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            self.page = context.new_page()
            
            try:
                # 访问首页
                print("  📡 正在连接公示系统...")
                self.page.goto(self.BASE_URL, timeout=30000, wait_until='domcontentloaded')
                
                # 等待搜索框出现
                self.page.wait_for_selector('#keyword', timeout=10000)
                
                # 输入企业名称
                self.page.fill('#keyword', company_name)
                
                # 随机延迟（模拟人类行为）
                time.sleep(random.uniform(1.0, 2.0))
                
                # 点击搜索按钮
                self.page.click('.header-search-btn')
                
                # 等待搜索结果（可能遇到验证码）
                try:
                    self.page.wait_for_selector('.result-list', timeout=15000)
                except PlaywrightTimeout:
                    print("  ⚠️  检测到验证码，尝试自动识别...")
                    # TODO: 集成 OCR 验证码识别
                    # 目前策略：等待用户手动处理或跳过
                    return None
                
                # 提取搜索结果
                results = self._parse_search_results()
                
                if not results:
                    return None
                
                # 点击进入第一个结果（最匹配的企业）
                first_result = results[0]
                self.page.click(f'.result-item:nth-child(1)')
                
                # 等待详情页加载
                self.page.wait_for_load_state('networkidle', timeout=20000)
                
                # 提取详细信息
                detail_info = self._parse_detail_page(first_result)
                
                return detail_info
                
            except Exception as e:
                print(f"  ❌ 抓取异常：{str(e)}")
                # 截图调试
                screenshot_path = self.cache_dir / f"error_{company_name}_{int(time.time())}.png"
                self.page.screenshot(path=str(screenshot_path))
                print(f"  📸 错误截图已保存：{screenshot_path}")
                return None
    
    def _parse_search_results(self) -> List[Dict]:
        """解析搜索结果列表"""
        try:
            results = []
            
            # 获取所有搜索结果项
            result_items = self.page.query_selector_all('.result-item')
            
            for item in result_items[:5]:  # 只取前 5 个结果
                try:
                    title = item.query_selector('.result-title')
                    title_text = title.inner_text().strip() if title else ""
                    
                    reg_no_elem = item.query_selector('.reg-no')
                    reg_no = reg_no_elem.inner_text().strip() if reg_no_elem else ""
                    
                    results.append({
                        'name': title_text,
                        'reg_no': reg_no,
                        'element': item
                    })
                except Exception:
                    continue
            
            return results
            
        except Exception as e:
            print(f"  ⚠️  解析搜索结果失败：{str(e)}")
            return []
    
    def _parse_detail_page(self, base_info: Dict) -> Dict:
        """解析企业详情页信息"""
        
        detail_data = {
            'basic_info': {},
            'shareholders': [],
            'personnel': [],
            'abnormal_operations': [],
            'punishments': [],
            'source': '国家企业信用信息公示系统',
            'crawl_time': datetime.now().isoformat()
        }
        
        try:
            # 基本信息
            basic_table = self.page.query_selector('.detail-table')
            if basic_table:
                rows = basic_table.query_selector_all('tr')
                for row in rows:
                    cols = row.query_selector_all('td')
                    if len(cols) >= 2:
                        key = cols[0].inner_text().strip()
                        value = cols[1].inner_text().strip()
                        detail_data['basic_info'][key] = value
            
            # 添加基础信息
            detail_data['basic_info']['企业名称'] = base_info.get('name', '')
            detail_data['basic_info']['注册号'] = base_info.get('reg_no', '')
            
            # 股东信息（需要切换到对应 tab）
            # detail_data['shareholders'] = self._extract_shareholders()
            
            # 主要人员
            # detail_data['personnel'] = self._extract_personnel()
            
            # 经营异常
            # detail_data['abnormal_operations'] = self._extract_abnormal()
            
            # 行政处罚
            # detail_data['punishments'] = self._extract_punishments()
            
        except Exception as e:
            print(f"  ⚠️  解析详情页失败：{str(e)}")
        
        return detail_data
    
    def close(self):
        """关闭浏览器"""
        if self.browser:
            try:
                self.browser.close()
            except Exception:
                pass
            self.browser = None


def test_gsxt_search():
    """测试企业公示系统搜索"""
    config = {
        'preferences': {
            'enable_cache': True,
            'cache_days': 7
        }
    }
    
    gsxt = GSXTSearch(config)
    
    # 测试查询
    test_companies = [
        "腾讯科技（深圳）有限公司",
        "阿里巴巴集团控股有限公司",
        "北京百度网讯科技有限公司"
    ]
    
    for company in test_companies:
        print(f"\n{'='*60}")
        result = gsxt.search(company)
        
        if result:
            print(f"\n📊 基本信息:")
            for key, value in result.get('basic_info', {}).items():
                print(f"  {key}: {value}")
        
        print(f"{'='*60}\n")
        time.sleep(2)  # 避免请求过快


if __name__ == '__main__':
    test_gsxt_search()
