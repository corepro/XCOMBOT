"""
反爬虫检测模块
提供多级别的反爬虫检测规避功能
"""

from .config import AntiDetectionConfig, AntiDetectionMode
from .basic import BasicAntiDetection
from .enhanced import EnhancedAntiDetection
from .extreme import ExtremeAntiDetection

__all__ = [
    'AntiDetectionConfig',
    'AntiDetectionMode', 
    'BasicAntiDetection',
    'EnhancedAntiDetection',
    'ExtremeAntiDetection',
    'get_anti_detection_handler'
]


def get_anti_detection_handler(mode: AntiDetectionMode):
    """根据模式获取对应的反爬虫处理器"""
    if mode == AntiDetectionMode.BASIC:
        return BasicAntiDetection()
    elif mode == AntiDetectionMode.ENHANCED:
        return EnhancedAntiDetection()
    elif mode == AntiDetectionMode.EXTREME:
        return ExtremeAntiDetection()
    else:
        return None  # 关闭模式
