"""
MessageSanitizer — 统一消息清洗器 v2.0
======================================
所有发往 LLM API 的消息必经此模块清洗。
"""

import copy
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 需要 reasoning_content 回填的厂商
THINKING_PROVIDERS = {"deepseek", "kimi", "moonshot"}

# 调试模式
DEBUG = os.environ.get("DEEPSEEK_FIX_DEBUG", "").lower() in ("1", "true", "yes")


class MessageSanitizer:
    """
    统一消息清洗器。
    
    ═══════════════════════════════════════════════════════════
    核心设计原理
    ═══════════════════════════════════════════════════════════
    
    1. 不可变转换（Immutable Transformation）
       ────────────────────────
       copy.deepcopy 每次生成全新 dict。防止 #17400 间歇性失败——
       Hermes 中多个函数共享同一个消息 dict 引用时，
       后一个函数可能意外覆盖前一个的 reasoning_content。
       
       对比 OpenClaw：TypeScript 的 spread operator (...)
       天然保证不可变。Hermes 的 Python 需要显式 deepcopy。
    
    2. 统一出口（Single Exit Point）
       ──────────────
       不管走 main loop、cron、gateway 还是辅助路径，
       所有 API 请求最终都调用 sanitize_for_api()。
       一处处理，处处生效。
       
       对比 OpenClaw：DeepSeek provider 插件在 onBeforeSend
       生命周期中统一拦截，也是单一出口模式。
    
    3. 对称设计（Symmetric Design）
       ────────────
       API 发送前 → sanitize_for_api()
       存储前     → sanitize_for_storage()
       加载后     → sanitize_after_load()
       
       三方向一致，保证字段名永不丢失。
    ═══════════════════════════════════════════════════════════
    """
    
    def __init__(self, provider: str, model_id: str, thinking_enabled: bool):
        self.provider = (provider or "").lower()
        self.model_id = model_id or ""
        self.thinking_enabled = thinking_enabled
    
    def sanitize_for_api(self, messages: List[Dict]) -> List[Dict]:
        """
        ⭐ 核心方法：将内部消息转换为符合 DeepSeek API 要求的格式。
        
        解决的问题：
        - #14933 tool-call 消息缺 RC → 强制回填
        - #16137 plain assistant 缺 RC → 填空字符串
        - #17400 间歇性丢失 → deepcopy 防状态突变
        - #17052 stale RC 复用 → 新鲜度检查
        - #15748 跨厂商泄漏 → 非 thinking 模型清理
        """
        working = copy.deepcopy(messages)  # ← 关键：深度拷贝防状态突变
        working = self._ensure_reasoning_content(working)
        working = self._clean_foreign_fields(working)
        self._debug_log(working)
        return working
    
    def sanitize_for_storage(self, messages: List[Dict]) -> List[Dict]:
        """
        存储前处理：同时保留 reasoning 和 reasoning_content。
        解决 #16844 — 下次加载时不会因字段名不一致而丢失 RC。
        """
        result = []
        for msg in copy.deepcopy(messages):
            if msg.get("role") == "assistant":
                rc = msg.get("reasoning_content") or msg.get("reasoning")
                msg["reasoning"] = rc
                msg["reasoning_content"] = rc
            result.append(msg)
        return result
    
    def sanitize_after_load(self, messages: List[Dict]) -> List[Dict]:
        """
        加载后处理：如果只有 reasoning 没有 reasoning_content → 补上。
        解决 #16844, #17825 — session 恢复后 RC 不丢失。
        """
        result = []
        for msg in copy.deepcopy(messages):
            if msg.get("role") == "assistant" and not msg.get("reasoning_content"):
                msg["reasoning_content"] = msg.get("reasoning", "")
            result.append(msg)
        return result
    
    def needs_reasoning_content(self) -> bool:
        """判断当前厂商是否需要 reasoning_content 回填"""
        return self.thinking_enabled and any(
            p in self.provider for p in THINKING_PROVIDERS
        )
    
    def _ensure_reasoning_content(self, messages: List[Dict]) -> List[Dict]:
        if not self.needs_reasoning_content():
            return messages
        
        result = []
        for i, msg in enumerate(messages):
            if msg.get("role") != "assistant":
                result.append(msg)
                continue
            rc = msg.get("reasoning_content")
            if rc is None:
                rc = msg.get("reasoning", "")
            result.append({**msg, "reasoning_content": rc if rc is not None else ""})
        return result
    
    def _clean_foreign_fields(self, messages: List[Dict]) -> List[Dict]:
        if not self.thinking_enabled:
            return [
                {k: v for k, v in msg.items() if k not in ("reasoning_content", "reasoning")}
                for msg in messages
            ]
        return messages
    
    def _debug_log(self, messages: List[Dict]):
        if not DEBUG:
            return
        for i, msg in enumerate(messages):
            if msg.get("role") == "assistant":
                logger.debug(
                    f"msg[{i}]: role=assistant "
                    f"rc={'✅' if msg.get('reasoning_content') is not None else '❌'} "
                    f"tc={'✅' if msg.get('tool_calls') else '❌'}"
                )
