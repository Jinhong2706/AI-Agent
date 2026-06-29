#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音对标账号工具 - 模块初始化
抖音对标账号分析核心脚本集合
功能：
1. account_collector - 对标账号信息采集
2. fan_profile_analyzer - 粉丝画像分析
3. viral_video_analyzer - 爆款视频分析
4. content_strategy_parser - 内容策略拆解
5. competitor_monitor - 竞品动态监控
6. benchmark_comparator - 数据对比分析
7. growth_strategy_generator - 增长策略生成
"""

from .account_collector import AccountCollector, AccountInfo, VideoInfo, LiveInfo
from .fan_profile_analyzer import FanProfileAnalyzer, FanProfile, ContentPreference
from .viral_video_analyzer import ViralVideoAnalyzer, ViralVideo, VideoAnalysis
from .content_strategy_parser import ContentStrategyParser, ContentStrategy, PersonaProfile
from .competitor_monitor import CompetitorMonitor, CompetitorUpdate, MonitoringTask
from .benchmark_comparator import BenchmarkComparator, AccountMetrics, MetricComparison
from .growth_strategy_generator import GrowthStrategyGenerator, GrowthStrategy, ContentPlan

__all__ = [
    # 数据类
    'AccountInfo',
    'VideoInfo', 
    'LiveInfo',
    'FanProfile',
    'ContentPreference',
    'ViralVideo',
    'VideoAnalysis',
    'ContentStrategy',
    'PersonaProfile',
    'CompetitorUpdate',
    'MonitoringTask',
    'AccountMetrics',
    'MetricComparison',
    'GrowthStrategy',
    'ContentPlan',
    # 分析器类
    'AccountCollector',
    'FanProfileAnalyzer',
    'ViralVideoAnalyzer',
    'ContentStrategyParser',
    'CompetitorMonitor',
    'BenchmarkComparator',
    'GrowthStrategyGenerator',
]

__version__ = '1.0.0'
__author__ = 'Douyin Master Team'
