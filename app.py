from __future__ import annotations
import argparse
from src.browser import BrowserManager
from src.login import login_flow, open_home
from src.config import CONFIG
from src.logger import logger
from src.run_tasks import run_follow_once, run_monitor_loop, like_once, retweet_once, comment_once



def cli_login():
    bm = BrowserManager()
    try:
        bm.launch()
        bm.new_context(use_storage=True)
        login_flow(bm)
        logger.info("Login flow completed.")
    finally:
        bm.close()


def cli_open():
    bm = BrowserManager()
    try:
        bm.launch()
        bm.new_context(use_storage=True)
        open_home(bm)
        logger.info("Open home completed.")
    finally:
        bm.close()


def main():
    parser = argparse.ArgumentParser(description="XComBot - Playwright automation for X.COM")
    parser.add_argument("--login", action="store_true", help="Open login page and wait for manual login, then save cookies")
    parser.add_argument("--open", action="store_true", help="Open home using stored cookies")
    parser.add_argument("--follow-once", action="store_true", help="Visit each configured user and follow if not already")
    parser.add_argument("--comment-once", action="store_true", help="Comment on a visible tweet once")
    parser.add_argument("--like-once", action="store_true", help="Like a visible tweet once")
    parser.add_argument("--retweet-once", action="store_true", help="Retweet a visible tweet once")
    parser.add_argument("--monitor", action="store_true", help="Start monitoring loop to retweet and comment on new posts")
    parser.add_argument("--gui", action="store_true", help="Run GUI")
    parser.add_argument("--platform", choices=["twitter", "weibo"], help="Override platform for this run")

    args = parser.parse_args()

    # 可选：临时覆盖平台
    if getattr(args, "platform", None):
        from src.config import CONFIG as _CFG
        _CFG.platform = args.platform

    if args.login:
        cli_login(); return
    if args.open:
        cli_open(); return
    if args.follow_once:
        run_follow_once(); return
    if args.comment_once:
        comment_once(); return
    if args.like_once:
        like_once(); return
    if args.retweet_once:
        retweet_once(); return
    if args.monitor:
        run_monitor_loop(); return
    if args.gui:
        from src.ui_bootstrap import AppUIBoot
        AppUIBoot().run(); return

    # 默认启动现代化 ttkbootstrap 界面
    from src.ui_bootstrap import AppUIBoot
    AppUIBoot().run()


if __name__ == "__main__":
    main()

