#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ai-stock-researcher MCP Server — A股智能投研工具
通过 MCP 协议暴露持仓导入/导出、股票研究、技术分析、情绪分析等工具，
让 Claude Code 可以直接调用股票研究员的核心功能。

使用方式（Claude Code 配置 mcpServers）:
{
  "mcpServers": {
    "ai-stock-researcher": {
      "command": "python",
      "args": ["./mcp_server.py"],
      "env": {
        "PYTHONDONTWRITEBYTECODE": "1"
      }
    }
  }
}
"""
from __future__ import annotations

import json
import sys
import os
from pathlib import Path

sys.dont_write_bytecode = True

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR
sys.path.insert(0, str(SKILL_DIR / "scripts"))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
except ImportError:
    print("请安装 MCP SDK: pip install mcp", file=sys.stderr)
    sys.exit(1)

from stock_researcher.import_engine import StockImportEngine
from stock_researcher.industry_chain import (
    IndustryChainAnalyzer, AShareChainAnalyzer,
    get_preset_chain, list_presets,
    ChainNode, CompetitorProfile, SubstitutionProgress,
    StockRecommendation, DynamicAnalysis, ASignals,
)

engine = StockImportEngine()


# ==================== 持仓导入 ====================

@server.tool()
async def import_holdings_screenshot(image_path: str, client_id: str = "") -> str:
    """从截图OCR识别股票/基金持仓。支持中英文混合识别，自动区分股票和基金，
    解析代码、名称、数量、成本价、止盈止损比例。
    适用场景：客户发送了持仓页面截图。

    Args:
        image_path: 截图文件完整路径
        client_id: 客户姓名或ID（可选）
    """
    result = engine.import_from_screenshot(
        image_path, client_id=client_id if client_id else None
    )
    if result['success']:
        items = result['items']
        lines = [f"识别到 {len(items)} 条持仓:"]
        for item in items:
            itype = '股票' if item.get('item_type') == 'stock' else '基金'
            lines.append(
                f"  [{itype}] {item.get('code')} {item.get('name', '未知')} "
                f"数量:{item.get('shares', '?')} 成本:{item.get('cost', '?')}"
            )
        if client_id:
            lines.append(f"已保存到客户「{client_id}」的持仓仓库。")
        return '\n'.join(lines)
    else:
        return f"识别失败: {'; '.join(result['errors'])}"


@server.tool()
async def import_holdings_ppt(file_path: str, client_id: str = "") -> str:
    """从PPT幻灯片导入股票/基金持仓。解析PPT中的表格和文本框内容。
    适用场景：客户提供了PPT格式的资产配置或持仓分析报告。

    Args:
        file_path: PPT文件完整路径
        client_id: 客户姓名或ID（可选）
    """
    result = engine.import_from_ppt(
        file_path, client_id=client_id if client_id else None
    )
    if result['success']:
        items = result['items']
        lines = [f"从PPT识别到 {len(items)} 条持仓:"]
        for item in items:
            itype = '股票' if item.get('item_type') == 'stock' else '基金'
            lines.append(
                f"  [{itype}] {item.get('code')} {item.get('name', '未知')} "
                f"数量:{item.get('shares', '?')} 成本:{item.get('cost', '?')}"
            )
        if client_id:
            lines.append(f"已保存到客户「{client_id}」的持仓仓库。")
        return '\n'.join(lines)
    else:
        return f"导入失败: {'; '.join(result['errors'])}"


@server.tool()
async def import_holdings_docx(file_path: str, client_id: str = "") -> str:
    """从Word文档(.docx)导入股票/基金持仓。

    Args:
        file_path: Word文档完整路径
        client_id: 客户姓名或ID（可选）
    """
    result = engine.import_from_docx(
        file_path, client_id=client_id if client_id else None
    )
    if result['success']:
        items = result['items']
        lines = [f"从Word文档识别到 {len(items)} 条持仓:"]
        for item in items:
            itype = '股票' if item.get('item_type') == 'stock' else '基金'
            lines.append(
                f"  [{itype}] {item.get('code')} {item.get('name', '未知')} "
                f"数量:{item.get('shares', '?')} 成本:{item.get('cost', '?')}"
            )
        if client_id:
            lines.append(f"已保存到客户「{client_id}」的持仓仓库。")
        return '\n'.join(lines)
    else:
        return f"导入失败: {'; '.join(result['errors'])}"


@server.tool()
async def import_holdings_pdf(file_path: str, client_id: str = "") -> str:
    """从PDF文档导入股票/基金持仓。注意：扫描件请使用截图导入。

    Args:
        file_path: PDF文件完整路径
        client_id: 客户姓名或ID（可选）
    """
    result = engine.import_from_pdf(
        file_path, client_id=client_id if client_id else None
    )
    if result['success']:
        items = result['items']
        lines = [f"从PDF识别到 {len(items)} 条持仓:"]
        for item in items:
            itype = '股票' if item.get('item_type') == 'stock' else '基金'
            lines.append(
                f"  [{itype}] {item.get('code')} {item.get('name', '未知')} "
                f"数量:{item.get('shares', '?')} 成本:{item.get('cost', '?')}"
            )
        if client_id:
            lines.append(f"已保存到客户「{client_id}」的持仓仓库。")
        return '\n'.join(lines)
    else:
        return f"导入失败: {'; '.join(result['errors'])}"


@server.tool()
async def import_holdings_url(url: str, client_id: str = "",
                              username: str = "", password: str = "") -> str:
    """从浏览器链接抓取股票/基金持仓。支持东方财富、天天基金等平台。

    Args:
        url: 持仓页面URL
        client_id: 客户姓名或ID（可选）
        username: 登录用户名（可选）
        password: 登录密码（可选）
    """
    credentials = None
    if username:
        credentials = {"username": username, "password": password}

    result = engine.import_from_url(
        url,
        client_id=client_id if client_id else None,
        credentials=credentials
    )
    if result['success']:
        items = result['items']
        lines = [f"从链接抓取到 {len(items)} 条持仓:"]
        for item in items:
            itype = '股票' if item.get('item_type') == 'stock' else '基金'
            lines.append(
                f"  [{itype}] {item.get('code')} {item.get('name', '未知')} "
                f"价格:{item.get('price', item.get('nav', '?'))}"
            )
        if client_id:
            lines.append(f"已保存到客户「{client_id}」的持仓仓库。")
        return '\n'.join(lines)
    else:
        return f"抓取失败: {'; '.join(result['errors'])}"


# ==================== 持仓导出 ====================

@server.tool()
async def export_holdings_excel(client_id: str = "",
                                output_path: str = "") -> str:
    """导出客户持仓为Excel表格，包含持仓明细和汇总sheet。

    Args:
        client_id: 客户姓名或ID
        output_path: 输出路径（可选）
    """
    if client_id:
        items = engine.load_client_items(client_id)
        if not items:
            return f"客户「{client_id}」暂无持仓记录。"
    else:
        return "请提供 client_id 参数。"

    try:
        path = engine.export_to_excel(
            items,
            output_path=output_path if output_path else None,
            client_id=client_id
        )
        return f"Excel已生成！\n  客户: {client_id}\n  持仓: {len(items)}条\n  路径: {path}"
    except ImportError:
        return "需要安装 openpyxl: pip install openpyxl"
    except Exception as e:
        return f"导出失败: {str(e)}"


@server.tool()
async def export_holdings_csv(client_id: str = "",
                              output_path: str = "") -> str:
    """导出客户持仓为CSV文件。

    Args:
        client_id: 客户姓名或ID
        output_path: 输出路径（可选）
    """
    if client_id:
        items = engine.load_client_items(client_id)
        if not items:
            return f"客户「{client_id}」暂无持仓记录。"
    else:
        return "请提供 client_id 参数。"

    try:
        path = engine.export_to_csv(
            items,
            output_path=output_path if output_path else None,
            client_id=client_id
        )
        return f"CSV已生成！\n  客户: {client_id}\n  持仓: {len(items)}条\n  路径: {path}"
    except Exception as e:
        return f"导出失败: {str(e)}"


# ==================== 客户管理 ====================

@server.tool()
async def list_clients() -> str:
    """列出所有已导入持仓的客户及概览。"""
    clients = engine.list_clients()
    if not clients:
        return "暂无客户持仓记录。使用导入工具添加客户持仓。"

    lines = ["【客户持仓仓库】"]
    for client_id, info in clients.items():
        count = info.get('items_count', 0)
        value = info.get('total_value', 0)
        updated = info.get('last_updated', '')
        lines.append(f"  {client_id}    {count}条    ¥{value:,.2f}    {updated}")
    return '\n'.join(lines)


@server.tool()
async def get_client_holdings(client_id: str) -> str:
    """查看指定客户持仓详情，包括每只股票/基金的市值和盈亏。

    Args:
        client_id: 客户姓名或ID
    """
    items = engine.load_client_items(client_id)
    if not items:
        return f"客户「{client_id}」暂无持仓记录。"

    lines = [f"【{client_id} 持仓明细】共 {len(items)} 条"]
    total_cost = 0
    total_value = 0
    for item in items:
        itype = '股' if item.get('item_type') == 'stock' else '基'
        shares = item.get('shares', 0) or 0
        cost = item.get('cost', 0) or 0
        price = item.get('price') or item.get('nav') or cost
        market_value = shares * price
        cost_value = shares * cost
        profit = market_value - cost_value
        profit_pct = (profit / cost_value * 100) if cost_value > 0 else 0
        total_cost += cost_value
        total_value += market_value

        name = (item.get('name') or '')[:16]
        lines.append(
            f"  [{itype}] {item.get('code')} {name:<16s} "
            f"数量:{shares:>8,.0f} 成本:{cost:>8.2f} 现价:{price:>8.2f} "
            f"市值:{market_value:>12,.2f} 盈亏:{profit:>+10,.2f}({profit_pct:>+.1f}%)"
        )

    total_profit = total_value - total_cost
    total_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0
    lines.append(f"───")
    lines.append(f"  合计: 成本 ¥{total_cost:,.2f}  市值 ¥{total_value:,.2f}  "
                 f"盈亏 ¥{total_profit:+,.2f} ({total_pct:+.1f}%)")
    return '\n'.join(lines)


@server.tool()
async def get_import_history(client_id: str) -> str:
    """查看客户历史导入记录。

    Args:
        client_id: 客户姓名或ID
    """
    history = engine.get_import_history(client_id)
    if not history:
        return f"客户「{client_id}」暂无导入记录。"

    lines = [f"【{client_id} 导入历史】共 {len(history)} 次"]
    for record in history[:20]:
        lines.append(
            f"  {record.get('timestamp', '')}  来源:{record.get('source', '')}  "
            f"数量:{record.get('count', 0)}条"
        )
    return '\n'.join(lines)


@server.tool()
async def auto_import_file(file_path: str, client_id: str = "") -> str:
    """智能导入：根据文件扩展名自动选择导入方式。
    支持: .png/.jpg (截图OCR), .pptx (PPT), .docx (Word), .pdf (PDF)

    Args:
        file_path: 文件完整路径
        client_id: 客户姓名或ID（可选）
    """
    ext = Path(file_path).suffix.lower()
    cid = client_id if client_id else None

    if ext in ('.png', '.jpg', '.jpeg', '.bmp', '.gif'):
        result = engine.import_from_screenshot(file_path, client_id=cid)
        method = "截图OCR"
    elif ext == '.pptx':
        result = engine.import_from_ppt(file_path, client_id=cid)
        method = "PPT导入"
    elif ext == '.docx':
        result = engine.import_from_docx(file_path, client_id=cid)
        method = "Word导入"
    elif ext == '.pdf':
        result = engine.import_from_pdf(file_path, client_id=cid)
        method = "PDF导入"
    else:
        return f"不支持的文件类型: {ext}。支持: .png/.jpg/.pptx/.docx/.pdf"

    if result.get('success'):
        items = result.get('items', [])
        lines = [f"{method}成功，识别到 {len(items)} 条持仓:"]
        for item in items:
            itype = '股票' if item.get('item_type') == 'stock' else '基金'
            lines.append(f"  [{itype}] {item.get('code')} {item.get('name', '未知')}")
        if client_id:
            lines.append(f"已保存到客户「{client_id}」的持仓仓库。")
        return '\n'.join(lines)
    else:
        errors = result.get('errors', ['未知错误'])
        return f"{method}失败: {'; '.join(errors)}"


# ==================== 股票研究 ====================

@server.tool()
async def analyze_stock(code: str, period: str = "short") -> str:
    """对指定股票进行全面分析（技术面+估值+三维预测）。
    支持短期(1-5日)、中期(20-60日)、长期(120+日)三个周期。

    Args:
        code: 6位股票代码，如 600519（贵州茅台）、000858（五粮液）
        period: 分析周期，可选 short/medium/long，默认 short
    """
    try:
        from stock_researcher.core.analyzer import StockResearcher

        researcher = StockResearcher()
        result = researcher.analyze_stock(code, period=period)

        if not result:
            return f"未能获取股票 {code} 的数据，请检查代码是否正确或网络是否可用。"

        tech = result.technical
        pred = result.prediction

        lines = [
            f"【{result.name} {code}】{period}期分析",
            f"",
            f"行情: 现价 {result.price}  涨跌 {result.change_pct}%",
        ]

        if tech:
            lines += [
                f"",
                f"技术指标:",
                f"  RSI(6): {tech.rsi6}  RSI(14): {tech.rsi14}",
                f"  MACD: DIF={tech.macd_dif} DEA={tech.macd_dea}",
                f"  均线: MA5={tech.ma5} MA20={tech.ma20} MA60={tech.ma60}",
                f"  技术评分: {tech.tech_score}",
            ]

        if pred:
            lines += [
                f"",
                f"三维预测评分: {pred.composite_score}/100",
                f"  情绪面: {pred.sentiment_score}  估值面: {pred.valuation_score}",
                f"  历史案例: {pred.historical_score}  技术面: {pred.technical_score}",
                f"操作建议: {pred.final_signal}",
            ]

        return '\n'.join(lines)
    except ImportError as e:
        return f"缺少依赖: {e}"
    except Exception as e:
        return f"分析失败: {str(e)}"


@server.tool()
async def get_stock_technical_indicators(code: str) -> str:
    """获取股票的技术指标详情：MA均线系统、RSI、MACD、布林带、ADX等。

    Args:
        code: 6位股票代码
    """
    try:
        from stock_researcher.core.technical import TechnicalAnalyzer
        ta = TechnicalAnalyzer()
        result = ta.analyze(code)

        if not result:
            return f"无法获取 {code} 的技术数据。"

        lines = [
            f"【{code} 技术指标】",
            f"",
            f"均线系统:",
            f"  MA5: {result.get('ma5', '?')}  MA10: {result.get('ma10', '?')}  MA20: {result.get('ma20', '?')}",
            f"  MA60: {result.get('ma60', '?')}  MA120: {result.get('ma120', '?')}",
            f"  排列: {result.get('ma_pattern', '?')}",
            f"",
            f"摆动指标:",
            f"  RSI(6): {result.get('rsi6', '?')}  RSI(14): {result.get('rsi14', '?')}  RSI(24): {result.get('rsi24', '?')}",
            f"  KDJ: K={result.get('kdj_k', '?')} D={result.get('kdj_d', '?')} J={result.get('kdj_j', '?')}",
            f"",
            f"趋势与波动:",
            f"  MACD: DIF={result.get('dif', '?')} DEA={result.get('dea', '?')} Hist={result.get('macd_hist', '?')}",
            f"  ADX: {result.get('adx', '?')}  {'趋势明显' if result.get('adx', 0) > 25 else '震荡整理'}",
            f"  布林带: 上轨={result.get('boll_upper', '?')} 中轨={result.get('boll_mid', '?')} 下轨={result.get('boll_lower', '?')}",
            f"  Hurst: {result.get('hurst', '?')}",
        ]
        return '\n'.join(lines)
    except ImportError as e:
        return f"缺少依赖: {e}"
    except Exception as e:
        return f"技术分析失败: {str(e)}"


@server.tool()
async def get_stock_sentiment(code: str) -> str:
    """分析股票的市场情绪，基于东方财富股吧和雪球的讨论内容。

    Args:
        code: 6位股票代码
    """
    try:
        from stock_researcher.data.sentiment_forum_crawler import SentimentForumCrawler
        crawler = SentimentForumCrawler()
        result = crawler.analyze(code)

        if not result:
            return f"无法获取 {code} 的情绪数据。可能该股票讨论较少。"

        sentiment_score = result.get('sentiment_score', 0)
        sentiment_label = result.get('sentiment_label', '未知')
        bullish_ratio = result.get('bullish_ratio', 0)

        lines = [
            f"【{code} 市场情绪分析】",
            f"",
            f"情绪评分: {sentiment_score} ({sentiment_label})",
            f"多头比例: {bullish_ratio:.1%}",
            f"热门话题: {', '.join(result.get('hot_topics', ['无']))}",
            f"",
            f"情绪告警:",
        ]
        if bullish_ratio > 0.85:
            lines.append("  极度乐观 — 注意分批减仓")
        elif bullish_ratio < 0.15:
            lines.append("  极度悲观 — 关注超跌机会")
        elif sentiment_score > 50:
            lines.append("  偏乐观 — 持股观望")
        elif sentiment_score < -50:
            lines.append("  偏悲观 — 谨慎操作")
        else:
            lines.append("  中性 — 无异常信号")

        return '\n'.join(lines)
    except ImportError as e:
        return f"缺少依赖: {e}"
    except Exception as e:
        return f"情绪分析失败: {str(e)}"


@server.tool()
async def analyze_index(index_code: str = "") -> str:
    """分析大盘指数（上证、沪深300、创业板、科创50）。

    Args:
        index_code: 指数代码，可选: sh000001(上证) sh000300(沪深300) sz399006(创业板) sh000688(科创50)
                    不填则分析全部主要指数
    """
    try:
        from stock_researcher.index_analysis.indices import IndexAnalyzer
        analyzer = IndexAnalyzer()

        if index_code:
            result = analyzer.analyze_single(index_code)
            if result:
                return (
                    f"【{result.get('name')} {index_code}】\n"
                    f"点位: {result.get('price')}  涨跌: {result.get('change_pct')}%\n"
                    f"MA5: {result.get('ma5')}  MA20: {result.get('ma20')}  MA60: {result.get('ma60')}\n"
                    f"RSI: {result.get('rsi')}  MACD: {result.get('macd_signal')}\n"
                    f"趋势: {result.get('trend')}  情绪: {result.get('sentiment')}"
                )
            return f"无法获取指数 {index_code} 的数据。"

        # 分析全部主要指数
        results = analyzer.analyze_all()
        lines = ["【主要指数概览】", ""]
        for r in results:
            lines.append(
                f"  {r.get('name', ''):<10s} {r.get('price', '?'):>8s}  "
                f"{r.get('change_pct', '?'):>6s}%  {r.get('trend', '')}"
            )
        return '\n'.join(lines)
    except ImportError as e:
        return f"缺少依赖: {e}"
    except Exception as e:
        return f"指数分析失败: {str(e)}"


@server.tool()
async def track_stock(code: str, action: str = "add") -> str:
    """添加/移除/查看股票跟踪。跟踪后可以监控价格变动和止损止盈。

    Args:
        code: 6位股票代码
        action: 操作类型 — add(添加) / remove(移除) / check(检查) / list(列表)
    """
    try:
        from stock_researcher.tracker.portfolio import PortfolioTracker
        tracker = PortfolioTracker(data_dir=str(SKILL_DIR / "data"))

        if action == "add":
            tracker.add_stock(code)
            return f"已添加 {code} 到跟踪列表。"
        elif action == "remove":
            tracker.remove_stock(code)
            return f"已从跟踪列表移除 {code}。"
        elif action == "check":
            result = tracker.check_stock(code)
            if result:
                return (
                    f"【{code} 跟踪状态】\n"
                    f"现价: {result.get('price')}  涨跌: {result.get('change_pct')}%\n"
                    f"止损: {result.get('stop_loss')}  止盈: {result.get('take_profit')}\n"
                    f"信号: {result.get('signal', '正常')}\n"
                    f"建议: {result.get('advice', '继续持有')}"
                )
            return f"未找到 {code} 的跟踪数据。"
        elif action == "list":
            stocks = tracker.list_all()
            if not stocks:
                return "暂无跟踪股票。"
            lines = ["【跟踪列表】"]
            for s in stocks:
                lines.append(f"  {s.get('code')} {s.get('name', '')}  "
                            f"成本:{s.get('cost', '?')} 现价:{s.get('price', '?')}")
            return '\n'.join(lines)
        else:
            return f"未知操作: {action}。支持: add/remove/check/list"
    except ImportError as e:
        return f"缺少依赖: {e}"
    except Exception as e:
        return f"操作失败: {str(e)}"


@server.tool()
async def get_sector_analysis(sector_name: str = "") -> str:
    """分析行业板块的强弱和轮动信号。

    Args:
        sector_name: 板块名称，如 银行、医药生物、电子、新能源 等。不填则显示所有板块排行。
    """
    try:
        from stock_researcher.sector_analysis.sectors import SectorAnalyzer
        analyzer = SectorAnalyzer()

        if sector_name:
            result = analyzer.analyze_sector(sector_name)
            if result:
                return (
                    f"【{sector_name} 板块分析】\n"
                    f"平均涨跌: {result.avg_change_pct:.2f}%\n"
                    f"上涨/下跌: {result.up_count}/{result.down_count}\n"
                    f"资金净流入: {result.total_net_flow:.2f}万\n"
                    f"轮动信号: {result.rotation_signal}"
                )
            return f"未找到板块「{sector_name}」。"

        # 全板块排行
        results = analyzer.get_sector_ranking()
        lines = ["【板块强弱排行】", ""]
        for i, r in enumerate(results[:10], 1):
            lines.append(
                f"  {i:>2}. {r.name:<10s}  "
                f"涨跌:{r.avg_change_pct:>+6.2f}%  "
                f"资金:{r.total_net_flow:>+8.2f}万  "
                f"{r.signal}"
            )
        return '\n'.join(lines)
    except ImportError as e:
        return f"缺少依赖: {e}"
    except Exception as e:
        return f"板块分析失败: {str(e)}"


# ==================== 产业链分析 ====================

@server.tool()
async def list_industry_presets() -> str:
    """列出所有预设产业链名称。每条产业链包含上中下游节点结构。"""
    presets = list_presets()
    lines = ["【预设产业链列表】", ""]
    for name in presets:
        chain = get_preset_chain(name)
        up = " → ".join(chain["upstream"][:3])
        mid = " → ".join(chain["midstream"][:3])
        down = " → ".join(chain["downstream"][:3])
        lines.append(f"  {name}")
        lines.append(f"    上游: {up}")
        lines.append(f"    中游: {mid}")
        lines.append(f"    下游: {down}")
        lines.append("")
    return "\n".join(lines)


@server.tool()
async def analyze_industry_chain(
    industry: str,
    mode: str = "general"
) -> str:
    """分析产业链上下游格局。支持通用模式和A股专版模式。

    通用模式（general）六层框架：地图→价值分布→竞争格局→战略控制点→动态演化→投资判断
    A股模式（ashare）六层框架：地图(参与度)→价值(A股利润)→竞争矩阵→国产替代→动态→标的推荐

    Args:
        industry: 产业链名称，如 半导体、新能源汽车、光伏、AI芯片、医药、消费电子、军工、机器人
        mode: 分析模式，general(通用) 或 ashare(A股专版)
    """
    preset = get_preset_chain(industry)
    if not preset:
        return f"未找到「{industry}」的预设产业链。可用: {', '.join(list_presets())}"

    if mode == "ashare":
        analyzer = AShareChainAnalyzer()
        nodes = analyzer.build_chain_map(
            industry,
            [{"name": n, "participation": "🟡"} for n in preset["upstream"]],
            [{"name": n, "participation": "🟡"} for n in preset["midstream"]],
            [{"name": n, "participation": "🟡"} for n in preset["downstream"]]
        )
    else:
        analyzer = IndustryChainAnalyzer()
        nodes = analyzer.build_chain_map(
            industry, preset["upstream"], preset["midstream"], preset["downstream"]
        )

    # 构建基础结果
    from stock_researcher.industry_chain.chain_analyzer import ChainAnalysisResult
    import time
    result = ChainAnalysisResult(
        industry=industry,
        analysis_mode=mode,
        timestamp=time.strftime("%Y-%m-%d %H:%M"),
        nodes=nodes
    )

    return analyzer.format_report(result) + \
        "\n\n骨架已生成。使用 update_chain_node 补充各节点数据后可生成完整分析。"


@server.tool()
async def get_chain_preset_detail(industry: str) -> str:
    """查看指定产业链的详细节点结构。

    Args:
        industry: 产业链名称
    """
    preset = get_preset_chain(industry)
    if not preset:
        return f"未找到「{industry}」。可用: {', '.join(list_presets())}"

    lines = [f"【{industry} 产业链结构】", ""]
    level_names = {"upstream": "上游", "midstream": "中游", "downstream": "下游"}
    for level, nodes in preset.items():
        label = level_names.get(level, level)
        for i, node in enumerate(nodes):
            prefix = "└─" if i == len(nodes) - 1 else "├─"
            lines.append(f"  [{label}] {prefix} {node}")
    return "\n".join(lines)


# ==================== Web UI ====================

_web_server_thread = None

@server.tool()
async def launch_web_ui(port: int = 5003) -> str:
    """启动 AI 股票研究员 Web UI 仪表盘。
    包含：市场概览、股票分析、多智能体研究、板块分析四大模块。
    浏览器会自动打开 http://localhost:{port}

    Args:
        port: Web服务端口号，默认5003
    """
    global _web_server_thread
    import threading, time as _time
    if _web_server_thread and _web_server_thread.is_alive():
        return f"Web UI 已在运行: http://localhost:{port}"

    try:
        from web_server import create_app
        app = create_app()
        def run():
            app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False, threaded=True)
        _web_server_thread = threading.Thread(target=run, daemon=True)
        _web_server_thread.start()
        _time.sleep(1)
        return f"Web UI 已启动！\n访问地址: http://localhost:{port}\n功能模块: 市场概览 | 股票分析 | 多智能体研究 | 板块分析"
    except Exception as e:
        return f"启动失败: {e}"


# ==================== 多智能体分析 ====================

@server.tool()
async def run_multi_agent_analysis(
    ticker: str,
    trade_date: str = "",
    llm_provider: str = "deepseek",
    quick_model: str = "deepseek-chat",
    deep_model: str = "deepseek-chat"
) -> str:
    """使用 TradingAgents 多智能体框架对A股进行深度分析。
    7位AI分析师（市场/情绪/新闻/基本面/政策/资金/解禁）→ 多空辩论 → 风控评估 → 最终决策。

    Args:
        ticker: 6位股票代码或中文股票名称，如 600519 或 贵州茅台
        trade_date: 分析日期 YYYY-MM-DD，默认今天
        llm_provider: LLM提供商，deepseek/openai/anthropic/qwen
        quick_model: 快速思考模型（分析师用）
        deep_model: 深度思考模型（经理/风控用）
    """
    if not trade_date:
        from datetime import date as _date
        trade_date = _date.today().strftime("%Y-%m-%d")

    try:
        from multi_agent.default_config import DEFAULT_CONFIG
        from multi_agent.graph.trading_graph import TradingAgentsGraph

        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = llm_provider
        config["quick_think_llm"] = quick_model
        config["deep_think_llm"] = deep_model
        config["output_language"] = "Chinese"
        config["max_debate_rounds"] = 1
        config["max_risk_discuss_rounds"] = 1

        graph = TradingAgentsGraph(
            selected_analysts=["market", "social", "news", "fundamentals", "policy", "hot_money", "lockup"],
            config=config,
        )

        final_state, signal = graph.propagate(ticker, trade_date)

        lines = [
            f"【TradingAgents 多智能体分析】{ticker} {trade_date}",
            f"{'='*50}",
            f"",
            f"最终信号: {signal}",
            f"",
        ]

        report_keys = [
            ("market_report", "市场分析师"),
            ("sentiment_report", "社交情绪分析师"),
            ("news_report", "新闻分析师"),
            ("fundamentals_report", "基本面分析师"),
            ("policy_report", "政策分析师"),
            ("hot_money_report", "资金流向追踪"),
            ("lockup_report", "限售解禁监控"),
        ]

        for key, label in report_keys:
            content = final_state.get(key, "")
            if content:
                lines.append(f"--- {label} ---")
                lines.append(content[:500] + ("..." if len(content) > 500 else ""))
                lines.append("")

        debate = final_state.get("investment_debate_state", {})
        if debate.get("judge_decision"):
            lines.append("--- 研究员裁决 ---")
            lines.append(debate["judge_decision"][:500])
            lines.append("")

        if final_state.get("final_trade_decision"):
            lines.append("--- 最终决策 ---")
            lines.append(final_state["final_trade_decision"][:800])

        return '\n'.join(lines)
    except ImportError as e:
        return f"缺少依赖: {e}\n请安装: pip install langchain-core langchain-openai langgraph"
    except Exception as e:
        return f"分析失败: {type(e).__name__}: {e}"


# ==================== v2.1.0 新增：量化分析工具 ====================

# MCP 工具数量: 22 → 27 (+5 个量化工具)
# analyze_volatility / analyze_factors / find_pairs / run_ml_prediction / run_quant_analysis

@server.tool()
async def analyze_volatility(
    code: str,
    horizon: int = 5,
    days: int = 120,
) -> str:
    """GARCH波动率预测。分析股票的历史波动率状态，使用GARCH模型预测未来N日波动率，
    判断当前处于高/中/低波动状态，辅助风险管理和仓位控制。

    依赖: pip install arch statsmodels

    Args:
        code: 6位股票代码，如 600519
        horizon: 预测天数（默认5日）
        days: 回看历史天数（默认120日，最少50日）
    """
    try:
        from stock_researcher.quantitative.garch_model import GarchForecaster
    except ImportError:
        return "GARCH模型依赖未安装。请运行: pip install arch statsmodels scipy"

    try:
        # 获取K线数据
        from scripts.stock_researcher.data.market import MarketData
        market = MarketData()
        kline = market.fetch_history(code, days=days)
        if not kline or not kline.get("closes"):
            return f"获取 {code} K线数据失败"

        prices = kline["closes"]
        if len(prices) < 50:
            return f"数据不足：需要至少50个交易日数据，当前仅 {len(prices)} 个"

        forecaster = GarchForecaster(auto_select=True)
        result = forecaster.forecast(prices, horizon=horizon)
        regime = forecaster.analyze_volatility_regime(prices)

        lines = [
            f"【GARCH 波动率预测】{code}",
            f"{'='*50}",
            f"模型: {result.model_type}",
            f"AIC: {result.aic:.2f}  BIC: {result.bic:.2f}",
            f"模型收敛: {'✅' if result.convergence_ok else '⚠️ 未收敛（使用历史波动率回退）'}",
            f"",
            f"--- 波动率状态 ---",
            f"当前年化波动率: {result.current_vol:.2%}",
            f"预测年化波动率: {result.forecast_annual_vol:.2%}",
            f"长期均衡波动率: {result.long_run_vol:.2%}",
            f"波动率半衰期: {result.half_life:.1f} 天",
            f"",
            f"--- 波动率状态诊断 ---",
            f"当前状态: {regime.get('regime', '未知')}",
            f"历史分位: {regime.get('percentile', 'N/A')}%",
            f"操作建议: {regime.get('suggestion', '')}",
            f"",
            f"--- 未来 {horizon} 日波动率预测 ---",
        ]
        for i, vol in enumerate(result.forecast_vol):
            vol_annual = vol * (252 ** 0.5)
            lines.append(f"  T+{i+1}: 日波动={vol:.4%}  年化={vol_annual:.2%}")

        return '\n'.join(lines)
    except Exception as e:
        return f"波动率分析失败: {type(e).__name__}: {e}"


@server.tool()
async def analyze_factors(
    codes: str,
) -> str:
    """A股多因子评分分析。从价值/动量/质量/规模/成长/低波动/换手率/分析师预期
    共8个维度对股票池进行综合评分，输出排名和因子暴露。

    依赖: pip install scipy

    Args:
        codes: 股票代码列表，逗号分隔，如 "600519,000858,600036,601398,300750"
    """
    try:
        from stock_researcher.quantitative.factor_analysis import FactorAnalyzer
    except ImportError:
        return "因子分析依赖未安装。请运行: pip install scipy"

    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    if len(code_list) < 3:
        return "请提供至少3只股票代码（逗号分隔）"

    try:
        # 获取基础数据
        from scripts.stock_researcher.data.market import MarketData
        from scripts.stock_researcher.data.fundamental import FundamentalData
        market = MarketData()
        fund = FundamentalData()

        rt_data = market.fetch_realtime(code_list)
        stocks = []

        for code in code_list:
            rt = rt_data.get(code, {})
            fin = fund.get_financial_summary(code) if hasattr(fund, 'get_financial_summary') else {}

            stocks.append({
                "symbol": code,
                "name": rt.get("name", code),
                "pe": rt.get("pe", fin.get("pe", 0)),
                "pb": rt.get("pb", fin.get("pb", 0)),
                "roe": fin.get("roe", 0),
                "gross_margin": fin.get("gross_margin", 0),
                "debt_ratio": fin.get("debt_ratio", 50),
                "mcap": rt.get("mkt_cap", 0) / 1e8 if rt.get("mkt_cap") else 0,
                "ret_20d": rt.get("change_20d", 0),
                "ret_60d": rt.get("change_60d", 0),
                "eps_growth": fin.get("eps_growth", 0),
                "revenue_growth": fin.get("revenue_growth", 0),
                "volatility": rt.get("volatility", 30),
                "turnover": rt.get("turnover", 0),
            })

        analyzer = FactorAnalyzer()
        reports = analyzer.score_stocks(stocks)

        lines = [
            f"【A股多因子评分】{len(reports)} 只股票",
            f"{'='*60}",
            f"",
            f"排名 | 代码 | 名称 | 综合得分 | 百分位 | 建议",
            f"-----|------|------|---------|--------|------",
        ]

        for i, r in enumerate(reports):
            lines.append(
                f" {i+1:2d}  | {r.symbol} | {r.name[:6]:6s} | "
                f"{r.composite_score:6.1f} | {r.percentile_rank:5.1f}% | "
                f"{r.recommendation}"
            )

        lines.append("")
        lines.append("--- Top 3 因子贡献明细 ---")
        for r in reports[:5]:
            top_factors = sorted(
                r.factors.items(),
                key=lambda x: x[1].score * x[1].weight,
                reverse=True
            )[:3]
            factor_str = " | ".join(
                f"{name}: {f.score:.0f}分×{f.weight:.0%}={f.score*f.weight:.1f}"
                for name, f in top_factors
            )
            lines.append(f"  {r.symbol} {r.name}: {factor_str}")

        # 因子暴露统计
        exposure = analyzer.get_factor_exposure_report(reports)
        lines.append("")
        lines.append("--- 因子暴露统计（全池） ---")
        lines.append("因子 | 均值 | 中位数 | 标准差 | 权重")
        lines.append("-----|------|--------|--------|------")
        for fn, stats in exposure.items():
            lines.append(
                f"  {fn} | {stats['mean']:5.1f} | {stats['median']:5.1f} | "
                f"{stats['std']:5.1f} | {stats['weight']:.0%}"
            )

        return '\n'.join(lines)
    except Exception as e:
        import traceback
        return f"因子分析失败: {type(e).__name__}: {e}\n{traceback.format_exc()}"


@server.tool()
async def find_pairs(
    codes: str,
    sector: str = "",
    min_correlation: float = 0.7,
) -> str:
    """配对交易分析。基于协整检验寻找具有长期均衡关系的股票对，
    计算对冲比率和价差Z-Score，生成统计套利信号。

    依赖: pip install scipy statsmodels

    Args:
        codes: 股票代码列表，逗号分隔（建议同行业，如银行股）
        sector: 行业限定（可选，如"银行"）
        min_correlation: 最小相关系数阈值（默认0.7）
    """
    try:
        from stock_researcher.quantitative.pairs_trading import PairsTrader
    except ImportError:
        return "配对交易依赖未安装。请运行: pip install scipy statsmodels"

    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    if len(code_list) < 2:
        return "请提供至少2只股票代码"

    try:
        from scripts.stock_researcher.data.market import MarketData
        market = MarketData()

        stock_pool = []
        for code in code_list:
            kline = market.fetch_history(code, days=200)
            if kline and kline.get("closes") and len(kline["closes"]) >= 60:
                stock_pool.append({
                    "symbol": code,
                    "name": kline.get("name", code),
                    "prices": kline["closes"],
                    "sector": sector if sector else "",
                })

        if len(stock_pool) < 2:
            return "有效数据不足（需要至少2只有效K线数据，每只≥60日）"

        trader = PairsTrader(min_correlation=min_correlation)
        pairs = trader.find_pairs(stock_pool, sector=sector if sector else None)

        if not pairs:
            return f"未找到符合条件的协整配对（相关性≥{min_correlation}，协整 p<0.05）"

        lines = [
            f"【配对交易分析】发现 {len(pairs)} 对协整关系",
            f"{'='*60}",
        ]

        for i, p in enumerate(pairs):
            lines.append(f"")
            lines.append(f"--- 配对 {i+1}: {p.name_a}({p.stock_a}) ↔ {p.name_b}({p.stock_b}) ---")
            lines.append(f"  相关系数: {p.correlation:.4f}")
            lines.append(f"  协整p值: {p.coint_pvalue:.4f} {'✅' if p.coint_pvalue < 0.05 else '⚠️'}")
            lines.append(f"  对冲比率: 1 : {p.hedge_ratio:.4f}")
            lines.append(f"  价差均值: {p.spread_mean:.2f}  标准差: {p.spread_std:.2f}")
            lines.append(f"  当前价差: {p.current_spread:.2f}  Z-Score: {p.z_score:.2f}")
            lines.append(f"  半衰期: {p.half_life:.1f} 天")
            lines.append(f"  交易信号: {p.signal}")

            # 简单操作建议
            z = p.z_score
            if z > 2.0:
                lines.append(f"  💡 操作: 做空价差 — 卖出 {p.name_a}，买入 {p.name_b}")
            elif z < -2.0:
                lines.append(f"  💡 操作: 做多价差 — 买入 {p.name_a}，卖出 {p.name_b}")
            elif abs(z) < 0.5:
                lines.append(f"  💡 操作: 价差已回归均值，建议平仓观望")
            else:
                lines.append(f"  💡 操作: 持有/观望")

        return '\n'.join(lines)
    except Exception as e:
        import traceback
        return f"配对分析失败: {type(e).__name__}: {e}\n{traceback.format_exc()}"


@server.tool()
async def run_ml_prediction(
    code: str,
    horizon: int = 5,
) -> str:
    """机器学习涨跌方向预测。使用RandomForest模型，基于技术面/资金面/情绪面
    共27个特征，预测未来N日涨跌方向（上涨/震荡/下跌）。

    依赖: pip install scikit-learn scipy

    Args:
        code: 6位股票代码
        horizon: 预测天数（默认5日）
    """
    try:
        from stock_researcher.quantitative.ml_predictor import (
            MLPredictor, FeatureEngineer
        )
    except ImportError:
        return "ML预测依赖未安装。请运行: pip install scikit-learn scipy"

    try:
        from scripts.stock_researcher.data.market import MarketData
        market = MarketData()
        kline = market.fetch_history(code, days=200)

        if not kline or not kline.get("closes") or len(kline["closes"]) < 60:
            return f"数据不足：需要至少60个交易日，当前数据量不足"

        # 重建 OHLCV 字典列表
        closes = kline.get("closes", [])
        highs = kline.get("highs", [closes[-1]] * len(closes))
        lows = kline.get("lows", [closes[-1]] * len(closes))
        opens = kline.get("opens", [closes[-1]] * len(closes))
        volumes = kline.get("volumes", [0] * len(closes))

        ohlcv = []
        for i in range(len(closes)):
            ohlcv.append({
                "open": opens[i] if i < len(opens) else closes[i],
                "high": highs[i] if i < len(highs) else closes[i],
                "low": lows[i] if i < len(lows) else closes[i],
                "close": closes[i],
                "volume": volumes[i] if i < len(volumes) else 0,
            })

        # 提取特征
        features = FeatureEngineer.extract_features(ohlcv)
        if not features:
            return "特征提取失败，数据不足"

        lines = [
            f"【ML涨跌方向预测】{code}  (预测未来 {horizon} 日)",
            f"{'='*50}",
            f"",
            f"⚠️ 注意: ML模型需要大量历史数据训练才能给出可靠预测。",
            f"当前仅展示特征提取结果和信号摘要。",
            f"",
            f"--- 关键特征 ---",
            f"  RSI(14): {features.get('rsi_14', 'N/A'):.1f}" if isinstance(features.get('rsi_14'), (int, float)) else f"  RSI(14): {features.get('rsi_14', 'N/A')}",
            f"  MACD柱: {features.get('macd_hist', 'N/A')}" if not isinstance(features.get('macd_hist'), float) else f"  MACD柱: {features.get('macd_hist', 0):.4f}",
            f"  MA20偏离: {features.get('ma20_dev', 'N/A')}" if not isinstance(features.get('ma20_dev'), float) else f"  MA20偏离: {features.get('ma20_dev', 0):.2f}%",
            f"  5日涨跌: {features.get('ret_5d', 'N/A')}" if not isinstance(features.get('ret_5d'), float) else f"  5日涨跌: {features.get('ret_5d', 0):.2f}%",
            f"  20日涨跌: {features.get('ret_20d', 'N/A')}" if not isinstance(features.get('ret_20d'), float) else f"  20日涨跌: {features.get('ret_20d', 0):.2f}%",
            f"  20日波动率: {features.get('vol_20d', 'N/A')}" if not isinstance(features.get('vol_20d'), float) else f"  20日波动率: {features.get('vol_20d', 0):.1f}%",
            f"  布林带位置: {features.get('bb_position', 'N/A')}" if not isinstance(features.get('bb_position'), float) else f"  布林带位置: {features.get('bb_position', 0):.2f} (0=下轨, 1=上轨)",
            f"  量比(5日): {features.get('vol_ratio_5', 'N/A')}" if not isinstance(features.get('vol_ratio_5'), float) else f"  量比(5日): {features.get('vol_ratio_5', 0):.2f}x",
            f"",
            f"--- 技术信号解读 ---",
        ]

        # RSI 解读
        rsi = features.get('rsi_14', 50)
        if isinstance(rsi, (int, float)):
            if rsi > 70:
                lines.append(f"  RSI={rsi:.1f}: 超买区域，短期回调风险较高")
            elif rsi < 30:
                lines.append(f"  RSI={rsi:.1f}: 超卖区域，短期反弹概率较高")
            else:
                lines.append(f"  RSI={rsi:.1f}: 中性区域")

        # 均线偏离
        ma20_dev = features.get('ma20_dev', 0)
        if isinstance(ma20_dev, (int, float)):
            if ma20_dev > 10:
                lines.append(f"  价格高于MA20 {ma20_dev:.1f}%: 短期偏高")
            elif ma20_dev < -10:
                lines.append(f"  价格低于MA20 {ma20_dev:.1f}%: 短期偏低")

        # 量价配合
        vol_corr = features.get('vol_price_corr', 0)
        if isinstance(vol_corr, (int, float)):
            if vol_corr > 0.5:
                lines.append(f"  量价正相关({vol_corr:.2f}): 技术面健康")
            elif vol_corr < -0.3:
                lines.append(f"  量价背离({vol_corr:.2f}): 注意风险")

        lines.append(f"")
        lines.append(f"💡 如需完整ML训练+预测，请使用批量数据调用 run_quant_analysis 工具。")

        return '\n'.join(lines)
    except Exception as e:
        import traceback
        return f"ML预测失败: {type(e).__name__}: {e}\n{traceback.format_exc()}"


@server.tool()
async def run_quant_analysis(
    code: str,
    analysis_type: str = "all",
) -> str:
    """综合量化分析入口。对单只股票运行完整的量化分析流水线：
    Alpha信号 + 技术指标 + 风险管理 + 波动率预测 + 因子评分。

    国内网络环境优化 — 所有数据源均为国内可直接访问的API
    （腾讯财经/东方财富/同花顺/mootdx/新浪财经）。

    Args:
        code: 6位股票代码，如 600519
        analysis_type: 分析类型 — all(全部) / alpha(信号) / risk(风控) / vol(波动率) / factor(因子)
    """
    try:
        from scripts.stock_researcher.data.market import MarketData
        from scripts.stock_researcher.quantitative.engine import AShareQuantEngine
        market = MarketData()
    except ImportError as e:
        return f"核心依赖缺失: {e}"

    try:
        # 获取数据
        kline = market.fetch_history(code, days=120)
        if not kline or not kline.get("closes") or len(kline["closes"]) < 30:
            return f"数据不足：{code} 需要至少30个交易日数据"

        closes = kline.get("closes", [])
        highs = kline.get("highs", [])
        lows = kline.get("lows", [])
        volumes = kline.get("volumes", [])
        current_price = closes[-1]
        prev_close = closes[-2] if len(closes) >= 2 else current_price
        change_pct = (current_price - prev_close) / prev_close * 100 if prev_close else 0

        # 重建OHLCV
        ohlcv_list = []
        for i in range(min(len(closes), len(highs), len(lows))):
            ohlcv_list.append({
                "open": closes[i],
                "high": highs[i],
                "low": lows[i],
                "close": closes[i],
                "volume": volumes[i] if i < len(volumes) else 0,
            })

        engine = AShareQuantEngine()
        result = engine.analyze_stock(code, ohlcv_list)

        lines = [
            f"【综合量化分析】{code}",
            f"{'='*60}",
            f"",
            f"--- 行情概览 ---",
            f"  现价: {current_price:.2f}",
            f"  涨跌: {change_pct:+.2f}%",
            f"",
            f"--- Alpha 信号（量化引擎） ---",
        ]

        signals = result.get("signals", [])
        if signals:
            for s in signals:
                arrow = "🔺" if s["direction"] == "UP" else "🔻"
                lines.append(
                    f"  {arrow} {s['model']}: {s['direction']} "
                    f"置信度={s['confidence']:.2f} 幅度={s['magnitude']:.1f}%"
                )
            lines.append(f"")
            lines.append(f"  综合建议: **{result.get('recommendation', 'N/A')}**")
        else:
            lines.append(f"  当前无显著信号")

        lines.append(f"")
        lines.append(f"--- 技术指标 ---")
        indicators = result.get("indicators", {})
        if indicators:
            macd = indicators.get("macd", {})
            rsi = indicators.get("rsi", {})
            adx = indicators.get("adx", {})
            kdj = indicators.get("kdj", {})
            bb = indicators.get("bollinger", {})
            hurst = indicators.get("hurst", {})

            lines.append(f"  MACD: DIF={macd.get('dif', 0):.4f} 信号={macd.get('signal', 'N/A')}" if isinstance(macd.get('dif'), (int, float)) else f"  MACD: {macd.get('signal', 'N/A')}")
            lines.append(f"  RSI(14): {rsi.get('value', 'N/A')} {rsi.get('signal', '')}" if not isinstance(rsi.get('value'), dict) else f"  RSI(14): {rsi.get('signal', 'N/A')}")
            lines.append(f"  ADX: {adx.get('adx', 'N/A')} 趋势={adx.get('trend', 'N/A')}" if not isinstance(adx.get('trend'), dict) else f"  ADX: 趋势={adx.get('trend', 'N/A')}")
            lines.append(f"  KDJ: K={kdj.get('k', 'N/A')} D={kdj.get('d', 'N/A')} J={kdj.get('j', 'N/A')}" if isinstance(kdj.get('k'), (int, float)) else f"  KDJ: {kdj.get('signal', 'N/A')}")
            lines.append(f"  布林: 上轨={bb.get('upper', 'N/A')} 中轨={bb.get('middle', 'N/A')} 下轨={bb.get('lower', 'N/A')}" if isinstance(bb.get('upper'), (int, float)) else f"  布林: 位置={bb.get('position', 'N/A')}")
            if hurst and isinstance(hurst, dict):
                h_val = hurst.get('value', 'N/A')
                h_interp = hurst.get('interpretation', f"H={h_val}")
                lines.append(f"  Hurst: {h_interp}")

        # GARCH波动率（可选）
        if analysis_type in ("all", "vol"):
            try:
                from stock_researcher.quantitative.garch_model import GarchForecaster
                forecaster = GarchForecaster(auto_select=True)
                garch_result = forecaster.forecast(closes, horizon=5)
                lines.append(f"")
                lines.append(f"--- GARCH 波动率预测 ---")
                lines.append(f"  模型: {garch_result.model_type} (收敛: {'✅' if garch_result.convergence_ok else '⚠️'})")
                lines.append(f"  年化波动率: 当前={garch_result.current_vol:.2%} → 预测={garch_result.forecast_annual_vol:.2%}")
                lines.append(f"  波动率半衰期: {garch_result.half_life:.1f} 天")
            except ImportError:
                pass

        # 因子评分（可选）
        if analysis_type in ("all", "factor"):
            try:
                from stock_researcher.quantitative.factor_analysis import FactorAnalyzer
                from stock_researcher.data.fundamental import FundamentalData
                fund = FundamentalData()
                fin = fund.get_financial_summary(code) if hasattr(fund, 'get_financial_summary') else {}

                rt_data = market.fetch_realtime([code])
                rt = rt_data.get(code, {})

                stock_data = [{
                    "symbol": code,
                    "name": rt.get("name", code),
                    "pe": rt.get("pe", fin.get("pe", 0)),
                    "pb": rt.get("pb", fin.get("pb", 0)),
                    "roe": fin.get("roe", 0),
                    "gross_margin": fin.get("gross_margin", 0),
                    "debt_ratio": fin.get("debt_ratio", 50),
                    "mcap": rt.get("mkt_cap", 0) / 1e8 if rt.get("mkt_cap") else 0,
                    "ret_20d": 0, "ret_60d": 0,
                    "eps_growth": fin.get("eps_growth", 0),
                    "revenue_growth": fin.get("revenue_growth", 0),
                    "volatility": 30, "turnover": rt.get("turnover", 0),
                }]
                analyzer = FactorAnalyzer()
                reports = analyzer.score_stocks(stock_data)
                if reports:
                    r = reports[0]
                    lines.append(f"")
                    lines.append(f"--- 因子评分 ---")
                    lines.append(f"  综合得分: {r.composite_score:.1f}/100")
                    lines.append(f"  投资建议: {r.recommendation}")
                    lines.append(f"  因子明细:")
                    for name, factor in sorted(r.factors.items(), key=lambda x: x[1].score * x[1].weight, reverse=True)[:5]:
                        lines.append(f"    {factor.name}: {factor.score:.1f}分 × {factor.weight:.0%} = {factor.score*factor.weight:.1f}")
            except ImportError:
                pass

        lines.append(f"")
        lines.append(f"--- 数据源 ---")
        lines.append(f"  行情: 腾讯财经 qt.gtimg.cn")
        lines.append(f"  财务: 东方财富/Mootdx")
        lines.append(f"  K线: Mootdx TCP / 新浪财经备源")
        lines.append(f"  所有数据源均为国内网络直接可用 🇨🇳")

        return '\n'.join(lines)
    except Exception as e:
        import traceback
        return f"量化分析失败: {type(e).__name__}: {e}\n{traceback.format_exc()}"


# ==================== 好友分析工具 ====================

@server.tool()
async def add_friend(friend_name: str, note: str = "") -> str:
    """添加好友到持仓分析系统。添加后可以为该好友导入持仓数据并进行分析。
    适用场景：想为朋友分析股票持仓，先注册好友信息。

    Args:
        friend_name: 好友名称或昵称，如 "张三"、"小李"
        note: 备注信息（可选），如 "大学同学"、"同事"
    """
    result = engine.add_friend(friend_name, note=note)
    if result['success']:
        return (f"好友已添加！\n"
                f"  好友ID: {result['friend_id']}\n"
                f"  名称: {friend_name}\n"
                f"  备注: {note or '无'}\n\n"
                f"接下来可以为好友导入持仓数据：\n"
                f"  - 使用 import_friend_holdings_text 粘贴持仓文本\n"
                f"  - 使用 auto_import_file 上传持仓文件")
    return f"添加失败: {result.get('error', '未知错误')}"


@server.tool()
async def import_friend_holdings_text(friend_name: str, holdings_text: str) -> str:
    """从文本导入好友持仓数据。支持多种格式的持仓文本粘贴。
    支持格式示例：
      - 600519 贵州茅台 100股 成本1800
      - 五粮液(000858) 500股
      - 表格粘贴（含股票代码、名称、数量等列）

    Args:
        friend_name: 好友名称（需已通过 add_friend 添加）
        holdings_text: 持仓文本内容，支持多种格式
    """
    friend_id = f"friend_{friend_name}"

    # 检查好友是否存在
    clients = engine.list_clients()
    if friend_id not in clients:
        # 自动创建好友
        engine.add_friend(friend_name)

    result = engine.import_from_text(holdings_text, client_id=friend_id,
                                     client_type='friend')
    if result['success']:
        items = result['items']
        lines = [f"成功导入好友「{friend_name}」的持仓，共 {len(items)} 条:"]
        for item in items:
            itype = '股票' if item.get('item_type') == 'stock' else '基金'
            lines.append(
                f"  [{itype}] {item.get('code')} {item.get('name', '未知')} "
                f"数量:{item.get('shares', '?')} 成本:{item.get('cost', '?')}"
            )
        lines.append(f"\n已保存到好友「{friend_name}」的持仓仓库。")
        lines.append(f"可使用 analyze_friend 进行持仓分析。")
        return '\n'.join(lines)
    return f"导入失败: {'; '.join(result['errors'])}"


@server.tool()
async def list_friends() -> str:
    """列出所有已添加的好友及其持仓概览。
    返回每个好友的持仓数量、总市值和最后更新时间。
    """
    friends = engine.list_friends()
    if not friends:
        return "暂无好友记录。使用 add_friend 添加好友。"
    lines = ["【好友列表】"]
    for friend_id, info in friends.items():
        name = info.get('name', friend_id)
        note = info.get('note', '')
        count = info.get('items_count', 0)
        value = info.get('total_value', 0)
        updated = info.get('last_updated', '')
        note_str = f" ({note})" if note else ""
        lines.append(f"  {name}{note_str}    {count}条持仓    ¥{value:,.2f}    {updated}")
    return '\n'.join(lines)


@server.tool()
async def analyze_friend(friend_name: str) -> str:
    """分析好友的股票/基金持仓情况。包括持仓概览、盈亏统计、持仓明细等。
    适用场景：查看好友持仓分析结果。

    Args:
        friend_name: 好友名称（需已导入持仓数据）
    """
    friend_id = f"friend_{friend_name}"

    items = engine.load_client_items(friend_id)
    if not items:
        return f"好友「{friend_name}」暂无持仓数据，请先使用 import_friend_holdings_text 导入。"

    # 计算统计数据
    total_value = 0
    total_cost = 0
    item_details = []

    for item in items:
        shares = item.get('shares', 0) or 0
        cost = item.get('cost', 0) or 0
        price = item.get('price') or item.get('nav') or cost
        market_value = shares * price
        cost_value = shares * cost
        profit = market_value - cost_value
        profit_pct = (profit / cost_value * 100) if cost_value > 0 else 0
        total_value += market_value
        total_cost += cost_value
        item_details.append({
            'type': item.get('item_type', 'stock'),
            'code': item.get('code', ''),
            'name': item.get('name', '未知'),
            'shares': shares,
            'cost': cost,
            'price': price,
            'value': market_value,
            'profit': profit,
            'profit_pct': profit_pct
        })

    total_profit = total_value - total_cost
    total_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0

    # 生成分析报告
    lines = [
        f"{'='*50}",
        f"  好友「{friend_name}」持仓分析报告",
        f"{'='*50}",
        "",
        f"【持仓概览】",
        f"  持有标的: {len(items)} 只",
        f"  总市值: ¥{total_value:,.2f}",
        f"  总成本: ¥{total_cost:,.2f}",
        f"  总盈亏: ¥{total_profit:+,.2f} ({total_pct:+.1f}%)",
        "",
        f"【持仓明细】",
    ]

    # 按盈亏排序
    item_details.sort(key=lambda x: x['profit'], reverse=True)

    for detail in item_details:
        itype = '股' if detail['type'] == 'stock' else '基'
        status = "📈" if detail['profit'] >= 0 else "📉"
        lines.append(
            f"  {status} [{itype}] {detail['code']} {detail['name']:<15s} "
            f"数量:{detail['shares']:>8,.0f} "
            f"市值:{detail['value']:>12,.2f} "
            f"盈亏:{detail['profit']:>+10,.2f} ({detail['profit_pct']:>+.1f}%)"
        )

    # 风险提示
    lines.extend([
        "",
        f"【风险提示】",
        f"  • 以上分析仅供参考，不构成投资建议",
        f"  • 股票投资有风险，入市需谨慎",
        f"  • 数据基于导入时的价格，实际可能有偏差",
    ])

    return '\n'.join(lines)


@server.tool()
async def generate_friend_report(friend_name: str, report_type: str = "text") -> str:
    """为好友生成持仓分析报告文件。
    支持文本报告和Excel导出。

    Args:
        friend_name: 好友名称
        report_type: 报告类型 ("text"=文本报告, "excel"=Excel表格)
    """
    friend_id = f"friend_{friend_name}"

    items = engine.load_client_items(friend_id)
    if not items:
        return f"好友「{friend_name}」暂无持仓数据，请先导入。"

    try:
        if report_type.lower() == "excel":
            path = engine.export_to_excel(items, client_id=friend_id)
            return (f"Excel报告已生成！\n"
                    f"  好友: {friend_name}\n"
                    f"  持仓数: {len(items)}条\n"
                    f"  文件路径: {path}")
        else:
            # 文本报告
            analysis = await analyze_friend(friend_name)
            report_dir = engine.clients_dir / friend_id / 'reports'
            report_dir.mkdir(parents=True, exist_ok=True)
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = report_dir / f'report_{timestamp}.txt'
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(analysis)
            return (f"文本报告已生成！\n"
                    f"  好友: {friend_name}\n"
                    f"  持仓数: {len(items)}条\n"
                    f"  文件路径: {report_file}")
    except Exception as e:
        return f"报告生成失败: {str(e)}"


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
