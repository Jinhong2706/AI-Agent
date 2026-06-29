#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音对标账号工具 - 竞品动态监控脚本
功能：实时监控对标账号的更新、爆款、直播等动态变化
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import time


@dataclass
class CompetitorUpdate:
    """竞品动态更新"""
    account_id: str = ""
    account_name: str = ""
    update_type: str = ""  # video/live/follower/engagement
    content: str = ""
    timestamp: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    alert_level: str = "normal"  # normal/warning/critical


@dataclass
class MonitoringTask:
    """监控任务"""
    task_id: str = ""
    account_ids: List[str] = field(default_factory=list)
    monitor_types: List[str] = field(default_factory=list)  # video/live/follower/engagement
    frequency: str = "daily"  # real-time/hourly/daily
    alert_channels: List[str] = field(default_factory=list)
    status: str = "active"
    created_at: str = ""
    last_run: str = ""


class CompetitorMonitor:
    """竞品动态监控器"""
    
    # 预警阈值配置
    ALERT_THRESHOLDS = {
        "follower_spike": {
            "threshold": 5000,  # 24小时内涨粉超过5000
            "level": "warning"
        },
        "viral_video": {
            "threshold": 1000000,  # 播放量超过100万
            "level": "critical"
        },
        "engagement_drop": {
            "threshold": -30,  # 互动率下降超过30%
            "level": "warning"
        },
        "content_pivot": {
            "threshold": 0.3,  # 内容方向变化超过30%
            "level": "normal"
        },
        "live_peak": {
            "threshold": 10000,  # 峰值在线超过1万
            "level": "warning"
        }
    }
    
    def __init__(self):
        self.tasks: Dict[str, MonitoringTask] = {}
        self.alert_history: List[Dict] = []
        self.baseline_cache: Dict[str, Dict] = {}
    
    def create_monitoring_task(
        self,
        account_ids: List[str],
        monitor_types: List[str] = None,
        frequency: str = "daily",
        alert_channels: List[str] = None
    ) -> MonitoringTask:
        """
        创建监控任务
        
        Args:
            account_ids: 要监控的账号ID列表
            monitor_types: 监控类型
            frequency: 监控频率
            alert_channels: 告警渠道
            
        Returns:
            MonitoringTask: 监控任务对象
        """
        if monitor_types is None:
            monitor_types = ["video", "follower", "engagement"]
        
        if alert_channels is None:
            alert_channels = ["console"]
        
        task = MonitoringTask(
            task_id=f"task_{int(time.time())}",
            account_ids=account_ids,
            monitor_types=monitor_types,
            frequency=frequency,
            alert_channels=alert_channels,
            created_at=datetime.now().isoformat(),
            last_run=datetime.now().isoformat()
        )
        
        self.tasks[task.task_id] = task
        return task
    
    def set_baseline(self, account_id: str, baseline_data: Dict[str, Any]) -> None:
        """
        设置基准数据
        
        Args:
            account_id: 账号ID
            baseline_data: 基准数据
        """
        self.baseline_cache[account_id] = {
            "data": baseline_data,
            "timestamp": datetime.now().isoformat()
        }
    
    def check_updates(
        self,
        account_id: str,
        current_data: Dict[str, Any]
    ) -> List[CompetitorUpdate]:
        """
        检查账号动态
        
        Args:
            account_id: 账号ID
            current_data: 当前数据
            
        Returns:
            List[CompetitorUpdate]: 动态更新列表
        """
        updates = []
        baseline = self.baseline_cache.get(account_id, {}).get("data", {})
        
        # 检查粉丝变化
        if "followers" in current_data and "followers" in baseline:
            follower_change = current_data["followers"] - baseline["followers"]
            if follower_change >= self.ALERT_THRESHOLDS["follower_spike"]["threshold"]:
                update = CompetitorUpdate(
                    account_id=account_id,
                    account_name=current_data.get("nickname", ""),
                    update_type="follower",
                    content=f"24小时涨粉 {follower_change:,}",
                    timestamp=datetime.now().isoformat(),
                    metrics={"change": follower_change},
                    alert_level=self.ALERT_THRESHOLDS["follower_spike"]["level"]
                )
                updates.append(update)
        
        # 检查视频更新
        if "recent_videos" in current_data:
            baseline_video_ids = set(baseline.get("recent_video_ids", []))
            current_video_ids = set(current_data.get("recent_video_ids", []))
            
            new_videos = current_video_ids - baseline_video_ids
            if new_videos:
                update = CompetitorUpdate(
                    account_id=account_id,
                    account_name=current_data.get("nickname", ""),
                    update_type="video",
                    content=f"发布新视频 {len(new_videos)} 条",
                    timestamp=datetime.now().isoformat(),
                    metrics={"new_videos": len(new_videos)},
                    alert_level="normal"
                )
                updates.append(update)
        
        # 检查爆款视频
        if "viral_videos" in current_data:
            for viral in current_data["viral_videos"]:
                if viral.get("views", 0) >= self.ALERT_THRESHOLDS["viral_video"]["threshold"]:
                    update = CompetitorUpdate(
                        account_id=account_id,
                        account_name=current_data.get("nickname", ""),
                        update_type="viral",
                        content=f"爆款视频: {viral.get('title', '')[:20]}...",
                        timestamp=datetime.now().isoformat(),
                        metrics={"views": viral.get("views", 0)},
                        alert_level=self.ALERT_THRESHOLDS["viral_video"]["level"]
                    )
                    updates.append(update)
        
        # 检查直播动态
        if "recent_live" in current_data:
            live = current_data["recent_live"]
            if live.get("peak_viewers", 0) >= self.ALERT_THRESHOLDS["live_peak"]["threshold"]:
                update = CompetitorUpdate(
                    account_id=account_id,
                    account_name=current_data.get("nickname", ""),
                    update_type="live",
                    content=f"直播峰值 {live.get('peak_viewers', 0):,} 人在线",
                    timestamp=datetime.now().isoformat(),
                    metrics={
                        "peak": live.get("peak_viewers", 0),
                        "sales": live.get("sales_amount", 0)
                    },
                    alert_level=self.ALERT_THRESHOLDS["live_peak"]["level"]
                )
                updates.append(update)
        
        # 检查互动率变化
        if "engagement_rate" in current_data and "engagement_rate" in baseline:
            current_rate = current_data["engagement_rate"]
            baseline_rate = baseline["engagement_rate"]
            
            if baseline_rate > 0:
                change_rate = (current_rate - baseline_rate) / baseline_rate * 100
                
                if change_rate <= self.ALERT_THRESHOLDS["engagement_drop"]["threshold"]:
                    update = CompetitorUpdate(
                        account_id=account_id,
                        account_name=current_data.get("nickname", ""),
                        update_type="engagement",
                        content=f"互动率下降 {abs(change_rate):.1f}%",
                        timestamp=datetime.now().isoformat(),
                        metrics={"change": change_rate},
                        alert_level=self.ALERT_THRESHOLDS["engagement_drop"]["level"]
                    )
                    updates.append(update)
        
        # 检查内容方向变化
        if "content_matrix" in current_data and "content_matrix" in baseline:
            matrix_change = self._calculate_matrix_change(
                baseline["content_matrix"],
                current_data["content_matrix"]
            )
            
            if matrix_change >= self.ALERT_THRESHOLDS["content_pivot"]["threshold"]:
                update = CompetitorUpdate(
                    account_id=account_id,
                    account_name=current_data.get("nickname", ""),
                    update_type="pivot",
                    content=f"内容方向调整 {matrix_change*100:.0f}%",
                    timestamp=datetime.now().isoformat(),
                    metrics={"change_rate": matrix_change},
                    alert_level="warning"
                )
                updates.append(update)
        
        return updates
    
    def _calculate_matrix_change(
        self, 
        baseline: Dict[str, float], 
        current: Dict[str, float]
    ) -> float:
        """计算内容矩阵变化幅度"""
        total_change = 0
        
        all_keys = set(baseline.keys()) | set(current.keys())
        for key in all_keys:
            base_val = baseline.get(key, 0)
            curr_val = current.get(key, 0)
            
            if base_val > 0:
                change = abs(curr_val - base_val) / base_val
                total_change += change
        
        return total_change / len(all_keys) if all_keys else 0
    
    def execute_monitoring(
        self, 
        task_id: str,
        accounts_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        执行监控任务
        
        Args:
            task_id: 任务ID
            accounts_data: 账号数据字典
            
        Returns:
            Dict: 监控结果
        """
        task = self.tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}
        
        results = {
            "task_id": task_id,
            "execution_time": datetime.now().isoformat(),
            "accounts_checked": 0,
            "updates_detected": [],
            "alerts": []
        }
        
        for account_id in task.account_ids:
            if account_id not in accounts_data:
                continue
            
            current_data = accounts_data[account_id]
            updates = self.check_updates(account_id, current_data)
            
            results["accounts_checked"] += 1
            results["updates_detected"].extend(updates)
            
            # 收集告警
            for update in updates:
                if update.alert_level in ["warning", "critical"]:
                    results["alerts"].append({
                        "account_id": account_id,
                        "account_name": update.account_name,
                        "update": update
                    })
            
            # 更新基准数据
            self.baseline_cache[account_id] = {
                "data": current_data,
                "timestamp": datetime.now().isoformat()
            }
        
        # 更新任务状态
        task.last_run = datetime.now().isoformat()
        
        # 记录告警历史
        self.alert_history.extend(results["alerts"])
        
        return results
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """获取监控汇总"""
        summary = {
            "total_tasks": len(self.tasks),
            "active_tasks": len([t for t in self.tasks.values() if t.status == "active"]),
            "monitored_accounts": set(),
            "total_alerts": len(self.alert_history),
            "recent_alerts": []
        }
        
        for task in self.tasks.values():
            summary["monitored_accounts"].update(task.account_ids)
        
        summary["monitored_accounts"] = len(summary["monitored_accounts"])
        
        # 最近告警
        recent = sorted(
            self.alert_history, 
            key=lambda x: x.get("update", {}).get("timestamp", ""), 
            reverse=True
        )[:10]
        
        summary["recent_alerts"] = recent
        
        return summary
    
    def generate_alert_report(
        self, 
        alerts: List[Dict],
        time_range: str = "7d"
    ) -> str:
        """
        生成告警报告
        
        Args:
            alerts: 告警列表
            time_range: 时间范围
            
        Returns:
            str: 告警报告
        """
        # 统计告警类型
        alert_type_counts = defaultdict(int)
        critical_count = 0
        warning_count = 0
        
        for alert in alerts:
            update = alert.get("update", {})
            alert_type_counts[update.update_type] += 1
            
            if update.alert_level == "critical":
                critical_count += 1
            elif update.alert_level == "warning":
                warning_count += 1
        
        report_lines = [
            "=" * 60,
            "🚨 竞品动态告警报告",
            "=" * 60,
            "",
            f"📊 监控时间范围: 最近{time_range}",
            f"📊 总告警数: {len(alerts)}",
            f"   🔴 严重告警: {critical_count}",
            f"   🟡 警告告警: {warning_count}",
            "",
            "-" * 60,
            "一、告警类型分布",
            "-" * 60,
            "",
        ]
        
        for alert_type, count in sorted(alert_type_counts.items(), key=lambda x: x[1], reverse=True):
            type_names = {
                "follower": "📈 粉丝暴涨",
                "video": "📹 新视频发布",
                "viral": "🔥 爆款视频",
                "engagement": "📉 互动下降",
                "live": "🎬 直播动态",
                "pivot": "🔄 内容转型"
            }
            report_lines.append(f"  {type_names.get(alert_type, alert_type)}: {count} 条")
        
        report_lines.extend([
            "",
            "-" * 60,
            "二、紧急告警详情",
            "-" * 60,
            "",
        ])
        
        critical_alerts = [a for a in alerts if a.get("update", {}).alert_level == "critical"]
        for i, alert in enumerate(critical_alerts[:5], 1):
            update = alert.get("update", {})
            report_lines.extend([
                f"[{i}] {update.account_name}",
                f"    类型: {update.update_type}",
                f"    内容: {update.content}",
                f"    时间: {update.timestamp}",
                "",
            ])
        
        report_lines.extend([
            "-" * 60,
            "三、监控建议",
            "-" * 60,
            "",
        ])
        
        suggestions = self._generate_monitoring_suggestions(alert_type_counts)
        for i, suggestion in enumerate(suggestions, 1):
            report_lines.append(f"  {i}. {suggestion}")
        
        report_lines.extend([
            "",
            "=" * 60,
            f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 60,
        ])
        
        return "\n".join(report_lines)
    
    def _generate_monitoring_suggestions(
        self, 
        alert_type_counts: Dict[str, int]
    ) -> List[str]:
        """生成监控建议"""
        suggestions = []
        
        if alert_type_counts.get("follower", 0) > 5:
            suggestions.append("关注竞品粉丝暴涨原因，及时调整内容方向")
        
        if alert_type_counts.get("viral", 0) > 3:
            suggestions.append("分析竞品爆款规律，快速借鉴创作")
        
        if alert_type_counts.get("pivot", 0) > 2:
            suggestions.append("竞品可能正在进行内容转型，提前布局应对")
        
        if alert_type_counts.get("live", 0) > 5:
            suggestions.append("关注竞品直播动态，学习直播技巧和选品策略")
        
        if not suggestions:
            suggestions.append("继续保持监控，关注竞品常规更新")
            suggestions.append("定期复盘竞品数据，发现规律性变化")
        
        return suggestions
    
    def export_monitoring_data(self, format: str = "json") -> str:
        """
        导出监控数据
        
        Args:
            format: 导出格式
            
        Returns:
            str: 导出数据
        """
        import json
        
        data = {
            "tasks": [vars(t) for t in self.tasks.values()],
            "baselines": {
                aid: {
                    "timestamp": info["timestamp"],
                    "keys": list(info["data"].keys())
                }
                for aid, info in self.baseline_cache.items()
            },
            "alert_history": [
                {
                    "account_id": a["account_id"],
                    "account_name": a["account_name"],
                    "update_type": a["update"]["update_type"],
                    "alert_level": a["update"]["alert_level"],
                    "timestamp": a["update"]["timestamp"]
                }
                for a in self.alert_history
            ],
            "export_time": datetime.now().isoformat()
        }
        
        if format == "json":
            return json.dumps(data, ensure_ascii=False, indent=2)
        else:
            return str(data)


def main():
    """主函数 - 演示竞品监控"""
    print("=" * 60)
    print("抖音竞品动态监控工具")
    print("=" * 60)
    
    # 初始化监控器
    monitor = CompetitorMonitor()
    
    # 创建监控任务
    print("\n【1】创建监控任务")
    task = monitor.create_monitoring_task(
        account_ids=["acc_001", "acc_002", "acc_003"],
        monitor_types=["video", "follower", "viral", "live"],
        frequency="daily",
        alert_channels=["console"]
    )
    print(f"任务ID: {task.task_id}")
    print(f"监控账号: {len(task.account_ids)} 个")
    print(f"监控类型: {', '.join(task.monitor_types)}")
    
    # 设置基准数据
    print("\n【2】设置基准数据")
    monitor.set_baseline("acc_001", {
        "followers": 500000,
        "engagement_rate": 6.5,
        "recent_video_ids": ["v1", "v2", "v3"],
        "content_matrix": {"引流型": 30, "固粉型": 40, "转化型": 20, "人设型": 10}
    })
    
    monitor.set_baseline("acc_002", {
        "followers": 800000,
        "engagement_rate": 5.8,
        "recent_video_ids": ["v10", "v11", "v12"]
    })
    
    print("基准数据已设置 ✓")
    
    # 模拟当前数据
    print("\n【3】执行监控检查")
    accounts_data = {
        "acc_001": {
            "nickname": "竞品账号A",
            "followers": 512000,  # 涨粉12000
            "engagement_rate": 5.2,  # 下降
            "recent_video_ids": ["v1", "v2", "v3", "v4", "v5"],  # 新增2个
            "viral_videos": [
                {"title": "这个技巧太实用了", "views": 1500000}
            ],
            "recent_live": {
                "peak_viewers": 15000,
                "sales_amount": 50000
            },
            "content_matrix": {"引流型": 50, "固粉型": 30, "转化型": 15, "人设型": 5}
        },
        "acc_002": {
            "nickname": "竞品账号B",
            "followers": 810000,
            "engagement_rate": 6.0,
            "recent_video_ids": ["v10", "v11", "v12", "v13"]
        }
    }
    
    results = monitor.execute_monitoring(task.task_id, accounts_data)
    
    print(f"检查账号数: {results['accounts_checked']}")
    print(f"检测到动态: {len(results['updates_detected'])}")
    print(f"触发告警: {len(results['alerts'])}")
    
    # 显示告警
    if results["alerts"]:
        print("\n🚨 告警详情:")
        for alert in results["alerts"]:
            print(f"  [{alert['update'].alert_level.upper()}] {alert['account_name']}")
            print(f"    {alert['update'].content}")
    
    # 获取监控汇总
    print("\n【4】监控状态汇总")
    summary = monitor.get_monitoring_summary()
    
    print(f"活跃任务: {summary['active_tasks']}")
    print(f"监控账号: {summary['monitored_accounts']}")
    print(f"总告警数: {summary['total_alerts']}")
    
    # 生成告警报告
    print("\n【5】生成告警报告")
    report = monitor.generate_alert_report(results["alerts"])
    print(report)
    
    print("\n" + "=" * 60)
    print("监控完成！")


if __name__ == "__main__":
    main()
