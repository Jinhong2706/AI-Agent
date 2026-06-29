"""
ThinkingControllerProxy — 统一请求入口代理
============================================
提供统一的 LLM API 请求入口，所有发送路径走同一代码。
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ThinkingControllerProxy:
    """
    统一 LLM 请求入口代理。
    
    通过 Hermes 的 before_api_call hook 注入，
    确保 main loop / cron / gateway / auxiliary 所有路径
    都走统一的清洗逻辑。
    
    同时解决 #15700 — thinking=off 时必须显式传 disabled 参数，
    否则 DeepSeek 默认开启 thinking mode。
    """
    
    def __init__(self):
        self._thinking_enabled: Optional[bool] = None
    
    def configure(self, thinking: bool):
        self._thinking_enabled = thinking
    
    def build_thinking_params(self) -> Dict:
        """
        构造 thinking 参数。
        
        关键（#15700）：DeepSeek API 在未收到 thinking 参数时
        默认启用 thinking mode。所以 thinking=off 必须显式传入。
        
        正确:
            thinking=off → {"thinking": {"type": "disabled"}}
            thinking=on  → {} (让 DeepSeek 用自己的默认值)
            未配置      → {} (兼容旧版本)
        """
        if self._thinking_enabled is False:
            return {"thinking": {"type": "disabled"}}
        return {}


# 全局单例
proxy = ThinkingControllerProxy()
