#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI视频创作师 - Scripts包
提供完整的视频创作脚本工具集
"""

from scripts.inspiration_generator import InspirationGenerator, StoryDirection
from scripts.script_generator import ScriptGenerator, Character, VideoScript, Shot, SoundDesign
from scripts.script_diagnosis import ScriptDiagnosis, DiagnosisReport
from scripts.viral_formula import ViralFormulaLibrary, FormulaTemplate
from scripts.multi_platform_adapter import MultiPlatformAdapter, AdaptationResult

__all__ = [
    # 灵感裂变
    "InspirationGenerator",
    "StoryDirection",
    
    # 剧本生成
    "ScriptGenerator",
    "Character",
    "VideoScript",
    "Shot",
    "SoundDesign",
    
    # 剧本诊断
    "ScriptDiagnosis",
    "DiagnosisReport",
    
    # 爆款公式
    "ViralFormulaLibrary",
    "FormulaTemplate",
    
    # 多平台适配
    "MultiPlatformAdapter",
    "AdaptationResult",
]

__version__ = "1.0.0"
