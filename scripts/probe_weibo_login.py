from __future__ import annotations
from pathlib import Path
import argparse
from src.browser import BrowserManager
from src.login_weibo import get_logged_in_username, _has_login_prompt, WEIBO_LOGIN_URL
from src.logger import logger


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--use-storage", action="store_true", help="Load saved storage_state.json")
    ap.add_argument("--login-page", action="store_true", help="Open official login page first")
    ap.add_argument("--screenshot", default="screenshots/weibo_probe.png")
    args = ap.parse_args()

    bm = BrowserManager()
    from src.config import CONFIG
    CONFIG.headless = True
    bm.launch()
    bm.new_context(use_storage=args.use_storage)

    page = bm.page
    assert page is not None

    if args.login_page:
        logger.info("Go to official login page: {}", WEIBO_LOGIN_URL)
        page.goto(WEIBO_LOGIN_URL)
    else:
        logger.info("Go to weibo.com home")
        page.goto("https://weibo.com")

    page.wait_for_load_state("domcontentloaded")

    uname = get_logged_in_username(page)
    prompt = _has_login_prompt(page)
    url = page.url
    logger.info("Probe result: url={} has_login_prompt={} username={}", url, prompt, uname)

    # screenshot
    p = Path(args.screenshot)
    p.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(p))
    print("PROBE:", {
        "url": url,
        "has_login_prompt": bool(prompt),
        "username": uname,
        "screenshot": str(p),
    })

    bm.close()


if __name__ == "__main__":
    main()

