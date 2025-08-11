from playwright.sync_api import sync_playwright
import time


def replay():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://weibo.com")
        page.wait_for_load_state('domcontentloaded')
        try:
            page.locator('card.locator("button[title*=\'赞\']").first').first.click()
        except Exception:
            pass
        try:
            page.mouse.click(834.8249816894531, 566.566650390625)
        except Exception:
            pass
        input('Replay done. Press Enter to close...')
        browser.close()


if __name__ == '__main__':
    replay()