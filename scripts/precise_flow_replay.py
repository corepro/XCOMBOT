from playwright.sync_api import sync_playwright
import time


def replay():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://weibo.com")
        page.wait_for_load_state('domcontentloaded')
        page.goto("https://weibo.com/5894431188/PFcA5hWuA")
        page.wait_for_load_state('domcontentloaded')
        input('Replay done. Press Enter to close...')
        browser.close()


if __name__ == '__main__':
    replay()