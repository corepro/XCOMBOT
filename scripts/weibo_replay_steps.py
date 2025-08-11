from playwright.sync_api import sync_playwright
import re, time


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        # [t+949ms] 导航
        page.goto('https://weibo.com')
        page.wait_for_load_state('domcontentloaded')
        # [t+8963ms] 点击 card.locator("button[title*='赞']").first
        try:
            page.locator('card.locator("button[title*=\'赞\']").first').first.click()
        except Exception:
            pass
        # 兜底坐标点击 (834.8249816894531, 566.566650390625)
        try:
            page.mouse.click(834.8249816894531, 566.566650390625)
        except Exception:
            pass
        input('MCP run done. Press Enter to close...')
        browser.close()


if __name__ == '__main__':
    run()