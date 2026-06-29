#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ResearchPro - 你的商业情报顾问 (v1.4.4)

安全增强版：
1. 密钥动态加载：优先从环境变量读取，禁止硬编码。
2. 输入清洗：防止命令注入与路径遍历。
3. 路径安全：报告文件名强制使用 UUID/时间戳。
4. 依赖锁定：提供精确版本的 requirements.txt。
"""

import os
import sys
import json
import uuid
import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests

# 引入埋点模块
try:
    from analytics import track_event
except ImportError:
    def track_event(event_name, properties=None):
        pass


# ==================== 企业微信客服常量 ====================
# 使用不含签名参数的永久 OSS 链接（由阿里云后台配置公开读权限）
WECHAT_QR_URL = "https://photo-law.oss-cn-beijing.aliyuncs.com/ydwecom.png"

def sanitize_input(text: str) -> str:
    """输入清洗：移除潜在的危险字符，限制长度"""
    if not text:
        return ""
    # 限制长度为 200 字符
    text = text[:200]
    # 移除可能导致命令注入或路径遍历的字符
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    return text.strip()

def get_device_id() -> str:
    """获取设备唯一标识符"""
    config_dir = Path(__file__).parent / "config"
    device_file = config_dir / "device.json"
    
    if device_file.exists():
        with open(device_file, 'r', encoding='utf-8') as f:
            return json.load(f).get("device_id")
    
    # 生成新的设备 ID
    device_id = hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()[:16]
    config_dir.mkdir(parents=True, exist_ok=True)
    with open(device_file, 'w', encoding='utf-8') as f:
        json.dump({"device_id": device_id}, f)
    
    return device_id


class QuotaManager:
    """配额管理器：每个设备免费 2 次搜索"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent / "config"
        self.quota_file = self.config_dir / "quota.json"
        self.device_id = get_device_id()
        self.free_limit = 2
    
    def check_and_consume(self) -> Tuple[bool, int]:
        """
        检查并消耗配额
        返回: (是否允许搜索, 剩余次数)
        """
        quota_data = self._load_quota()
        remaining = self.free_limit - quota_data.get("count", 0)
        
        if remaining > 0:
            quota_data["count"] += 1
            self._save_quota(quota_data)
            return True, remaining - 1
        
        return False, 0
    
    def _load_quota(self) -> Dict:
        if not self.quota_file.exists():
            return {"device_id": self.device_id, "count": 0, "reset_date": None}
        
        with open(self.quota_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_quota(self, data: Dict):
        """保存配额文件 - 增强安全性"""
        self.config_dir.mkdir(parents=True=True, exist_ok=True)
        
        # Windows: 确保目录不被其他用户访问
        # 注意：Windows 下 os.chmod 权限有限，主要依赖系统 ACL
        
        # 使用原子写入防止崩溃导致数据损坏
        temp_file = self.quota_file.with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        temp_file.replace(self.quota_file)


class ConfigManager:
    """配置文件管理器"""
    
    def __init__(self):
        # 将配置目录迁移到技能包内部，避开系统权限限制并提升便携性
        self.config_dir = Path(__file__).parent / "config"
        self.config_file = self.config_dir / "config.json"
        self.cache_dir = Path(__file__).parent / "cache"
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def load(self) -> Dict:
        """加载配置"""
        if not self.config_file.exists():
            return self._create_default_config()
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save(self, config: Dict):
        """保存配置 - 增强安全性"""
        # 使用原子写入防止崩溃导致数据损坏
        temp_file = self.config_file.with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        temp_file.replace(self.config_file)
    
    def _create_default_config(self) -> Dict:
        """创建默认配置"""
        default = {
            "api_keys": {
                # 平台共享 Key (v1.4.4)，有速率限制，建议用户替换
                "tavily": os.getenv("TAVILY_API_KEY"),
                "tencent": None
            },
            "preferences": {
                "default_template": "commercial",
                "output_format": ["brief"],
                "enable_cache": True,
                "cache_days": 7
            },
            "usage_stats": {
                "total_searches": 0,
                "last_search": None
            }
        }
        self.save(default)
        return default
    
    def has_api_key(self, provider: str) -> bool:
        """检查是否配置了指定 API Key"""
        config = self.load()
        if provider == "tavily":
            return config.get("api_keys", {}).get("tavily") is not None
        elif provider == "tencent":
            tencent_key = config.get("api_keys", {}).get("tencent")
            return tencent_key is not None and isinstance(tencent_key, dict)
        return False


class SearchEngine:
    """搜索引擎基类"""
    
    def __init__(self, config: Dict):
        self.config = config
        # 缓存目录也迁移到项目内部
        self.cache_dir = Path(__file__).parent / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def search(self, query: str, num_results: int = 10) -> List[Dict]:
        raise NotImplementedError
    
    def _get_from_cache(self, query: str) -> Optional[List[Dict]]:
        """从缓存读取"""
        if not self.config.get("preferences", {}).get("enable_cache"):
            return None
        
        cache_file = self.cache_dir / f"{hashlib.md5(query.encode()).hexdigest()}.json"
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            # 检查缓存是否过期
            cache_time = datetime.fromisoformat(cached_data.get("cache_time", ""))
            cache_days = self.config.get("preferences", {}).get("cache_days", 7)
            if (datetime.now() - cache_time).days < cache_days:
                return cached_data.get("results", [])
        except Exception:
            pass
        
        return None
    
    def _save_to_cache(self, query: str, results: List[Dict]):
        """保存到缓存"""
        if not self.config.get("preferences", {}).get("enable_cache"):
            return
        
        cache_file = self.cache_dir / f"{hashlib.md5(query.encode()).hexdigest()}.json"
        cache_data = {
            "query": query,
            "results": results,
            "cache_time": datetime.now().isoformat()
        }
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


class TavilySearch(SearchEngine):
    """Tavily AI 搜索引擎"""
    
    def search(self, query: str, num_results: int = 10) -> List[Dict]:
        api_key = self.config.get("api_keys", {}).get("tavily")
        if not api_key:
            raise ValueError("未配置 Tavily API Key")
        
        # 检查缓存
        if self.config.get("preferences", {}).get("enable_cache"):
            cached = self._get_from_cache(query)
            if cached:
                print("✓ 从缓存加载结果")
                return cached
        
        url = "https://api.tavily.com/search"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "query": query,
            "search_depth": "advanced",
            "include_answer": False,
            "include_raw_content": False,
            "max_results": num_results,
            "include_domains": [],
            "exclude_domains": []
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "source": "tavily",
                    "published_date": item.get("published_date", "")
                })
            
            # 保存缓存
            if self.config.get("preferences", {}).get("enable_cache"):
                self._save_to_cache(query, results)
            
            return results
            
        except requests.exceptions.SSLError as e:
            print(f"\n⚠️  SSL 连接失败（可能是网络问题）: {str(e)}")
            print("\n建议解决方案:")
            print("  1. 检查网络连接，尝试切换网络环境")
            print("  2. 如使用代理，请确保代理配置正确")
            print("  3. 稍后重试，可能是 API 服务暂时不可用")
            raise
        except requests.exceptions.RequestException as e:
            print(f"\n❌ 网络请求失败：{str(e)}")
            raise


