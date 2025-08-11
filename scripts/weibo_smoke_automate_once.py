from __future__ import annotations
import argparse, json, time, sys
from pathlib import Path
from src.browser import BrowserManager
from src.logger import logger
from src.config import CONFIG
from src.weibo import automate_on_post, WEIBO_HOME
from src.login_weibo import is_logged_in_weibo, login_flow_weibo


def main(argv=None):
    ap = argparse.ArgumentParser(description="Weibo smoke automate once")
    ap.add_argument("--like", action="store_true", help="执行点赞")
    ap.add_argument("--comment", action="store_true", help="执行评论")
    ap.add_argument("--repost", action="store_true", help="执行转发（会先输入评论）")
    ap.add_argument("--headless", action="store_true", help="无头运行")
    ap.add_argument("--save-replay", default="scripts/weibo_replay.py", help="保存MCP回放脚本路径")
    args = ap.parse_args(argv)

    # 平台及可视化
    CONFIG.platform = "weibo"
    CONFIG.headless = bool(args.headless)

    bm = BrowserManager()
    try:
        bm.launch()
        bm.new_context(use_storage=True)
        page = bm.page
        assert page is not None

        # 如果未登录，引导登录一次（人工扫码/输入），成功后保存会话
        page.goto(WEIBO_HOME)
        page.wait_for_load_state("domcontentloaded")
        if not is_logged_in_weibo(page):
            logger.info("未检测到登录状态，将打开官方登录页，请在页面内完成登录…")
            login_flow_weibo(bm, timeout_sec=300)
            page = bm.page
            assert page is not None

        # 执行一次自动化：默认只点赞，除非命令行启用
        do_like = bool(args.like) or (not args.comment and not args.repost)
        do_comment = bool(args.comment)
        do_repost = bool(args.repost)

        result = automate_on_post(page, do_comment=do_comment, do_like=do_like, do_repost=do_repost, do_follow=True)

        # 输出关键信息
        safe = dict(result)
        # 保存回放脚本（选项D）
        replay_path = Path(args.save_replay)
        try:
            replay_code = safe.get("mcp_script") or ""
            if replay_code:
                replay_path.parent.mkdir(parents=True, exist_ok=True)
                replay_path.write_text(replay_code, encoding="utf-8")
                logger.info("已保存回放脚本: {}", replay_path)
            # 另存 MCP 逐步代码
            mcp_code = safe.get("mcp_code") or ""
            if mcp_code:
                code_path = Path(str(replay_path).replace(".py", "_steps.py"))
                code_path.write_text(mcp_code, encoding="utf-8")
                logger.info("已保存MCP逐步代码: {}", code_path)
        except Exception as e:
            logger.warning("写入回放/代码失败: {}", e)
        # 截断输出
        for key in ["mcp_script", "mcp_code"]:
            val = safe.get(key) or ""
            if val and len(val) > 400:
                safe[key] = val[:400] + "...<truncated>"
        print("WEIBO_AUTOMATE_RESULT:", json.dumps(safe, ensure_ascii=False))

    finally:
        try:
            bm.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()

