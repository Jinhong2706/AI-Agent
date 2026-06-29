#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆管家 V3.0 - Thin Wrapper (兼容入口)
所有功能已迁移至 memory_manager/ 包，此文件仅为向后兼容入口。

使用方法:
    python memory_manager.py [command] [args]

新方式:
    python -m memory_manager [command] [args]
    或:
    from memory_manager import MemoryManager, main
    from memory_manager.cli import main; main()
"""

import sys

from memory_manager.cli import main

if __name__ == "__main__":
    sys.exit(main())
