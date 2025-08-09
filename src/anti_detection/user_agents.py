"""
用户代理池管理
提供丰富的用户代理字符串用于轮换
"""

import random
from typing import List, Dict, Optional


class UserAgentPool:
    """用户代理池"""
    
    def __init__(self):
        self.user_agents = {
            "chrome_windows": [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            ],
            "chrome_macos": [
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            ],
            "firefox_windows": [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:117.0) Gecko/20100101 Firefox/117.0",
            ],
            "firefox_macos": [
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:119.0) Gecko/20100101 Firefox/119.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:121.0) Gecko/20100101 Firefox/121.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:120.0) Gecko/20100101 Firefox/120.0",
            ],
            "safari_macos": [
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
            ],
            "edge_windows": [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.0.0",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.0.0",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.0.0",
            ]
        }
        
        # 移动端用户代理
        self.mobile_user_agents = {
            "chrome_android": [
                "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                "Mozilla/5.0 (Linux; Android 12; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
                "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
            ],
            "safari_ios": [
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
            ]
        }
        
        # 权重配置（某些浏览器更常见）
        self.browser_weights = {
            "chrome_windows": 0.4,
            "chrome_macos": 0.2,
            "firefox_windows": 0.15,
            "firefox_macos": 0.1,
            "safari_macos": 0.1,
            "edge_windows": 0.05
        }
    
    def get_random_user_agent(self, include_mobile: bool = False) -> str:
        """获取随机用户代理"""
        if include_mobile and random.random() < 0.1:  # 10%概率使用移动端
            category = random.choice(list(self.mobile_user_agents.keys()))
            return random.choice(self.mobile_user_agents[category])
        
        # 根据权重选择浏览器类型
        categories = list(self.browser_weights.keys())
        weights = list(self.browser_weights.values())
        category = random.choices(categories, weights=weights)[0]
        
        return random.choice(self.user_agents[category])
    
    def get_user_agent_by_browser(self, browser: str, os: str = "windows") -> str:
        """根据浏览器类型获取用户代理"""
        key = f"{browser}_{os}"
        if key in self.user_agents:
            return random.choice(self.user_agents[key])
        
        # 回退到随机选择
        return self.get_random_user_agent()
    
    def get_all_user_agents(self) -> List[str]:
        """获取所有用户代理"""
        all_agents = []
        for agents in self.user_agents.values():
            all_agents.extend(agents)
        return all_agents
    
    def get_user_agents_by_platform(self, platform: str) -> List[str]:
        """根据平台获取用户代理"""
        platform_mapping = {
            "weibo": ["chrome_windows", "chrome_macos", "firefox_windows"],
            "zhihu": ["chrome_windows", "chrome_macos", "safari_macos"],
            "xhs": ["chrome_windows", "chrome_macos", "safari_macos"],
            "toutiao": ["chrome_windows", "firefox_windows", "edge_windows"],
            "twitter": ["chrome_windows", "chrome_macos", "firefox_windows", "safari_macos"]
        }
        
        categories = platform_mapping.get(platform, ["chrome_windows", "chrome_macos"])
        agents = []
        for category in categories:
            if category in self.user_agents:
                agents.extend(self.user_agents[category])
        
        return agents if agents else self.get_all_user_agents()


# 全局用户代理池实例
user_agent_pool = UserAgentPool()


def get_random_user_agent(platform: Optional[str] = None, include_mobile: bool = False) -> str:
    """获取随机用户代理的便捷函数"""
    if platform:
        agents = user_agent_pool.get_user_agents_by_platform(platform)
        return random.choice(agents)
    return user_agent_pool.get_random_user_agent(include_mobile)


def get_user_agent_info(user_agent: str) -> Dict[str, str]:
    """解析用户代理信息"""
    info = {
        "browser": "unknown",
        "os": "unknown",
        "version": "unknown"
    }
    
    ua_lower = user_agent.lower()
    
    # 检测浏览器
    if "chrome" in ua_lower and "edg" not in ua_lower:
        info["browser"] = "chrome"
    elif "firefox" in ua_lower:
        info["browser"] = "firefox"
    elif "safari" in ua_lower and "chrome" not in ua_lower:
        info["browser"] = "safari"
    elif "edg" in ua_lower:
        info["browser"] = "edge"
    
    # 检测操作系统
    if "windows" in ua_lower:
        info["os"] = "windows"
    elif "macintosh" in ua_lower or "mac os x" in ua_lower:
        info["os"] = "macos"
    elif "linux" in ua_lower:
        info["os"] = "linux"
    elif "android" in ua_lower:
        info["os"] = "android"
    elif "iphone" in ua_lower or "ipad" in ua_lower:
        info["os"] = "ios"
    
    return info
