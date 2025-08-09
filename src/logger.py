from loguru import logger
from pathlib import Path
import sys
from queue import SimpleQueue
from typing import Optional

# 控制台与文件均使用 UTF-8 编码并中文输出
Path("logs").mkdir(parents=True, exist_ok=True)
logger.remove()  # 移除默认 sink
logger.add(sys.stdout, colorize=True, enqueue=True, backtrace=False, diagnose=False)
logger.add("logs/app.log", rotation="5 MB", retention=5, enqueue=True, encoding="utf-8")

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