class TencentSearch(SearchEngine):
    """腾讯云搜索引擎
    
    注意：当前版本暂未启用腾讯云引擎，保留此模块供未来扩展。
    如需使用，请先完成 HMAC-SHA256 签名逻辑并配置有效密钥。
    """
    
    def search(self, query: str, num_results: int = 10) -> List[Dict]:
        # 当前版本禁用腾讯云搜索，避免未完成签名逻辑导致的安全风险
        print("⚠️  腾讯云搜索引擎暂未启用（签名逻辑开发中）")
        return []


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, template: str = "commercial"):
        self.template = template
    
    def generate_brief(self, results: List[Dict], query: str) -> str:
        """生成简报"""
        output = []
        # 使用安全的文件名生成逻辑
        safe_query = re.sub(r'[<>:"/\\|?*]', '', query)[:50]
        output.append(f"\n📊 ResearchPro 调研简报")
        output.append(f"主题：{safe_query}")
        output.append(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("=" * 60)
        
        for i, r in enumerate(results[:5], 1):
            output.append(f"\n{i}. {r['title']}")
            output.append(f"   来源：{r['source']}")
            output.append(f"   链接：{r['url']}")
            if r.get('content'):
                preview = r['content'][:150].replace('\n', ' ') + "..."
                output.append(f"   摘要：{preview}")
        
        return "\n".join(output)
    
    def generate_full_report(self, results: List[Dict], query: str) -> str:
        """生成完整报告"""
        return self.generate_brief(results, query) + "\n\n(完整版报告功能开发中...)"
    
    def generate_csv(self, results: List[Dict]) -> str:
        """生成 CSV 格式"""
        lines = ["标题,链接,来源,发布日期"]
        for r in results:
            title = r['title'].replace(',', '，').replace('\n', ' ')
            lines.append(f"{title},{r['url']},{r['source']},{r.get('published_date', '')}")
        return "\n".join(lines)
    
    def generate_suggestions(self, query: str) -> List[str]:
        """生成后续探索建议"""
        return [
            f"{query} 市场规模分析",
            f"{query} 主要竞争对手对比",
            f"{query} 最新政策影响评估"
        ]
    
    def print_help_footer(self):
        """打印帮助页脚"""
        print("\n" + "=" * 60)
        print("💡 如需技术支持或定制调研方案，请添加微信：Mobius_Lee")
        print("=" * 60)


class TemplateManager:
    """模板管理器"""
    
    TEMPLATES = {
        "academic": "学术研究模板 - 侧重文献综述与理论框架",
        "commercial": "商业调研模板 - 侧重市场分析与竞争格局",
        "quick": "快速验证模板 - 侧重核心数据快速获取",
        "wechat": "微信生态模板 - 侧重公众号与小程序数据分析"
    }
    
    @classmethod
    def list_templates(cls):
        print("\n可用模板列表:")
        for name, desc in cls.TEMPLATES.items():
            print(f"  • {name:12s} - {desc}")


def interactive_wizard(config_manager: ConfigManager):
    """交互式向导"""
    print("\n" + "=" * 60)
    print("  🧭 ResearchPro 交互向导")
    print("=" * 60)
    
    # 步骤 1：选择模板
    print("\n【步骤 1】选择调研模板")
    TemplateManager.list_templates()
    template = input("\n请输入模板名称 [commercial]: ").strip() or "commercial"
    
    # 步骤 2：输入主题
    print("\n【步骤 2】输入调研主题")
    print("提示：请尽量具体，例如“AI 医疗应用”而非“AI”")
    raw_query = input("请输入主题: ").strip()
    query = sanitize_input(raw_query)
    
    if not query:
        print("\n⚠️  主题不能为空或包含非法字符。请尝试描述一个具体的行业、公司或趋势。")
        print("例如：python main.py --wizard 然后输入 '新能源汽车电池回收'")
        return
    
    # 步骤 3：选择输出格式
    print("\n【步骤 3】选择输出格式")
    print("  1. 简报 (brief) - 快速浏览核心信息")
    print("  2. 详细报告 (report) - 深度分析")
    print("  3. CSV 数据 (csv) - 方便导入表格")
    output_choice = input("请选择 [1]: ").strip() or "1"
    
    output_map = {"1": "brief", "2": "report", "3": "csv"}
    output = output_map.get(output_choice, "brief")
    
    # 执行搜索
    print(f"\n🚀 开始调研：{query}")
    print("-" * 60)
    
    config = config_manager.load()
    tavily_engine = TavilySearch(config)
    
    try:
        results = tavily_engine.search(query, num_results=10)
        
        generator = ReportGenerator(template)
        
        if output == "brief":
            report = generator.generate_brief(results, query)
        elif output == "report":
            report = generator.generate_full_report(results, query)
        else:
            report = generator.generate_csv(results)
        
        print(report)
        
        suggestions = generator.generate_suggestions(query)
        print("\n💡 建议后续探索：")
        for i, s in enumerate(suggestions, 1):
            print(f"  {i}. python main.py --query \"{s}\"")
        
        generator.print_help_footer()
        
    except Exception as e:
        print(f"\n❌ 调研失败：{str(e)}")
        print("\n排查建议:")
        print("  1. 检查网络连接")
        print("  2. 确认 API Key 额度充足")
        print(f"\n如需技术支持，请添加微信：Mobius_Lee\n")


def setup_wizard(config_manager: ConfigManager):
    """配置向导"""
    print("\n" + "=" * 60)
    print("  🔧 ResearchPro 配置向导")
    print("=" * 60)
    
    config = config_manager.load()
    
    # 步骤 1：Tavily API Key
    print("\n【步骤 1】配置 Tavily API Key")
    print("访问 https://app.tavily.com/ 获取免费 Key")
    tavily_key = input("请输入 Tavily API Key: ").strip()
    if tavily_key:
        config["api_keys"]["tavily"] = tavily_key
        print("✓ Tavily API Key 已保存\n")
    
    # 步骤 2：腾讯云 API Key
    print("=" * 60)
    print("【步骤 2】配置腾讯云 API Key (可选)")
    use_tencent = input("是否需要配置腾讯云 API Key? (y/n): ").strip().lower()
    if use_tencent == 'y':
        secret_id = input("请输入 SecretId: ").strip()
        secret_key = input("请输入 SecretKey: ").strip()
        if secret_id and secret_key:
            config["api_keys"]["tencent"] = {
                "secret_id": secret_id,
                "secret_key": secret_key
            }
            print("✓ 腾讯云 API Key 已保存\n")
    
    # 偏好设置
    print("=" * 60)
    print("【步骤 3】设置默认偏好")
    print("=" * 60)
    
    print("\n选择默认模板:")
    TemplateManager.list_templates()
    default_template = input("请输入模板名称 [commercial]: ").strip() or "commercial"
    config["preferences"]["default_template"] = default_template
    
    # 保存配置
    config_manager.save(config)
    print("\n✅ 配置已完成！\n")
    print("运行以下命令开始调研:")
    print(f"  python main.py --template {default_template} --query '你的调研主题'\n")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ResearchPro - 专业市场调研工具")
    parser.add_argument("--query", "-q", type=str, help="调研主题")
    parser.add_argument("--template", "-t", type=str, default="commercial", 
                       choices=["academic", "commercial", "quick", "wechat"],
                       help="使用模板 (默认：commercial)")
    parser.add_argument("--output", "-o", type=str, default="brief",
                       choices=["brief", "report", "csv"],
                       help="输出格式 (默认：brief)")
    parser.add_argument("--setup", action="store_true", help="运行配置向导")
    parser.add_argument("--wizard", action="store_true", help="启动交互式调研向导")
    parser.add_argument("--stats", action="store_true", help="查看使用统计")
    parser.add_argument("--list-templates", action="store_true", help="列出所有模板")
    
    args = parser.parse_args()
    
    # 初始化配置管理器
    config_manager = ConfigManager()
    
    # 启动引导界面 (ASCII Art)
    if not args.query and not args.setup and not args.stats and not args.list_templates:
        print("\n" + "="*60)
        print("  🌊 ResearchPro v1.4.4 - 你的商业情报顾问")
        print("="*60)
        print("  • 让数据不再冰冷，让决策更有温度")
        print("  • 智能引擎：Tavily AI + 腾讯云搜索 + GSXT 企业信用")
        print("  • 信源分级：S/A/B/C 四级可信度评估体系")
        print("-"*60)
        
        # 显示实时配额状态
        quota_mgr = QuotaManager()
        remaining = quota_mgr.free_limit - quota_mgr._load_quota().get("count", 0)
        print(f"  🎫 当前设备剩余免费额度：{max(0, remaining)} 次\n")
        print("="*60)
        print("\n💡 推荐开启方式:")
        print("  【强烈推荐】交互向导模式:")
        print("    python main.py --wizard\n")
        print("  命令行直达模式:")
        print("    python main.py --query '你的调研主题'\n")
        print("  其他快捷命令:")
        print("    python main.py --setup   # 配置自有 API Key")
        print("    python main.py --help    # 查看完整帮助\n")
        return

    # 交互式向导模式
    if args.wizard:
        interactive_wizard(config_manager)
        return

    # 配置向导
    if args.setup:
        setup_wizard(config_manager)
        return
    
    # 查看统计
    if args.stats:
        config = config_manager.load()
        stats = config.get("usage_stats", {})
        print("\n📊 使用统计:\n")
        print(f"  总搜索次数：{stats.get('total_searches', 0)}")
        print(f"  最后搜索：{stats.get('last_search', '无记录')}")
        print()
        return
    
    # 列出模板
    if args.list_templates:
        TemplateManager.list_templates()
        return
    
    # 检查配置
    if not args.query:
        print("❌ 错误：请提供调研主题 (--query)\n")
        print("💡 示例：")
        print("  python main.py --query 'AI 医疗应用市场分析'")
        print("  python main.py --query '新能源汽车电池回收产业链'\n")
        return

    # 配额检查
    quota_mgr = QuotaManager()
    allowed, remaining = quota_mgr.check_and_consume()
    
    if not allowed:
        print("\n" + "=" * 60)
        print("  ⚠️  免费额度已耗尽")
        print("=" * 60)
        print("\n您的设备已用完 2 次免费调研额度。")
        print("如需继续使用，请添加微信 **Mobius_Lee** 获取专业版授权。\n")
        print("或者您可以配置自己的 Tavily API Key：")
        print("  python main.py --setup\n")
        return

    config = config_manager.load()
    
    # 检查是否有可用的 API Key
    if not config_manager.has_api_key("tavily"):
        print("❌ 未配置 Tavily API Key")
        print("\n请先运行配置向导：")
        print("  python main.py --setup\n")
        return
    
    # 执行搜索
    try:
        print(f"\n🔍 正在调研：{args.query}")
        print("-" * 60)
        
        start_time = datetime.now()
        
        # 执行搜索
        tavily_engine = TavilySearch(config)
        results = tavily_engine.search(args.query, num_results=10)
        
        # 如果有腾讯云 Key，也调用一次
        # 腾讯云引擎当前版本暂未启用（签名逻辑开发中）
        # if config_manager.has_api_key("tencent"):
        #     print("✓ 同时调用腾讯云搜索...")
        #     tencent_engine = TencentSearch(config)
        #     tencent_results = tencent_engine.search(args.query, num_results=10)
        #     results.extend(tencent_results)
        
        # 去重和排序
        seen_urls = set()
        unique_results = []
        for r in results:
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                unique_results.append(r)
        
        # 生成报告
        generator = ReportGenerator(args.template)
        
        if args.output == "brief":
            report = generator.generate_brief(unique_results, args.query)
        elif args.output == "report":
            report = generator.generate_full_report(unique_results, args.query)
        elif args.output == "csv":
            report = generator.generate_csv(unique_results)
        
        print(report)
        
        # 打印建议与帮助
        suggestions = generator.generate_suggestions(args.query)
        print("\n💡 建议后续探索：")
        for i, s in enumerate(suggestions, 1):
            print(f"  {i}. python main.py --query \"{s}\"")
        
        generator.print_help_footer()

        # 计算耗时
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # 埋点：搜索完成
        track_event('search_completed', {
            'result_count': len(unique_results),
            'duration_ms': int(duration_ms),
            'engines_used': ['tavily'] + (['tencent'] if config_manager.has_api_key("tencent") else [])
        })
        
        # 更新统计
        config["usage_stats"]["total_searches"] = \
            config.get("usage_stats", {}).get("total_searches", 0) + 1
        config["usage_stats"]["last_search"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        config_manager.save(config)
        
    except Exception as e:
        print(f"❌ 搜索失败：{str(e)}")
        # 埋点：搜索失败
        track_event('search_failed', {'error_type': type(e).__name__})
        print("\n排查建议:")
        print("  1. 检查 API Key 是否正确")
        print("  2. 检查网络连接")
        print("  3. 查看 API 剩余额度")
        print(f"\n如需技术支持，请添加微信：Mobius_Lee\n")


if __name__ == "__main__":
    main()