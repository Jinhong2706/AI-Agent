#!/usr/bin/env python3
"""全维度分析 — 7位分析师协作"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.cache_manager import CacheManager
from core.data_providers.stock_price import StockPriceProvider
from core.data_providers.akshare_provider import AkShareProvider
from core.data_providers.news_provider import NewsProvider
from core.agents import AnalystTeam
from core.local_llm import LocalLLM
from core.skill_manager import SkillManager

def main():
    if len(sys.argv) < 2:
        print("用法: python full_analysis.py 600519")
        sys.exit(1)
    code = sys.argv[1]

    # 初始化
    cache = CacheManager()
    providers = {
        "akshare": AkShareProvider(cache),
        "stock_price": StockPriceProvider(cache),
        "news": NewsProvider(cache),
    }

    print(f"\n{'='*60}")
    print(f"  📊 AI-Stock-Researcher 全维度分析 — {code}")
    print(f"{'='*60}\n")

    # 1. 行情
    print("📈 [1/4] 获取实时行情...")
    quote = providers["stock_price"].get(code)
    if quote.get("status") == "success":
        print(f"  {quote['name']}  {quote['price']}  {quote['change_pct']:+.2f}%")
    else:
        print(f"  ⚠️ 行情: {quote.get('msg', '未知')}")

    # 2. 7位分析师
    print("\n🤖 [2/4] 7位分析师多维度评估...")
    team = AnalystTeam(providers)
    analysis = team.analyze(code)
    print(f"  综合评分: {analysis['overall_score']}/100")
    print(f"  投资建议: {analysis['recommendation']}")
    for name, d in analysis.get("dimensions", {}).items():
        s = d.get("score", "?")
        bar = "█" * (s // 5) + "░" * (20 - s // 5) if isinstance(s, int) else "─" * 20
        print(f"  {bar} {name}: {s}/100")

    # 3. 技能状态
    print("\n🔧 [3/4] 技能状态检查...")
    sm = SkillManager()
    status = sm.get_summary()
    print(f"  可用: {status['ok_count']}/{status['total']}")

    # 4. LLM分析
    print("\n🧠 [4/4] AI综合分析...")
    llm = LocalLLM()
    result = llm.analyze_stock(code, analysis)
    print(f"  {result[:500]}")

    print(f"\n{'='*60}")
    print(f"  分析完成！")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
