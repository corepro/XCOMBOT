"""
反爬虫集成模块
将反爬虫措施集成到所有操作中
"""

import functools
from typing import Optional, Callable, Any
from playwright.sync_api import Page, BrowserContext
from ..config import CONFIG
from ..logger import logger
from . import get_anti_detection_handler, AntiDetectionMode


class AntiDetectionIntegration:
    """反爬虫集成管理器"""
    
    def __init__(self):
        self.handler = None
        self.enabled = False
        self.mode = AntiDetectionMode.OFF
        self._update_handler()
    
    def _update_handler(self) -> None:
        """更新反爬虫处理器"""
        try:
            # 从配置获取模式
            mode_str = getattr(CONFIG, 'anti_detection_mode', 'off')
            self.enabled = getattr(CONFIG, 'anti_detection_enabled', False)
            
            # 转换模式
            mode_mapping = {
                'off': AntiDetectionMode.OFF,
                'basic': AntiDetectionMode.BASIC,
                'enhanced': AntiDetectionMode.ENHANCED,
                'extreme': AntiDetectionMode.EXTREME
            }
            
            self.mode = mode_mapping.get(mode_str, AntiDetectionMode.OFF)
            
            # 获取处理器
            if self.enabled and self.mode != AntiDetectionMode.OFF:
                self.handler = get_anti_detection_handler(self.mode)
                logger.info("反爬虫集成: 启用 {} 模式", self.mode.value.upper())
            else:
                self.handler = None
                logger.info("反爬虫集成: 已关闭")
                
        except Exception as e:
            logger.warning("反爬虫集成: 更新处理器失败: {}", str(e))
            self.handler = None
            self.enabled = False
    
    def setup_browser_context(self, context: BrowserContext) -> None:
        """设置浏览器上下文"""
        if self.handler:
            try:
                self.handler.setup_browser_context(context)
            except Exception as e:
                logger.warning("反爬虫集成: 设置浏览器上下文失败: {}", str(e))
    
    def setup_page(self, page: Page) -> None:
        """设置页面"""
        if self.handler:
            try:
                self.handler.setup_page(page)
            except Exception as e:
                logger.warning("反爬虫集成: 设置页面失败: {}", str(e))
    
    def before_action(self, page: Page, action_name: str) -> None:
        """操作前处理"""
        if self.handler:
            try:
                self.handler.before_action(page, action_name)
            except Exception as e:
                logger.warning("反爬虫集成: 操作前处理失败: {}", str(e))
    
    def after_action(self, page: Page, action_name: str, success: bool) -> None:
        """操作后处理"""
        if self.handler:
            try:
                self.handler.after_action(page, action_name, success)
            except Exception as e:
                logger.warning("反爬虫集成: 操作后处理失败: {}", str(e))
    
    def before_navigation(self, page: Page, url: str) -> None:
        """导航前处理"""
        if self.handler:
            try:
                self.handler.before_navigation(page, url)
            except Exception as e:
                logger.warning("反爬虫集成: 导航前处理失败: {}", str(e))
    
    def after_navigation(self, page: Page, url: str) -> None:
        """导航后处理"""
        if self.handler:
            try:
                self.handler.after_navigation(page, url)
            except Exception as e:
                logger.warning("反爬虫集成: 导航后处理失败: {}", str(e))
    
    def should_restart_browser(self) -> bool:
        """判断是否应该重启浏览器"""
        if self.handler and hasattr(self.handler, 'should_restart_browser'):
            try:
                return self.handler.should_restart_browser()
            except Exception as e:
                logger.warning("反爬虫集成: 检查重启条件失败: {}", str(e))
        return False
    
    def reset_session(self) -> None:
        """重置会话"""
        if self.handler and hasattr(self.handler, 'reset_session'):
            try:
                self.handler.reset_session()
            except Exception as e:
                logger.warning("反爬虫集成: 重置会话失败: {}", str(e))
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        if self.handler:
            try:
                return self.handler.get_stats()
            except Exception as e:
                logger.warning("反爬虫集成: 获取统计信息失败: {}", str(e))
        
        return {
            "mode": "off",
            "enabled": False
        }
    
    def refresh_config(self) -> None:
        """刷新配置"""
        self._update_handler()


# 全局反爬虫集成实例
anti_detection = AntiDetectionIntegration()


def with_anti_detection(action_name: str):
    """反爬虫装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 刷新配置
            anti_detection.refresh_config()
            
            # 查找page参数
            page = None
            for arg in args:
                if hasattr(arg, 'goto') and hasattr(arg, 'locator'):  # 检查是否是Page对象
                    page = arg
                    break
            
            if not page:
                # 如果没有找到page，直接执行原函数
                return func(*args, **kwargs)
            
            try:
                # 操作前处理
                anti_detection.before_action(page, action_name)
                
                # 执行原函数
                result = func(*args, **kwargs)
                
                # 操作后处理
                success = result is not False and result is not None
                anti_detection.after_action(page, action_name, success)
                
                return result
                
            except Exception as e:
                # 操作失败处理
                anti_detection.after_action(page, action_name, False)
                raise e
        
        return wrapper
    return decorator


def with_navigation_protection(func: Callable) -> Callable:
    """导航保护装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 刷新配置
        anti_detection.refresh_config()
        
        # 查找page和url参数
        page = None
        url = None
        
        for arg in args:
            if hasattr(arg, 'goto') and hasattr(arg, 'locator'):  # Page对象
                page = arg
            elif isinstance(arg, str) and (arg.startswith('http') or arg.startswith('www')):
                url = arg
        
        if not page or not url:
            return func(*args, **kwargs)
        
        try:
            # 导航前处理
            anti_detection.before_navigation(page, url)
            
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 导航后处理
            anti_detection.after_navigation(page, url)
            
            return result
            
        except Exception as e:
            logger.warning("导航保护: 导航失败: {}", str(e))
            raise e
    
    return wrapper


def setup_anti_detection_for_browser_manager(browser_manager):
    """为BrowserManager设置反爬虫"""
    try:
        # 刷新配置
        anti_detection.refresh_config()
        
        if not anti_detection.enabled:
            return
        
        # 设置浏览器上下文
        if hasattr(browser_manager, 'context') and browser_manager.context:
            anti_detection.setup_browser_context(browser_manager.context)
        
        # 设置页面
        if hasattr(browser_manager, 'page') and browser_manager.page:
            anti_detection.setup_page(browser_manager.page)
        
        logger.info("反爬虫集成: 已为BrowserManager设置反爬虫保护")
        
    except Exception as e:
        logger.warning("反爬虫集成: 设置BrowserManager失败: {}", str(e))


def check_browser_restart_needed() -> bool:
    """检查是否需要重启浏览器"""
    try:
        return anti_detection.should_restart_browser()
    except Exception as e:
        logger.warning("反爬虫集成: 检查重启需求失败: {}", str(e))
        return False


def reset_anti_detection_session() -> None:
    """重置反爬虫会话"""
    try:
        anti_detection.reset_session()
    except Exception as e:
        logger.warning("反爬虫集成: 重置会话失败: {}", str(e))


def get_anti_detection_stats() -> dict:
    """获取反爬虫统计信息"""
    try:
        return anti_detection.get_stats()
    except Exception as e:
        logger.warning("反爬虫集成: 获取统计信息失败: {}", str(e))
        return {"mode": "error", "enabled": False}
