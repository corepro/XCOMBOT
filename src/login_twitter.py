#!/usr/bin/env python3
"""
Twitter/X登录模块
"""

import time
from playwright.sync_api import Page
from src.browser import BrowserManager
from src.logger import logger

# Twitter相关URL
TWITTER_HOME_URL = "https://x.com"
TWITTER_LOGIN_URL = "https://x.com/i/flow/login"


def open_home_twitter(page: Page):
    """打开Twitter首页"""
    logger.info("打开Twitter首页: {}", TWITTER_HOME_URL)
    page.goto(TWITTER_HOME_URL, timeout=30000)


def is_logged_in_twitter(page: Page) -> bool:
    """检查是否已登录Twitter"""
    try:
        current_url = page.url
        if "x.com" not in current_url and "twitter.com" not in current_url:
            return False
        
        # 检查登录状态的几种方式
        # 1. 检查是否有用户头像或菜单
        avatar_selectors = [
            "[data-testid='SideNav_AccountSwitcher_Button']",
            "[data-testid='AppTabBar_Profile_Link']",
            "[aria-label*='Profile']",
            ".r-1p0dtai.r-1d2f490.r-u8s1d.r-zchlnj.r-ipm5af"
        ]
        
        for selector in avatar_selectors:
            try:
                if page.locator(selector).count() > 0:
                    return True
            except:
                continue
        
        # 2. 检查是否有登录按钮（如果有登录按钮说明未登录）
        login_selectors = [
            "text=Log in",
            "text=Sign in",
            "text=登录",
            "[data-testid='loginButton']"
        ]
        
        for selector in login_selectors:
            try:
                if page.locator(selector).count() > 0:
                    return False
            except:
                continue
        
        # 3. 检查URL是否包含登录相关路径
        if any(path in current_url for path in ["/login", "/signin", "/i/flow/login"]):
            return False
        
        # 4. 检查是否有发推文按钮（登录后才有）
        tweet_selectors = [
            "[data-testid='tweetButtonInline']",
            "[data-testid='SideNav_NewTweet_Button']",
            "text=Tweet",
            "text=Post"
        ]
        
        for selector in tweet_selectors:
            try:
                if page.locator(selector).count() > 0:
                    return True
            except:
                continue
        
        # 如果没有明确的登录按钮，且在主域名下，可能已登录
        return True
        
    except Exception as e:
        logger.warning("检查Twitter登录状态失败: {}", str(e))
        return False


def login_flow_twitter(bm: BrowserManager, timeout_sec: int = 300) -> None:
    """Twitter登录流程"""
    page = bm.page
    assert page is not None
    
    logger.info("开始Twitter登录流程")
    
    # 打开Twitter首页
    open_home_twitter(page)
    
    # 检查是否已经登录
    if is_logged_in_twitter(page):
        logger.info("Twitter: 检测到已登录状态")
        bm.save_storage()
        return
    
    # 如果未登录，尝试打开登录页面
    logger.info("Twitter: 打开登录页面")
    page.goto(TWITTER_LOGIN_URL, timeout=30000)
    
    logger.info("Twitter: 未检测到登录状态，请在打开的页面完成登录，最多等待{}秒…", timeout_sec)
    
    # 等待用户手动登录
    deadline = time.time() + max(5, int(timeout_sec))
    last_log = 0
    
    while time.time() < deadline:
        try:
            current_url = page.url
            
            # 检查是否登录成功
            if is_logged_in_twitter(page):
                logger.info("Twitter: 登录成功，当前URL={}。保存会话…", current_url)
                bm.save_storage()
                return
                
            if time.time() - last_log > 10:
                logger.info("等待登录中… 当前URL={}", current_url)
                last_log = time.time()
                
        except Exception as e:
            logger.warning("检查登录状态时出错: {}", str(e))
        
        time.sleep(1.0)
    
    raise TimeoutError("Twitter登录等待超时")


# 兼容性函数，用于测试
def login(bm: BrowserManager, timeout_sec: int = 300) -> bool:
    """兼容性登录函数"""
    try:
        login_flow_twitter(bm, timeout_sec)
        return True
    except Exception:
        return False


def check_login_status(page) -> bool:
    """兼容性登录状态检查函数"""
    return is_logged_in_twitter(page)
