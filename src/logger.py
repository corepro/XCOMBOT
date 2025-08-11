from loguru import logger
from pathlib import Path
import sys
import os
from queue import SimpleQueue
from typing import Optional

def setup_logger():
    """设置日志系统，兼容打包环境"""
    # 创建日志目录
    Path("logs").mkdir(parents=True, exist_ok=True)

    # 移除默认 sink
    logger.remove()

    # 检测是否在打包环境中
    is_frozen = getattr(sys, 'frozen', False)

    try:
        # 尝试添加控制台输出
        if sys.stdout is not None and not is_frozen:
            # 开发环境：正常的控制台输出
            logger.add(sys.stdout, colorize=True, enqueue=True, backtrace=False, diagnose=False)
        elif not is_frozen:
            # 开发环境但stdout有问题：使用stderr
            if sys.stderr is not None:
                logger.add(sys.stderr, colorize=True, enqueue=True, backtrace=False, diagnose=False)
        else:
            # 打包环境：不添加控制台输出，只使用文件日志
            pass
    except Exception as e:
        # 如果控制台输出失败，继续使用文件日志
        pass

    # 添加文件日志（这个在任何环境下都应该工作）
    try:
        logger.add("logs/app.log", rotation="5 MB", retention=5, enqueue=True, encoding="utf-8")
    except Exception as e:
        # 如果文件日志也失败，至少确保logger不会崩溃
        print(f"警告：无法创建日志文件: {e}")

# 初始化日志系统
setup_logger()

# GUI 日志桥接（可选）
_ui_queue: Optional[SimpleQueue] = None
_ui_sink_id: Optional[int] = None


def attach_ui_queue(q: SimpleQueue):
    global _ui_queue, _ui_sink_id
    _ui_queue = q

    # 先移除旧 sink
    if _ui_sink_id is not None:
        try:
            logger.remove(_ui_sink_id)
        except Exception:
            pass
        _ui_sink_id = None

    def _sink(message):
        try:
            txt = message.record.get("message", "")
            q.put(txt)
            # 简单识别统计日志
            if txt.startswith("统计："):
                q.put(f"[STAT]{txt}")
        except Exception:
            pass

    _ui_sink_id = logger.add(_sink, level="INFO")


__all__ = ["logger", "attach_ui_queue"]

