#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金评价分析工具

支持从天天基金网获取基金持仓数据、季度对比分析等功能。
"""

import requests
import re
import csv
import sys
from datetime import datetime


class FundEvaluator:
    """基金评价分析类"""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
    
    def get_holdings(self, fund_code, quarter=None):
        """
        获取基金季度持仓数据
        
        参数:
            fund_code: 基金代码，如 "519702"
            quarter: 季度，如 "2025年4季度"，为None则获取最新
        
        返回:
            dict: 包含持仓数据的字典
        """
        url = f"https://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjcc&code={fund_code}&topline=100"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                return {"error": f"请求失败，状态码: {response.status_code}"}
            
            quarters_data = self._extract_all_quarters(response.text)
            
            if not quarters_data:
                return {"error": "未找到持仓数据"}
            
            # 选择季度
            if quarter:
                selected = None
                for q in quarters_data:
                    if quarter in q['quarter']:
                        selected = q
                        break
                if not selected:
                    selected = quarters_data[0]
            else:
                selected = quarters_data[0]
            
            return {
                "fund_code": fund_code,
                "quarter": selected['quarter'],
                "date": selected['date'],
                "holdings": selected['holdings'],
                "all_quarters": [q['quarter'] for q in quarters_data]
            }
            
        except Exception as e:
            return {"error": f"获取数据时出错: {e}"}
    
    def print_holdings(self, data):
        """打印持仓数据表格"""
        if "error" in data:
            print(f"❌ {data['error']}")
            return
        
        print(f"\n{'=' * 80}")
        print(f"📊 {data['fund_code']} - {data['quarter']}持仓明细")
        print(f"📅 报告截止: {data['date']}")
        print(f"{'=' * 80}")
        
        print(f"\n{'排名':<6}{'股票代码':<12}{'股票名称':<15}{'占净值比':<12}{'持股数(万股)':<15}{'持仓市值(万元)':<15}")
        print("-" * 80)
        
        total_ratio = 0
        for item in data['holdings']:
            print(f"{item['rank']:<6}{item['code']:<12}{item['name']:<15}{item['ratio']:<12}{item['shares']:<15}{item['market_value']:<15}")
            try:
                ratio_str = item['ratio'].replace('%', '')
                total_ratio += float(ratio_str)
            except:
                pass
        
        print("-" * 80)
        print(f"{'合计':<33}{total_ratio:.2f}%")
    
    def compare_quarters(self, fund_code, q1=None, q2=None):
        """
        对比两个季度的持仓变化
        
        参数:
            fund_code: 基金代码
            q1: 较新的季度，如 "2025年4季度"，为None则取最新
            q2: 较旧的季度，如 "2025年3季度"，为None则取次新
        """
        url = f"https://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjcc&code={fund_code}&topline=100"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.encoding = 'utf-8'
            
            quarters_data = self._extract_all_quarters(response.text)
            
            if len(quarters_data) < 2:
                print("❌ 数据不足，无法进行季度对比")
                return
            
            # 选择季度
            if q1:
                data1 = next((q for q in quarters_data if q1 in q['quarter']), quarters_data[0])
            else:
                data1 = quarters_data[0]
                
            if q2:
                data2 = next((q for q in quarters_data if q2 in q['quarter']), quarters_data[1])
            else:
                data2 = quarters_data[1]
            
            print(f"\n{'=' * 80}")
            print(f"对比 {fund_code} 的季度持仓变化")
            print(f"{'=' * 80}")
            print(f"\n对比: {data1['quarter']} vs {data2['quarter']}")
            print("-" * 80)
            
            # 构建持仓字典
            holdings1 = {item['code']: item for item in data1['holdings']}
            holdings2 = {item['code']: item for item in data2['holdings']}
            
            # 新增持仓
            new_stocks = set(holdings1.keys()) - set(holdings2.keys())
            if new_stocks:
                print(f"\n📈 新增持仓 ({len(new_stocks)}只):")
                for code in sorted(new_stocks, key=lambda x: int(holdings1[x]['rank'])):
                    item = holdings1[code]
                    print(f"  + {item['code']} {item['name']} - 占比: {item['ratio']}")
            
            # 减持或清仓
            removed_stocks = set(holdings2.keys()) - set(holdings1.keys())
            if removed_stocks:
                print(f"\n📉 清仓/减持至前10外 ({len(removed_stocks)}只):")
                for code in sorted(removed_stocks, key=lambda x: int(holdings2[x]['rank'])):
                    item = holdings2[code]
                    print(f"  - {item['code']} {item['name']} - 上季占比: {item['ratio']}")
            
            # 仓位变化
            common_stocks = set(holdings1.keys()) & set(holdings2.keys())
            if common_stocks:
                changes = []
                for code in common_stocks:
                    h1 = holdings1[code]
                    h2 = holdings2[code]
                    r1 = float(h1['ratio'].replace('%', '')) if '%' in h1['ratio'] else 0
                    r2 = float(h2['ratio'].replace('%', '')) if '%' in h2['ratio'] else 0
                    change = r1 - r2
                    if abs(change) > 0.5:
                        changes.append({
                            'code': code,
                            'name': h1['name'],
                            'old': r2,
                            'new': r1,
                            'change': change
                        })
                
                if changes:
                    changes.sort(key=lambda x: abs(x['change']), reverse=True)
                    print(f"\n🔄 仓位变化:")
                    for c in changes:
                        direction = "↑" if c['change'] > 0 else "↓"
                        print(f"  {direction} {c['code']} {c['name']}: {c['old']:.2f}% → {c['new']:.2f}% ({c['change']:+.2f}%)")
            
        except Exception as e:
            print(f"❌ 对比分析时出错: {e}")
    
    def export_to_csv(self, data, filename=None):
        """导出持仓数据到CSV文件"""
        if "error" in data:
            print(f"❌ {data['error']}")
            return
        
        if filename is None:
            filename = f"{data['fund_code']}_{data['quarter'].replace('年', '').replace('季度', 'Q')}_holdings.csv"
        
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['排名', '股票代码', '股票名称', '占净值比', '持股数(万股)', '持仓市值(万元)'])
            for item in data['holdings']:
                writer.writerow([item['rank'], item['code'], item['name'], item['ratio'], item['shares'], item['market_value']])
        
        print(f"\n✅ 数据已导出到: {filename}")
        return filename
    
    def _extract_all_quarters(self, content):
        """从页面内容中提取所有季度的持仓数据"""
        quarters = []
        quarter_blocks = re.split(r'<div class=\'box\'><div class=\'boxitem w790\'>', content)
        
        for block in quarter_blocks[1:]:
            quarter_match = re.search(r'(\d{4}年\d季度).*?截止至：<font class=\'px12\'>(\d{4}-\d{2}-\d{2})', block)
            if not quarter_match:
                continue
            
            quarter_name = quarter_match.group(1)
            quarter_date = quarter_match.group(2)
            
            holdings = self._extract_holdings_from_table(block)
            
            if holdings:
                quarters.append({
                    'quarter': quarter_name,
                    'date': quarter_date,
                    'holdings': holdings
                })
        
        return quarters
    
    def _extract_holdings_from_table(self, html_block):
        """从HTML表格中提取持仓数据"""
        holdings = []
        rows = re.findall(r'<tr>(.*?)</tr>', html_block, re.DOTALL)
        
        for row in rows:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
            if len(cells) < 6:
                continue
            
            rank = self._clean_text(cells[0])
            code = self._clean_text(cells[1])
            name = self._clean_text(cells[2])
            
            if len(cells) >= 9:
                ratio = self._clean_text(cells[6])
                shares = self._clean_text(cells[7])
                market_value = self._clean_text(cells[8])
            elif len(cells) >= 7:
                ratio = self._clean_text(cells[4])
                shares = self._clean_text(cells[5])
                market_value = self._clean_text(cells[6])
            else:
                continue
            
            code_match = re.search(r'>(\d{6})<', cells[1])
            if code_match:
                code = code_match.group(1)
            
            name_match = re.search(r'>([^<]+)<', cells[2])
            if name_match:
                name = name_match.group(1)
            
            if rank and code and name:
                holdings.append({
                    'rank': rank,
                    'code': code,
                    'name': name,
                    'ratio': ratio,
                    'shares': shares,
                    'market_value': market_value
                })
        
        return holdings
    
    def _clean_text(self, text):
        """清洗HTML文本"""
        text = re.sub(r'<[^>]+>', '', text)
        text = text.strip()
        return text


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='基金评价分析工具')
    parser.add_argument('fund_code', help='基金代码，如 519702')
    parser.add_argument('-q', '--quarter', help='指定季度，如 "2025年4季度"')
    parser.add_argument('-c', '--compare', action='store_true', help='对比季度变化')
    parser.add_argument('-e', '--export', metavar='FILE', help='导出到CSV文件')
    parser.add_argument('-l', '--list', action='store_true', help='列出所有可用季度')
    
    args = parser.parse_args()
    
    evaluator = FundEvaluator()
    
    if args.list:
        result = evaluator.get_holdings(args.fund_code)
        if "all_quarters" in result:
            print(f"\n{args.fund_code} 可用的季度报告:")
            for i, q in enumerate(result['all_quarters'], 1):
                print(f"  {i}. {q}")
    elif args.compare:
        evaluator.compare_quarters(args.fund_code, args.quarter)
    else:
        result = evaluator.get_holdings(args.fund_code, args.quarter)
        evaluator.print_holdings(result)
        
        if args.export:
            evaluator.export_to_csv(result, args.export)


if __name__ == "__main__":
    main()
