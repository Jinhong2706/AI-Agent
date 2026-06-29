#!/usr/bin/env python3
"""
妙想金融数据查询脚本
整合mx-data、mx-search、mx-xuangu、mx-zixuan、mx-moni五大功能
"""

import os
import sys

# 设置API Key
os.environ['MX_APIKEY'] = os.environ.get('MX_APIKEY', '')

def run_mx_script(script_name, query):
    """运行妙想脚本"""
    script_path = os.path.join(os.path.dirname(__file__), '..', '..', f'mx-{script_name}', f'mx_{script_name}.py')
    if os.path.exists(script_path):
        os.system(f'MX_APIKEY={os.environ["MX_APIKEY"]} python3 {script_path} "{query}"')
    else:
        print(f"脚本不存在: {script_path}")

def query_data(query):
    """金融数据查询 (mx-data)"""
    run_mx_script('data', query)

def search_news(query):
    """资讯搜索 (mx-search)"""
    run_mx_script('search', query)

def select_stocks(query):
    """智能选股 (mx-xuangu)"""
    run_mx_script('xuangu', query)

def manage_watchlist(query):
    """自选股管理 (mx-zixuan)"""
    run_mx_script('zixuan', query)

def manage_portfolio(query):
    """模拟组合管理 (mx-moni)"""
    run_mx_script('moni', query)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python mx_query.py <功能> <查询语句>")
        print("功能: data|search|xuangu|zixuan|moni")
        sys.exit(1)
    
    func = sys.argv[1]
    query = ' '.join(sys.argv[2:])
    
    funcs = {
        'data': query_data,
        'search': search_news,
        'xuangu': select_stocks,
        'zixuan': manage_watchlist,
        'moni': manage_portfolio,
    }
    
    if func in funcs:
        funcs[func](query)
    else:
        print(f"未知功能: {func}")
        print("可用功能: data, search, xuangu, zixuan, moni")
