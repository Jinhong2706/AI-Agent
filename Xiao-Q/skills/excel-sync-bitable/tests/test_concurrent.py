"""并发模块测试"""
import pytest
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from core.concurrent import concurrent_export, ProgressTracker


class TestConcurrentExport:
    """并发导出测试"""
    
    def test_concurrent_export_success(self):
        """测试成功导出"""
        def export_item(item):
            return {'name': item['name'], 'value': item['value'] * 2}
        
        items = [
            {'name': 'item1', 'value': 1},
            {'name': 'item2', 'value': 2},
            {'name': 'item3', 'value': 3}
        ]
        
        results = concurrent_export(export_item, items, max_workers=2)
        
        assert len(results) == 3
        names = {r['name'] for r in results}
        assert 'item1' in names
        assert 'item2' in names
        assert 'item3' in names
    
    def test_concurrent_export_with_failure(self):
        """测试部分失败"""
        def export_item(item):
            if item['value'] == 2:
                raise ValueError("Simulated error")
            return {'name': item['name'], 'value': item['value']}
        
        items = [
            {'name': 'item1', 'value': 1},
            {'name': 'item2', 'value': 2},
            {'name': 'item3', 'value': 3}
        ]
        
        results = concurrent_export(export_item, items, max_workers=2)
        
        # 只有 item1 和 item3 成功
        assert len(results) == 2
    
    def test_concurrent_export_empty(self):
        """测试空列表"""
        results = concurrent_export(lambda x: x, [], max_workers=2)
        assert len(results) == 0


class TestProgressTracker:
    """进度追踪器测试"""
    
    def test_progress_tracker_init(self):
        """测试初始化"""
        tracker = ProgressTracker(100, "导出")
        assert tracker.total == 100
        assert tracker.completed == 0
        assert tracker.failed == 0
    
    def test_progress_tracker_update(self):
        """测试更新"""
        tracker = ProgressTracker(10, "测试")
        tracker.update(success=True)
        assert tracker.completed == 1
        assert tracker.failed == 0
        
        tracker.update(success=False)
        assert tracker.completed == 1
        assert tracker.failed == 1
    
    def test_progress_bar(self):
        """测试进度条"""
        tracker = ProgressTracker(4, "测试")
        
        bar1 = tracker._get_progress_bar(width=4)
        assert bar1 == '░░░░'
        
        tracker.update(success=True)
        bar2 = tracker._get_progress_bar(width=4)
        assert bar2 == '█░░░'
        
        tracker.update(success=True)
        tracker.update(success=True)
        tracker.update(success=True)
        bar3 = tracker._get_progress_bar(width=4)
        assert bar3 == '████'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
