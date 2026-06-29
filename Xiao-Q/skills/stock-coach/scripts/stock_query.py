#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票行情查询脚本 - 炒股教练技能
集成akshare功能，提供实时行情、历史K线、板块行情、资金流向等查询
"""

import json
import re
from datetime import datetime, timedelta

def get_stock_info(stock_code):
    """
    获取个股基本信息
    
    Args:
        stock_code: 股票代码，如 '000001' 或 '600519'
    
    Returns:
        dict: 股票基本信息
    """
    try:
        import akshare as ak
        
        # 判断市场
        if stock_code.startswith('6'):
            market = "sh"
            symbol = "sh" + stock_code
        else:
            market = "sz" 
            symbol = "sz" + stock_code
        
        # 获取实时行情
        df = ak.stock_zh_a_spot_em()
        stock_data = df[df['代码'] == stock_code]
        
        if stock_data.empty:
            return {"error": f"未找到股票 {stock_code}"}
        
        result = stock_data.iloc[0].to_dict()
        return result
        
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}


def get_realtime_quote(stock_codes):
    """
    获取实时行情（批量）
    
    Args:
        stock_codes: 股票代码列表，如 ['000001', '600519']
    
    Returns:
        DataFrame: 实时行情数据
    """
    try:
        import akshare as ak
        
        # 获取所有A股实时行情
        df = ak.stock_zh_a_spot_em()
        
        # 筛选指定股票
        if stock_codes:
            df = df[df['代码'].isin(stock_codes)]
        
        return df
        
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}


def get_historical_kline(stock_code, period="daily", start_date=None, end_date=None, adjust="qfq"):
    """
    获取历史K线数据
    
    Args:
        stock_code: 股票代码
        period: 周期 (daily/weekly/monthly)
        start_date: 开始日期，格式 YYYYMMDD
        end_date: 结束日期，格式 YYYYMMDD
        adjust: 复权类型 (qfq/不复权hfq)
    
    Returns:
        DataFrame: K线数据
    """
    try:
        import akshare as ak
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
        
        return df
        
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}


def get_sector_quotation(sector_type="industry"):
    """
    获取板块行情
    
    Args:
        sector_type: 板块类型 (industry/概念concept)
    
    Returns:
        DataFrame: 板块行情数据
    """
    try:
        import akshare as ak
        
        if sector_type == "industry":
            df = ak.stock_board_industry_name_em()
        else:
            df = ak.stock_board_concept_name_em()
        
        # 按涨幅排序
        df = df.sort_values('涨跌幅', ascending=False)
        
        return df
        
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}


def get_sector_stocks(sector_name):
    """
    获取板块内个股
    
    Args:
        sector_name: 板块名称，如 '半导体'、'人工智能'
    
    Returns:
        DataFrame: 板块内个股数据
    """
    try:
        import akshare as ak
        
        df = ak.stock_board_industry_cons_em(symbol=sector_name)
        
        return df
        
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}


def get_fund_flow(stock_code):
    """
    获取个股资金流向
    
    Args:
        stock_code: 股票代码
    
    Returns:
        DataFrame: 资金流向数据
    """
    try:
        import akshare as ak
        
        # 判断市场
        if stock_code.startswith('6'):
            market = "sh"
        else:
            market = "sz"
        
        df = ak.stock_individual_fund_flow(stock=stock_code, market=market)
        
        return df
        
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}


def get_market_money_flow():
    """
    获取大盘资金流向
    
    Returns:
        DataFrame: 市场整体资金流向
    """
    try:
        import akshare as ak
        
        df = ak.stock_market_fund_flow()
        
        return df
        
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}


def get_allowance_rate():
    """
    获取涨跌停统计
    
    Returns:
        DataFrame: 涨跌停数据
    """
    try:
        import akshare as ak
        
        df = ak.stock_zt_pool_em(date=datetime.now().strftime("%Y%m%d"))
        
        return df
        
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}


def get_limit_up_pool(date=None):
    """
    获取涨停板股票池
    
    Args:
        date: 日期，格式 YYYYMMDD
    
    Returns:
        DataFrame: 涨停股票列表
    """
    try:
        import akshare as ak
        
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        
        df = ak.stock_zt_pool_em(date=date)
        
        return df
        
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}


def get_limit_down_pool(date=None):
    """
    获取跌停板股票池
    
    Args:
        date: 日期，格式 YYYYMMDD
    
    Returns:
        DataFrame: 跌停股票列表
    """
    try:
        import akshare as ak
        
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        
        df = ak.stock_zt_pool_strong_em(date=date)
        
        return df
        
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}


def get_dragons_list(date=None):
    """
    获取龙虎榜数据
    
    Args:
        date: 日期，格式 YYYYMMDD
    
    Returns:
        DataFrame: 龙虎榜数据
    """
    try:
        import akshare as ak
        
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        
        df = ak.stock_lhb_detail_em(date=date)
        
        return df
        
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}


def get_index_quotation(index_code="000001"):
    """
    获取指数行情
    
    Args:
        index_code: 指数代码
            000001 - 上证指数
            399001 - 深证成指
            399006 - 创业板指
            000300 - 沪深300
            000016 - 上证50
    
    Returns:
        DataFrame: 指数数据
    """
    try:
        import akshare as ak
        
        df = ak.stock_zh_index_spot_em(symbol=index_code)
        
        return df
        
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}


def get_main_index():
    """
    获取主要指数实时行情
    
    Returns:
        DataFrame: 主要指数行情
    """
    try:
        import akshare as ak
        
        df = ak.stock_zh_index_spot_em()
        # 筛选主要指数
        main_indices = ['上证指数', '深证成指', '创业板指', '沪深300', '上证50']
        df = df[df['名称'].isin(main_indices)]
        
        return df
        
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}


def format_dataframe_for_display(df):
    """
    格式化DataFrame为可读文本
    
    Args:
        df: pandas DataFrame
    
    Returns:
        str: 格式化后的文本
    """
    if isinstance(df, dict) and "error" in df:
        return df["error"]
    
    if df is None or df.empty:
        return "暂无数据"
    
    # 设置显示选项
    pd_display_options()
    
    # 转换为字符串
    return df.to_string()


def pd_display_options():
    """设置pandas显示选项"""
    try:
        import pandas as pd
        pd.set_option('display.max_columns', 10)
        pd.set_option('display.width', 200)
        pd.set_option('display.max_colwidth', 20)
    except:
        pass


def query_stock(stock_code):
    """
    综合查询股票信息
    
    Args:
        stock_code: 股票代码
    
    Returns:
        str: 格式化的股票信息
    """
    try:
        import akshare as ak
        import pandas as pd
        
        # 设置显示
        pd_display_options()
        
        # 获取实时行情
        df_all = ak.stock_zh_a_spot_em()
        stock_data = df_all[df_all['代码'] == stock_code]
        
        if stock_data.empty:
            return f"未找到股票 {stock_code}"
        
        info = stock_data.iloc[0]
        
        # 格式化输出
        result = f"""
=== {info['名称']} ({stock_code}) ===
最新价: {info['最新价']}
涨跌幅: {info['涨跌幅']}%
涨跌额: {info['涨跌额']}
成交量: {info['成交量']}手
成交额: {info['成交额']}万
最高: {info['最高']}
最低: {info['最低']}
今开: {info['今开']}
昨收: {info['昨收']}
市盈率(动态): {info['市盈率-动态']}
市净率: {info['市净率']}
总市值: {info['总市值']}
流通市值: {info['流通市值']}
换手率: {info['换手率']}%
"""
        return result
        
    except Exception as e:
        return f"查询失败: {str(e)}"


# 主函数
if __name__ == "__main__":
    import pandas as pd
    
    pd_display_options()
    
    print("=== 炒股教练行情查询 ===")
    print("1. 查询个股行情")
    print("2. 查看主要指数")
    print("3. 查看板块行情")
    print("4. 查看涨停板")
    print("5. 查看资金流向")
    print("6. 查看龙虎榜")
    print()
    
    # 示例：查询上证指数
    print("=== 上证指数 ===")
    df = get_main_index()
    if not isinstance(df, dict):
        print(df)
