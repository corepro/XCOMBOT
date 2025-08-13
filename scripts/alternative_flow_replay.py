from playwright.sync_api import sync_playwright
import time


def replay():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://weibo.com")
        page.wait_for_load_state('domcontentloaded')
        page.goto("https://weibo.com/1921178767/PF31xDnWe")
        page.wait_for_load_state('domcontentloaded')
        try:
            page.locator('page.locator("a:has-text(\'关注\')").first').first.click()
        except Exception:
            pass
        try:
            page.mouse.click(187.0, 143.0)
        except Exception:
            pass
        try:
            page.locator('page.locator("button:has-text(\'赞\')").first').first.click()
        except Exception:
            pass
        try:
            page.mouse.click(808.8250122070312, 2445.5)
        except Exception:
            pass
        input('Replay done. Press Enter to close...')
        browser.close()


if __name__ == '__main__':
    replay()