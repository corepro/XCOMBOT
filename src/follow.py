from __future__ import annotations
from playwright.sync_api import Page, expect
from .logger import logger
from .selectors import HOME_LINK, FOLLOW_BUTTON_ROLE, FOLLOWING_BUTTON_ROLE

X_BASE = "https://x.com"


def goto_user(page: Page, username: str):
    url = f"{X_BASE}/{username}"
    logger.info("Opening user profile: {}", url)
    page.goto(url)
    page.wait_for_selector(HOME_LINK)


def ensure_following(page: Page) -> bool:
    # Try to click Follow if present
    try:
        btn = page.get_by_role(*FOLLOW_BUTTON_ROLE)
        if btn.is_visible():
            logger.info("Clicking Follow button...")
            btn.click()
            # Wait until becomes Following
            page.get_by_role(*FOLLOWING_BUTTON_ROLE).wait_for(timeout=10000)
            logger.info("Now following.")
            return True
    except Exception:
        pass

    # Already following?
    try:
        if page.get_by_role(*FOLLOWING_BUTTON_ROLE).is_visible():
            logger.info("Already following.")
            return True
    except Exception:
        pass

    logger.warning("Follow/Following button not found.")
    return False

