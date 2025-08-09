"""
基础反爬虫措施
包括随机延时、用户代理轮换、鼠标轨迹模拟、滚动行为等
"""

import random
import time
import asyncio
from typing import Optional, List
from playwright.sync_api import Page, BrowserContext
from ..logger import logger
from .config import DEFAULT_USER_AGENTS, COMMON_VIEWPORTS


class BasicAntiDetection:
    """基础反爬虫检测规避"""
    
    def __init__(self):
        self.user_agents = DEFAULT_USER_AGENTS.copy()
        self.current_user_agent = None
        self.operation_count = 0
        
    def setup_browser_context(self, context: BrowserContext) -> None:
        """设置浏览器上下文的反爬虫措施"""
        try:
            # 随机选择用户代理
            self.current_user_agent = random.choice(self.user_agents)
            
            # 设置用户代理
            context.set_extra_http_headers({
                "User-Agent": self.current_user_agent
            })
            
            logger.info("基础反爬虫: 已设置用户代理: {}", self.current_user_agent[:50] + "...")
            
        except Exception as e:
            logger.warning("基础反爬虫: 设置浏览器上下文失败: {}", str(e))
    
    def setup_page(self, page: Page) -> None:
        """设置页面级别的反爬虫措施"""
        try:
            # 随机化视口大小
            viewport = random.choice(COMMON_VIEWPORTS)
            page.set_viewport_size(viewport)
            
            logger.info("基础反爬虫: 已设置视口大小: {}x{}", viewport["width"], viewport["height"])
            
            # 注入反检测脚本
            self._inject_anti_detection_scripts(page)
            
        except Exception as e:
            logger.warning("基础反爬虫: 设置页面失败: {}", str(e))
    
    def _inject_anti_detection_scripts(self, page: Page) -> None:
        """注入反检测脚本"""
        try:
            # 基础的反检测脚本
            anti_detection_script = """
            // 覆盖webdriver属性
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });

            // 删除webdriver属性
            delete navigator.webdriver;

            // 覆盖plugins长度
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
                configurable: true
            });

            // 覆盖languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en'],
                configurable: true
            });

            // 移除自动化相关属性
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;

            // 覆盖chrome runtime
            if (window.chrome && window.chrome.runtime) {
                delete window.chrome.runtime.onConnect;
                delete window.chrome.runtime.onMessage;
            }

            console.log('基础反检测脚本已加载, webdriver:', navigator.webdriver);
            """
            
            page.add_init_script(anti_detection_script)
            logger.debug("基础反爬虫: 已注入反检测脚本")
            
        except Exception as e:
            logger.warning("基础反爬虫: 注入反检测脚本失败: {}", str(e))
    
    def random_delay(self, min_seconds: float = 0.5, max_seconds: float = 2.0) -> None:
        """随机延时"""
        delay = random.uniform(min_seconds, max_seconds)
        logger.debug("基础反爬虫: 随机延时 {:.2f} 秒", delay)
        time.sleep(delay)
    
    def simulate_human_mouse_movement(self, page: Page) -> None:
        """模拟人类鼠标移动"""
        try:
            # 随机移动鼠标到不同位置
            for _ in range(random.randint(2, 4)):
                x = random.randint(100, 1200)
                y = random.randint(100, 800)
                steps = random.randint(10, 30)
                
                page.mouse.move(x, y, steps=steps)
                time.sleep(random.uniform(0.1, 0.3))
                
            logger.debug("基础反爬虫: 完成鼠标轨迹模拟")
            
        except Exception as e:
            logger.warning("基础反爬虫: 鼠标轨迹模拟失败: {}", str(e))
    
    def simulate_human_scrolling(self, page: Page) -> None:
        """模拟人类滚动行为"""
        try:
            # 随机滚动
            scroll_count = random.randint(1, 3)
            for _ in range(scroll_count):
                delta_y = random.randint(200, 800)
                page.mouse.wheel(0, delta_y)
                time.sleep(random.uniform(0.3, 0.8))
                
            logger.debug("基础反爬虫: 完成滚动行为模拟")
            
        except Exception as e:
            logger.warning("基础反爬虫: 滚动行为模拟失败: {}", str(e))
    
    def simulate_reading_behavior(self, page: Page) -> None:
        """模拟阅读行为"""
        try:
            # 模拟停留阅读
            reading_time = random.uniform(2.0, 5.0)
            logger.debug("基础反爬虫: 模拟阅读停留 {:.2f} 秒", reading_time)
            time.sleep(reading_time)
            
            # 随机概率进行滚动
            if random.random() < 0.3:
                self.simulate_human_scrolling(page)
                
            # 随机概率进行鼠标移动
            if random.random() < 0.2:
                self.simulate_human_mouse_movement(page)
                
        except Exception as e:
            logger.warning("基础反爬虫: 阅读行为模拟失败: {}", str(e))
    
    def before_action(self, page: Page, action_name: str) -> None:
        """在执行操作前的反爬虫措施"""
        try:
            logger.debug("基础反爬虫: 准备执行操作: {}", action_name)
            
            # 操作前随机延时
            self.random_delay(0.8, 2.5)
            
            # 随机概率进行人类行为模拟
            if random.random() < 0.3:
                self.simulate_human_mouse_movement(page)
            
            self.operation_count += 1
            
        except Exception as e:
            logger.warning("基础反爬虫: 操作前处理失败: {}", str(e))
    
    def after_action(self, page: Page, action_name: str, success: bool) -> None:
        """在执行操作后的反爬虫措施"""
        try:
            logger.debug("基础反爬虫: 操作完成: {} (成功: {})", action_name, success)
            
            # 操作后随机延时
            self.random_delay(0.5, 1.5)
            
            # 随机概率进行阅读行为模拟
            if random.random() < 0.4:
                self.simulate_reading_behavior(page)
                
        except Exception as e:
            logger.warning("基础反爬虫: 操作后处理失败: {}", str(e))
    
    def before_navigation(self, page: Page, url: str) -> None:
        """在页面导航前的反爬虫措施"""
        try:
            logger.debug("基础反爬虫: 准备导航到: {}", url)
            
            # 导航前延时
            self.random_delay(1.0, 2.0)
            
        except Exception as e:
            logger.warning("基础反爬虫: 导航前处理失败: {}", str(e))
    
    def after_navigation(self, page: Page, url: str) -> None:
        """在页面导航后的反爬虫措施"""
        try:
            logger.debug("基础反爬虫: 导航完成: {}", url)
            
            # 等待页面稳定
            time.sleep(random.uniform(1.0, 2.0))
            
            # 模拟页面加载后的人类行为
            self.simulate_reading_behavior(page)
            
        except Exception as e:
            logger.warning("基础反爬虫: 导航后处理失败: {}", str(e))
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "mode": "basic",
            "enabled": True,
            "operation_count": self.operation_count,
            "current_user_agent": self.current_user_agent[:50] + "..." if self.current_user_agent else None
        }
