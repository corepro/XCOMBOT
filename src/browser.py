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
        browser_type = getattr(CONFIG, "browser_type", "chrome")
        logger.info("启动 Playwright {} 浏览器... 无头模式={} 慢动作={}ms 代理={}",
                   browser_type.upper(), CONFIG.headless, CONFIG.slow_mo_ms, CONFIG.proxy)

        try:
            self._playwright = sync_playwright().start()
            launch_args = {
                "headless": CONFIG.headless,
                "slow_mo": CONFIG.slow_mo_ms,
            }
            if CONFIG.proxy:
                launch_args["proxy"] = {"server": CONFIG.proxy}

            # 根据配置选择浏览器类型
            if browser_type == "firefox":
                self.browser = self._playwright.firefox.launch(**launch_args)
                logger.debug("Firefox浏览器启动成功")
            else:  # 默认使用Chrome
                self.browser = self._playwright.chromium.launch(**launch_args)
                logger.debug("Chrome浏览器启动成功")

        except Exception as e:
            logger.error("浏览器启动失败: {}", str(e))
            # 清理资源
            if self._playwright:
                try:
                    self._playwright.stop()
                except:
                    pass
                self._playwright = None
            raise Exception(f"浏览器启动失败: {e}") from e

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

        # 按顺序关闭资源，确保每个步骤都有独立的异常处理
        context_closed = False
        browser_closed = False
        playwright_stopped = False

        # 1. 关闭页面和上下文
        try:
            if self.page:
                self.page.close()
                self.page = None
                logger.debug("页面已关闭")
        except Exception as e:
            logger.warning("关闭页面失败: {}", str(e))

        try:
            if self.context:
                self.context.close()
                self.context = None
                context_closed = True
                logger.debug("上下文已关闭")
        except Exception as e:
            logger.warning("关闭上下文失败: {}", str(e))

        # 2. 关闭浏览器
        try:
            if self.browser:
                self.browser.close()
                self.browser = None
                browser_closed = True
                logger.debug("浏览器已关闭")
        except Exception as e:
            logger.warning("关闭浏览器失败: {}", str(e))

        # 3. 停止Playwright
        try:
            if self._playwright:
                self._playwright.stop()
                self._playwright = None
                playwright_stopped = True
                logger.debug("Playwright已停止")
        except Exception as e:
            logger.warning("停止Playwright失败: {}", str(e))

        # 记录最终状态
        if context_closed and browser_closed and playwright_stopped:
            logger.info("浏览器资源已完全释放")
        else:
            logger.warning("部分浏览器资源可能未完全释放 - 上下文:{} 浏览器:{} Playwright:{}",
                         context_closed, browser_closed, playwright_stopped)

