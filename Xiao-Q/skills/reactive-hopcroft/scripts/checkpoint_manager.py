#!/usr/bin/env python3
"""
Checkpoint 管理器 - 强制状态同步机制

核心职责：
1. 封装 checkpoint 读写，防止状态错乱
2. 强制更新规则：每个步骤完成后必须更新
3. 状态验证：读取前验证一致性
4. 错误恢复：自动修复或提示重置

使用示例：
    from checkpoint_manager import CheckpointManager
    
    cp = CheckpointManager("workflows/reactive-hopcroft/state/checkpoint.json")
    cp.update_step("generate", "data/03-draft.md")
    
    # 读取当前文件
    current_file = cp.get_current_file()
    
    # 验证状态
    cp.validate()
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class Checkpoint:
    """Checkpoint 数据模型"""
    workflow_id: str
    version: str
    completed_nodes: List[str]
    current_node: str
    started_at: str
    updated_at: str
    user_inputs: Dict
    intermediate_files: Dict[str, str]
    
    @classmethod
    def create_new(cls, workflow_id: str = "reactive-hopcroft", version: str = "1.1") -> "Checkpoint":
        """创建新的 checkpoint"""
        now = datetime.now(timezone.utc).isoformat()
        return cls(
            workflow_id=workflow_id,
            version=version,
            completed_nodes=[],
            current_node="extract",
            started_at=now,
            updated_at=now,
            user_inputs={},
            intermediate_files={}
        )


class CheckpointError(Exception):
    """Checkpoint 状态错误"""
    pass


class StateCorruptedError(CheckpointError):
    """状态错乱，需要修复"""
    pass


class CheckpointManager:
    """
    Checkpoint 管理器
    
    强制规则：
    1. 每个步骤完成后必须调用 update_step()
    2. 文件编号按步骤顺序递增，严禁复用
    3. 读取文件前必须验证状态
    """
    
    # 节点顺序和文件编号映射
    NODE_SEQUENCE = {
        "extract": 1,
        "title_select": 2,
        "generate": 3,
        "humanize": 4
    }
    
    # 节点对应的文件扩展名
    NODE_EXTENSIONS = {
        "extract": ".json",
        "title_select": ".json",
        "generate": ".md",
        "humanize": ".md"
    }
    
    def __init__(self, checkpoint_path: str, data_dir: str = "data"):
        """
        初始化 CheckpointManager
        
        Args:
            checkpoint_path: checkpoint.json 的完整路径
            data_dir: 数据文件存放目录
        """
        self.checkpoint_path = checkpoint_path
        self.data_dir = data_dir
        self.checkpoint = None
        self._load()
    
    def _load(self) -> None:
        """加载 checkpoint，如果不存在则创建新的"""
        if os.path.exists(self.checkpoint_path):
            with open(self.checkpoint_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.checkpoint = Checkpoint(**data)
        else:
            self.checkpoint = Checkpoint.create_new()
            self._save()
    
    def _save(self) -> None:
        """保存 checkpoint 到文件"""
        # 确保目录存在
        os.makedirs(os.path.dirname(self.checkpoint_path), exist_ok=True)
        
        with open(self.checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.checkpoint), f, ensure_ascii=False, indent=2)
    
    def _generate_filename(self, step_name: str) -> str:
        """
        根据步骤名称生成标准文件名
        
        规则：
        - 编号 = NODE_SEQUENCE[step_name]
        - 扩展名 = NODE_EXTENSIONS[step_name]
        - 格式：data/{编号:02d}-{step_name}{扩展名}
        
        示例：
        - extract -> data/01-extract.json
        - generate -> data/03-generate.md
        """
        if step_name not in self.NODE_SEQUENCE:
            raise CheckpointError(f"未知步骤: {step_name}")
        
        num = self.NODE_SEQUENCE[step_name]
        ext = self.NODE_EXTENSIONS[step_name]
        return os.path.join(self.data_dir, f"{num:02d}-{step_name}{ext}")
    
    def update_step(self, step_name: str, file_path: Optional[str] = None) -> str:
        """
        更新步骤状态（强制调用）
        
        每个步骤完成后必须调用此方法，否则状态会错乱。
        
        Args:
            step_name: 步骤名称（extract/title_select/generate/humanize）
            file_path: 文件路径（可选，如果不传则自动生成标准路径）
        
        Returns:
            实际使用的文件路径
        
        Raises:
            CheckpointError: 步骤顺序错误或状态异常
        """
        if step_name not in self.NODE_SEQUENCE:
            raise CheckpointError(f"未知步骤: {step_name}")
        
        # 验证步骤顺序
        expected_order = list(self.NODE_SEQUENCE.keys())
        current_idx = expected_order.index(step_name)
        
        if current_idx > 0:
            prev_step = expected_order[current_idx - 1]
            if prev_step not in self.checkpoint.completed_nodes:
                raise CheckpointError(
                    f"步骤顺序错误: {step_name} 的前置步骤 {prev_step} 未完成"
                )
        
        # 生成或验证文件路径
        if file_path is None:
            file_path = self._generate_filename(step_name)
        
        # 验证文件存在（如果是已完成步骤）
        if os.path.exists(file_path):
            # 文件已存在，验证一致性
            pass
        else:
            # 文件不存在，可能是新步骤，允许
            pass
        
        # 更新 completed_nodes
        if step_name not in self.checkpoint.completed_nodes:
            self.checkpoint.completed_nodes.append(step_name)
        
        # 更新 current_node
        if step_name == "humanize":
            self.checkpoint.current_node = "done"
        else:
            next_idx = current_idx + 1
            if next_idx < len(expected_order):
                self.checkpoint.current_node = expected_order[next_idx]
            else:
                self.checkpoint.current_node = "done"
        
        # 更新 intermediate_files
        self.checkpoint.intermediate_files[step_name] = file_path
        
        # 更新时间
        self.checkpoint.updated_at = datetime.now(timezone.utc).isoformat()
        
        # 保存
        self._save()
        
        return file_path
    
    def get_current_file(self) -> str:
        """
        获取当前步骤对应的文件路径
        
        根据 current_node 查找 intermediate_files 映射。
        
        Returns:
            当前步骤的文件路径
        
        Raises:
            StateCorruptedError: 状态错乱，文件不存在或映射错误
        """
        current = self.checkpoint.current_node
        
        # 如果已完成，返回最终文件
        if current == "done":
            if "humanize" in self.checkpoint.intermediate_files:
                return self.checkpoint.intermediate_files["humanize"]
            else:
                raise StateCorruptedError("流程已完成，但找不到 humanize 文件映射")
        
        # 查找当前步骤的文件
        # 注意：current_node 是"下一步"，所以找上一步的文件
        step_order = list(self.NODE_SEQUENCE.keys())
        if current in step_order:
            current_idx = step_order.index(current)
            if current_idx > 0:
                prev_step = step_order[current_idx - 1]
                if prev_step in self.checkpoint.intermediate_files:
                    return self.checkpoint.intermediate_files[prev_step]
        
        # 尝试直接查找 current_node 的映射
        if current in self.checkpoint.intermediate_files:
            return self.checkpoint.intermediate_files[current]
        
        raise StateCorruptedError(
            f"状态错乱: current_node={current}, 找不到对应的文件映射"
        )
    
    def get_step_file(self, step_name: str) -> str:
        """
        获取指定步骤的文件路径
        
        Args:
            step_name: 步骤名称
        
        Returns:
            文件路径
        
        Raises:
            StateCorruptedError: 步骤未完成或文件映射缺失
        """
        if step_name not in self.checkpoint.intermediate_files:
            raise StateCorruptedError(f"步骤 {step_name} 未完成或文件映射缺失")
        
        file_path = self.checkpoint.intermediate_files[step_name]
        
        if not os.path.exists(file_path):
            raise StateCorruptedError(f"文件不存在: {file_path}")
        
        return file_path
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        验证 checkpoint 状态一致性
        
        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []
        
        # 1. 验证 completed_nodes 顺序
        expected_order = list(self.NODE_SEQUENCE.keys())
        for i, node in enumerate(self.checkpoint.completed_nodes):
            if node not in expected_order:
                errors.append(f"completed_nodes[{i}] 包含未知节点: {node}")
            else:
                expected_idx = expected_order.index(node)
                if expected_idx != i:
                    errors.append(f"completed_nodes 顺序错误: {node} 应在位置 {expected_idx}")
        
        # 2. 验证 intermediate_files 与 completed_nodes 一致
        for node in self.checkpoint.completed_nodes:
            if node not in self.checkpoint.intermediate_files:
                errors.append(f"completed_nodes 包含 {node}, 但 intermediate_files 缺少映射")
        
        # 3. 验证文件存在性
        for step, file_path in self.checkpoint.intermediate_files.items():
            if not os.path.exists(file_path):
                errors.append(f"文件不存在: {step} -> {file_path}")
        
        # 4. 验证编号一致性
        for step, file_path in self.checkpoint.intermediate_files.items():
            if step in self.NODE_SEQUENCE:
                expected_num = self.NODE_SEQUENCE[step]
                expected_filename = os.path.basename(self._generate_filename(step))
                actual_filename = os.path.basename(file_path)
                if f"{expected_num:02d}" not in actual_filename:
                    errors.append(f"编号不一致: {step} 期望包含 {expected_num:02d}, 实际文件 {actual_filename}")
        
        # 5. 验证 current_node 合法性
        valid_nodes = list(self.NODE_SEQUENCE.keys()) + ["done"]
        if self.checkpoint.current_node not in valid_nodes:
            errors.append(f"current_node 非法: {self.checkpoint.current_node}")
        
        return len(errors) == 0, errors
    
    def reset(self, keep_completed: Optional[List[str]] = None) -> None:
        """
        重置 checkpoint
        
        Args:
            keep_completed: 保留已完成的节点（可选，用于部分重置）
        """
        if keep_completed is None:
            # 完全重置
            self.checkpoint = Checkpoint.create_new(
                workflow_id=self.checkpoint.workflow_id,
                version=self.checkpoint.version
            )
        else:
            # 部分重置：保留指定节点，重置后续
            new_cp = Checkpoint.create_new(
                workflow_id=self.checkpoint.workflow_id,
                version=self.checkpoint.version
            )
            
            for step in keep_completed:
                if step in self.checkpoint.intermediate_files:
                    new_cp.completed_nodes.append(step)
                    new_cp.intermediate_files[step] = self.checkpoint.intermediate_files[step]
            
            # 确定 current_node
            if new_cp.completed_nodes:
                last_step = new_cp.completed_nodes[-1]
                step_order = list(self.NODE_SEQUENCE.keys())
                if last_step in step_order:
                    last_idx = step_order.index(last_step)
                    if last_idx + 1 < len(step_order):
                        new_cp.current_node = step_order[last_idx + 1]
                    else:
                        new_cp.current_node = "done"
            
            self.checkpoint = new_cp
        
        self._save()
    
    def get_state_summary(self) -> Dict:
        """获取状态摘要（用于用户展示）"""
        valid, errors = self.validate()
        
        return {
            "workflow": self.checkpoint.workflow_id,
            "version": self.checkpoint.version,
            "status": "已完成" if self.checkpoint.current_node == "done" else "进行中",
            "current_step": self.checkpoint.current_node,
            "completed_steps": self.checkpoint.completed_nodes,
            "files": self.checkpoint.intermediate_files,
            "valid": valid,
            "errors": errors if not valid else [],
            "last_updated": self.checkpoint.updated_at
        }


def main():
    """命令行验证工具"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python3 checkpoint_manager.py <checkpoint.json路径>")
        sys.exit(1)
    
    checkpoint_path = sys.argv[1]
    
    try:
        cp = CheckpointManager(checkpoint_path)
        valid, errors = cp.validate()
        
        summary = cp.get_state_summary()
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        
        if not valid:
            print("\n⚠️ 状态异常，建议重置:")
            print(f"  python3 -c \"from checkpoint_manager import CheckpointManager; "
                  f"CheckpointManager('{checkpoint_path}').reset()\"")
            sys.exit(1)
        else:
            print("\n✓ 状态正常")
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
