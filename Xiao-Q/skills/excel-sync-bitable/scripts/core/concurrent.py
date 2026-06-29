"""并发导出模块"""
import concurrent.futures
from typing import List, Dict, Callable, Any
import time


def concurrent_export(
    export_func: Callable,
    items: List[Dict],
    max_workers: int = 3,
    progress_callback: Callable[[str, int, int], None] = None
) -> List[Dict]:
    """并发导出数据
    
    Args:
        export_func: 导出函数，签名为 (item) -> Dict
        items: 待导出的项目列表
        max_workers: 最大并发数（默认3，避免API限流）
        progress_callback: 进度回调函数 (item_name, current, total)
    
    Returns:
        list: 导出结果列表
    
    Example:
        >>> def export_table(table_info):
        ...     return {'name': table_info['name'], 'data': ...}
        >>> results = concurrent_export(export_table, [
        ...     {'name': '表1', 'id': 'tbl1'},
        ...     {'name': '表2', 'id': 'tbl2'}
        ... ])
    """
    results = []
    total = len(items)
    completed = 0
    
    print(f"🚀 开始并发导出 {total} 个项目（并发数: {max_workers}）")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_item = {
            executor.submit(export_func, item): item 
            for item in items
        }
        
        # 收集结果
        for future in concurrent.futures.as_completed(future_to_item):
            item = future_to_item[future]
            item_name = item.get('name', str(item))
            
            try:
                result = future.result()
                results.append(result)
                completed += 1
                
                if progress_callback:
                    progress_callback(item_name, completed, total)
                else:
                    print(f"  ✅ [{completed}/{total}] {item_name}")
                    
            except Exception as e:
                print(f"  ❌ [{completed + 1}/{total}] {item_name}: {str(e)}")
                completed += 1
    
    print(f"✅ 并发导出完成：{len(results)}/{total} 成功")
    return results


def batch_export_with_rate_limit(
    export_func: Callable,
    items: List[Dict],
    batch_size: int = 5,
    delay_seconds: float = 0.5
) -> List[Dict]:
    """批量导出（带速率限制）
    
    Args:
        export_func: 导出函数
        items: 待导出的项目列表
        batch_size: 每批数量
        delay_seconds: 批次间延迟（秒）
    
    Returns:
        list: 导出结果列表
    """
    results = []
    total = len(items)
    
    print(f"📦 开始批量导出 {total} 个项目（每批 {batch_size} 个，间隔 {delay_seconds}s）")
    
    for i in range(0, total, batch_size):
        batch = items[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total + batch_size - 1) // batch_size
        
        print(f"  📤 处理第 {batch_num}/{total_batches} 批...")
        
        batch_results = concurrent_export(
            export_func, 
            batch, 
            max_workers=min(batch_size, 3)
        )
        results.extend(batch_results)
        
        # 批次间延迟，避免API限流
        if i + batch_size < total:
            time.sleep(delay_seconds)
    
    return results


class ProgressTracker:
    """进度追踪器"""
    
    def __init__(self, total: int, desc: str = "导出"):
        self.total = total
        self.completed = 0
        self.failed = 0
        self.desc = desc
        self.start_time = time.time()
    
    def update(self, success: bool = True):
        """更新进度"""
        if success:
            self.completed += 1
        else:
            self.failed += 1
        
        self._print_progress()
    
    def _print_progress(self):
        """打印进度"""
        elapsed = time.time() - self.start_time
        rate = (self.completed + self.failed) / elapsed if elapsed > 0 else 0
        
        progress_bar = self._get_progress_bar()
        print(f"\r  {self.desc}: {progress_bar} [{self.completed}/{self.total}] "
              f"({rate:.1f} items/s){'  ' * 10}", end='', flush=True)
    
    def _get_progress_bar(self, width: int = 20) -> str:
        """生成进度条"""
        filled = int(width * (self.completed + self.failed) / self.total)
        return '█' * filled + '░' * (width - filled)
    
    def finish(self):
        """完成打印"""
        elapsed = time.time() - self.start_time
        print(f"\n✅ {self.desc}完成: {self.completed} 成功, {self.failed} 失败, "
              f"耗时 {elapsed:.1f}s")
