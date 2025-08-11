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
    'get_anti_detection_handler',
    'is_anti_detection_enabled',
    'safe_call_handler'
]


def get_anti_detection_handler(mode: AntiDetectionMode):
    """根据模式获取对应的反爬虫处理器"""
    try:
        if mode == AntiDetectionMode.BASIC:
            return BasicAntiDetection()
        elif mode == AntiDetectionMode.ENHANCED:
            return EnhancedAntiDetection()
        elif mode == AntiDetectionMode.EXTREME:
            return ExtremeAntiDetection()
        else:
            return None  # 关闭模式
    except Exception as e:
        # 如果创建反爬虫处理器失败，记录错误并返回None
        print(f"创建反爬虫处理器失败: {e}")
        return None


def is_anti_detection_enabled(handler) -> bool:
    """检查反爬虫处理器是否有效"""
    return handler is not None


def safe_call_handler(handler, method_name: str, *args, **kwargs):
    """安全调用反爬虫处理器的方法"""
    if not is_anti_detection_enabled(handler):
        return None

    try:
        method = getattr(handler, method_name, None)
        if method and callable(method):
            return method(*args, **kwargs)
        else:
            print(f"反爬虫处理器缺少方法: {method_name}")
            return None
    except Exception as e:
        print(f"调用反爬虫方法 {method_name} 失败: {e}")
        return None
