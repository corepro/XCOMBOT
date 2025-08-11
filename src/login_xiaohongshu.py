#!/usr/bin/env python3
"""
小红书登录模块
"""

import time
from playwright.sync_api import Page
from src.browser import BrowserManager
from src.logger import logger

# 小红书相关URL
XIAOHONGSHU_HOME_URL = "https://www.xiaohongshu.com"
XIAOHONGSHU_LOGIN_URL = "https://www.xiaohongshu.com/explore"


def open_home_xiaohongshu(page: Page):
    """打开小红书首页"""
    logger.info("打开小红书首页: {}", XIAOHONGSHU_HOME_URL)
    page.goto(XIAOHONGSHU_HOME_URL, timeout=30000)


def is_logged_in_xiaohongshu(page: Page) -> bool:
    """检查是否已登录小红书"""
    try:
        # 检查是否有用户头像或登录状态指示器
        current_url = page.url
        if "xiaohongshu.com" not in current_url:
            return False
        
        # 检查登录状态的几种方式
        # 1. 检查用户头像
        avatar_selectors = [
            "[data-testid='user-avatar']",
            ".avatar",
            ".user-avatar",
            ".header-avatar"
        ]
        
        for selector in avatar_selectors:
            try:
                if page.locator(selector).count() > 0:
                    return True
            except:
                continue
        
        # 2. 检查是否有登录按钮（如果有登录按钮说明未登录）
        login_selectors = [
            "text=登录",
            "text=注册",
            "[data-testid='login-button']"
        ]
        
        for selector in login_selectors:
            try:
                if page.locator(selector).count() > 0:
                    return False
            except:
                continue
        
        # 3. 检查URL是否包含登录相关路径
        if any(path in current_url for path in ["/login", "/signin", "/register"]):
            return False
        
        # 如果没有明确的登录按钮，且在主域名下，可能已登录
        return True
        
    except Exception as e:
        logger.warning("检查小红书登录状态失败: {}", str(e))
        return False


def login_flow_xiaohongshu(bm: BrowserManager, timeout_sec: int = 300) -> None:
    """小红书登录流程"""
    page = bm.page
    assert page is not None
    
    logger.info("开始小红书登录流程")
    
    # 打开小红书首页
    open_home_xiaohongshu(page)
    
    # 检查是否已经登录
    if is_logged_in_xiaohongshu(page):
        logger.info("小红书: 检测到已登录状态")
        bm.save_storage()
        return
    
    logger.info("小红书: 未检测到登录状态，请在打开的页面完成登录，最多等待{}秒…", timeout_sec)
    
    # 等待用户手动登录
    deadline = time.time() + max(5, int(timeout_sec))
    last_log = 0
    
    while time.time() < deadline:
        try:
            current_url = page.url
            
            # 检查是否登录成功
            if is_logged_in_xiaohongshu(page):
                logger.info("小红书: 登录成功，当前URL={}。保存会话…", current_url)
                bm.save_storage()
                return
                
            if time.time() - last_log > 10:
                logger.info("等待登录中… 当前URL={}", current_url)
                last_log = time.time()
                
        except Exception as e:
            logger.warning("检查登录状态时出错: {}", str(e))
        
        time.sleep(1.0)
    
    raise TimeoutError("小红书登录等待超时")


# 兼容性函数，用于测试
def login(bm: BrowserManager, timeout_sec: int = 300) -> bool:
    """兼容性登录函数"""
    try:
        login_flow_xiaohongshu(bm, timeout_sec)
        return True
    except Exception:
        return False


def check_login_status(page) -> bool:
    """兼容性登录状态检查函数"""
    return is_logged_in_xiaohongshu(page)
