from __future__ import annotations
from playwright.sync_api import Page, expect
from .logger import logger
from .browser import BrowserManager

X_BASE = "https://x.com"  # formerly twitter.com
LOGIN_URL = f"{X_BASE}/login"


def is_logged_in(page: Page) -> bool:
    try:
        # Heuristic: presence of sidebar/home button or avatar
        page.wait_for_selector('[data-testid="AppTabBar_Home_Link"], [data-testid="SideNav_AccountSwitcher_Button"]', timeout=25000)
        return True
    except Exception:
        return False


def login_flow(bm: BrowserManager):
    page = bm.page
    assert page is not None
    logger.info("打开 X.COM 登录页面: {}", LOGIN_URL)
    page.goto(LOGIN_URL)

    # If redirected to home due to prior storage_state
    if is_logged_in(page):
        logger.info("已检测到登录状态（通过UI检测）。")
        bm.save_storage()
        return

    logger.info("等待用户完成登录（手动/扫码）。")
    # Wait for login form or QR
    # The login may require username then password, or 2FA, or QR flow.
    # We just wait until the Home link appears.
    page.wait_for_selector('[data-testid="AppTabBar_Home_Link"]', timeout=300000)  # up to 5 minutes
    logger.info("检测到登录成功。正在保存登录状态...")
    bm.save_storage()


def open_home(bm: BrowserManager):
    page = bm.page
    assert page is not None
    page.goto(X_BASE)
    if not is_logged_in(page):
        logger.warning("导航到首页后未检测到登录状态。")
    else:
        logger.info("已以登录用户身份打开首页。")

