from __future__ import annotations
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from typing import Optional
from pathlib import Path
from .config import CONFIG
from .logger import logger
from .anti_detection.integration import setup_anti_detection_for_browser_manager, check_browser_restart_needed


class BrowserManager:
    def __init__(self):
        self._playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def launch(self):
        logger.info("启动 Playwright 浏览器... 无头模式={} 慢动作={}ms 代理={}", CONFIG.headless, CONFIG.slow_mo_ms, CONFIG.proxy)
        self._playwright = sync_playwright().start()
        launch_args = {
            "headless": CONFIG.headless,
            "slow_mo": CONFIG.slow_mo_ms,
        }
        if CONFIG.proxy:
            launch_args["proxy"] = {"server": CONFIG.proxy}
        self.browser = self._playwright.chromium.launch(**launch_args)

    def new_context(self, use_storage: bool = True):
        assert self.browser, "浏览器未启动"
        context_args = {"viewport": {"width": 1280, "height": 900}}
        storage_path = Path(CONFIG.storage_state_path)
        if use_storage and storage_path.exists():
            logger.info("从 {} 加载存储状态", storage_path)
            context_args["storage_state"] = str(storage_path)
        self.context = self.browser.new_context(**context_args)
        self.page = self.context.new_page()
        self.page.set_default_timeout(30000)
        self.page.set_default_navigation_timeout(45000)

        # 设置反爬虫保护
        setup_anti_detection_for_browser_manager(self)

        return self.page

    def save_storage(self):
        assert self.context, "上下文未创建"
        storage_path = Path(CONFIG.storage_state_path)
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("保存存储状态到 {}", storage_path)
        self.context.storage_state(path=str(storage_path))

    def should_restart_browser(self) -> bool:
        """检查是否需要重启浏览器"""
        return check_browser_restart_needed()

    def restart_if_needed(self) -> bool:
        """如果需要则重启浏览器"""
        if self.should_restart_browser():
            logger.info("反爬虫: 需要重启浏览器")
            self.close()
            self.launch()
            self.new_context(use_storage=True)
            return True
        return False

    def close(self):
        logger.info("关闭浏览器...")
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
        finally:
            if self._playwright:
                self._playwright.stop()

