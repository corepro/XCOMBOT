from __future__ import annotations
import random
from pathlib import Path
from typing import List, Optional
from .config import CONFIG
from .ai import gen_comment_by_ai
from .logger import logger


def load_local_comments() -> List[str]:
    path = Path(CONFIG.comment.local_library_path)
    if not path.exists():
        return [
            "赞同你的观点！",
            "很有启发，谢谢分享～",
            "这条信息很重要，转存一下",
            "观点独到，学习了",
        ]
    lines = [l.strip() for l in path.read_text(encoding="utf-8").splitlines()]
    return [l for l in lines if l]


def load_comments(file_path: str = None) -> List[str]:
    """加载评论文件，用于向后兼容"""
    if file_path is None:
        return load_local_comments()

    try:
        path = Path(file_path)
        if not path.exists():
            logger.warning("评论文件不存在: {}", file_path)
            return []

        lines = [l.strip() for l in path.read_text(encoding="utf-8").splitlines()]
        return [l for l in lines if l]
    except Exception as e:
        logger.error("加载评论文件失败: {}", str(e))
        return []


def get_random_comment() -> str:
    """获取随机评论，用于向后兼容"""
    return random_comment()


def random_comment(context_text: Optional[str] = None) -> str:
    mode = (CONFIG.comment.mode or "local").lower()
    if mode == "ai" and context_text:
        # 用 AI 生成
        text = gen_comment_by_ai(context_text)
        logger.info("AI 生成评论：{}", text)
        return text
    # 否则回到本地随机
    comments = load_local_comments()
    return random.choice(comments) if comments else "不错！"

