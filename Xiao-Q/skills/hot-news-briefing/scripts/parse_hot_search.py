#!/usr/bin/env python3
"""
热搜数据解析辅助脚本
用于解析从 web_search 返回的热搜数据
"""

import re
import sys
from typing import List, Dict

def parse_weibo_hot_search(search_results: str) -> List[Dict]:
    """
    解析微博热搜搜索结果
    
    Args:
        search_results: web_search 返回的微博热搜文本
    
    Returns:
        热搜列表，每项包含 rank, title, heat
    """
    hot_searches = []
    
    # 匹配模式：排名. 标题 热度值
    pattern = r'(\d+)\.\s*(.+?)\s*(\d+[万]?讨论)?'
    
    lines = search_results.split('\n')
    for line in lines:
        match = re.search(pattern, line)
        if match:
            hot_searches.append({
                'rank': int(match.group(1)),
                'title': match.group(2).strip(),
                'heat': match.group(3) if match.group(3) else 'N/A',
                'platform': '微博'
            })
    
    return hot_searches

def parse_zhihu_hot_list(search_results: str) -> List[Dict]:
    """
    解析知乎热榜搜索结果
    """
    hot_list = []
    
    # 匹配模式：排名. 问题标题 关注数
    pattern = r'(\d+)\.\s*(.+?)\s*(\d+[万]?人关注)?'
    
    lines = search_results.split('\n')
    for line in lines:
        match = re.search(pattern, line)
        if match:
            hot_list.append({
                'rank': int(match.group(1)),
                'title': match.group(2).strip(),
                'followers': match.group(3) if match.group(3) else 'N/A',
                'platform': '知乎'
            })
    
    return hot_list

def parse_bilibili_hot(search_results: str) -> List[Dict]:
    """
    解析B站热门搜索结果
    """
    hot_videos = []
    
    # 匹配模式：排名. 视频标题 UP主 播放量
    pattern = r'(\d+)\.\s*(.+?)\s*(.+?)\s*(\d+[万]?播放)?'
    
    lines = search_results.split('\n')
    for line in lines:
        match = re.search(pattern, line)
        if match:
            hot_videos.append({
                'rank': int(match.group(1)),
                'title': match.group(2).strip(),
                'author': match.group(3).strip(),
                'views': match.group(4) if match.group(4) else 'N/A',
                'platform': 'B站'
            })
    
    return hot_videos

def aggregate_hot_topics(weibo_data: List[Dict], zhihu_data: List[Dict], 
                         bilibili_data: List[Dict]) -> List[Dict]:
    """
    聚合三大平台热搜，去重并排序
    """
    all_topics = []
    
    # 合并所有话题
    all_topics.extend(weibo_data)
    all_topics.extend(zhihu_data)
    all_topics.extend(bilibili_data)
    
    # 简单去重（基于标题相似度）
    seen_titles = set()
    unique_topics = []
    
    for topic in all_topics:
        title_key = topic['title'][:10]  # 取前10个字符作为key
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_topics.append(topic)
    
    # 按排名排序（简单处理）
    unique_topics.sort(key=lambda x: x.get('rank', 999))
    
    return unique_topics[:5]  # 返回Top 5

def main():
    """
    主函数：演示用法
    """
    if len(sys.argv) < 2:
        print("用法: python parse_hot_search.py <platform>")
        print("platform: weibo | zhihu | bilibili")
        sys.exit(1)
    
    platform = sys.argv[1].lower()
    
    # 示例数据（实际使用时从 web_search 结果中获取）
    sample_data = {
        'weibo': "1. 高考加油 500万讨论\n2. 端午节放假安排 300万讨论",
        'zhihu': "1. 如何评价xxx？ 2000人关注\n2. 为什么xxx？ 1500人关注",
        'bilibili': "1. 视频标题1 UP主A 100万播放\n2. 视频标题2 UP主B 80万播放"
    }
    
    if platform in sample_data:
        if platform == 'weibo':
            result = parse_weibo_hot_search(sample_data[platform])
        elif platform == 'zhihu':
            result = parse_zhihu_hot_list(sample_data[platform])
        elif platform == 'bilibili':
            result = parse_bilibili_hot(sample_data[platform])
        else:
            print(f"未知平台: {platform}")
            sys.exit(1)
        
        print(f"\n{platform.upper()} 热搜解析结果:")
        for item in result:
            print(f"  {item['rank']}. {item['title']}")
    else:
        print(f"未找到 {platform} 的示例数据")

if __name__ == '__main__':
    main()
