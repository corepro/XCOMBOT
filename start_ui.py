#!/usr/bin/env python3
"""
启动UI界面
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from src.ui_bootstrap import AppUIBoot

if __name__ == "__main__":
    print("启动UI界面...")
    ui = AppUIBoot()
    ui.run()
