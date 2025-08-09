"""
反爬虫配置模块
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class AntiDetectionMode(Enum):
    """反爬虫模式枚举"""
    OFF = "off"           # 关闭
    BASIC = "basic"       # 基础模式
    ENHANCED = "enhanced" # 增强模式
    EXTREME = "extreme"   # 极限模式


class AntiDetectionConfig(BaseModel):
    """反爬虫配置"""
    
    # 基础配置
    mode: AntiDetectionMode = AntiDetectionMode.OFF
    enabled: bool = False
    
    # 延时配置
    min_delay: float = 0.5
    max_delay: float = 2.0
    action_delay_multiplier: float = 1.0
    
    # 用户代理配置
    rotate_user_agent: bool = True
    user_agent_pool: List[str] = []
    
    # 浏览器指纹配置
    randomize_viewport: bool = True
    randomize_timezone: bool = True
    randomize_language: bool = True
    block_webrtc: bool = True
    randomize_canvas: bool = True
    
    # 代理配置
    proxy_rotation: bool = False
    proxy_pool: List[str] = []
    
    # 行为模拟配置
    simulate_human_behavior: bool = True
    random_scroll_probability: float = 0.3
    random_mouse_move_probability: float = 0.2
    page_stay_min_seconds: float = 2.0
    page_stay_max_seconds: float = 8.0
    
    # 会话管理配置
    session_isolation: bool = False
    browser_restart_interval: int = 50  # 操作多少次后重启浏览器
    
    @classmethod
    def get_basic_config(cls) -> "AntiDetectionConfig":
        """获取基础模式配置"""
        return cls(
            mode=AntiDetectionMode.BASIC,
            enabled=True,
            min_delay=0.8,
            max_delay=2.5,
            rotate_user_agent=True,
            simulate_human_behavior=True,
            random_scroll_probability=0.2,
            random_mouse_move_probability=0.1
        )
    
    @classmethod
    def get_enhanced_config(cls) -> "AntiDetectionConfig":
        """获取增强模式配置"""
        return cls(
            mode=AntiDetectionMode.ENHANCED,
            enabled=True,
            min_delay=1.0,
            max_delay=3.5,
            action_delay_multiplier=1.5,
            rotate_user_agent=True,
            randomize_viewport=True,
            randomize_timezone=True,
            randomize_language=True,
            block_webrtc=True,
            randomize_canvas=True,
            simulate_human_behavior=True,
            random_scroll_probability=0.4,
            random_mouse_move_probability=0.3,
            page_stay_min_seconds=3.0,
            page_stay_max_seconds=10.0
        )
    
    @classmethod
    def get_extreme_config(cls) -> "AntiDetectionConfig":
        """获取极限模式配置"""
        return cls(
            mode=AntiDetectionMode.EXTREME,
            enabled=True,
            min_delay=1.5,
            max_delay=5.0,
            action_delay_multiplier=2.0,
            rotate_user_agent=True,
            randomize_viewport=True,
            randomize_timezone=True,
            randomize_language=True,
            block_webrtc=True,
            randomize_canvas=True,
            proxy_rotation=True,
            simulate_human_behavior=True,
            random_scroll_probability=0.6,
            random_mouse_move_probability=0.5,
            page_stay_min_seconds=5.0,
            page_stay_max_seconds=15.0,
            session_isolation=True,
            browser_restart_interval=20
        )


# 默认用户代理池
DEFAULT_USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    
    # Chrome macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    
    # Firefox macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    
    # Safari macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    
    # Edge Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
]

# 常见屏幕分辨率
COMMON_VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1280, "height": 720},
    {"width": 1600, "height": 900},
    {"width": 1024, "height": 768},
    {"width": 1280, "height": 800}
]

# 常见时区
COMMON_TIMEZONES = [
    "Asia/Shanghai",
    "Asia/Tokyo", 
    "America/New_York",
    "America/Los_Angeles",
    "Europe/London",
    "Europe/Paris",
    "Asia/Seoul",
    "Asia/Hong_Kong"
]

# 常见语言
COMMON_LANGUAGES = [
    "zh-CN,zh;q=0.9,en;q=0.8",
    "en-US,en;q=0.9",
    "ja-JP,ja;q=0.9,en;q=0.8",
    "ko-KR,ko;q=0.9,en;q=0.8",
    "zh-TW,zh;q=0.9,en;q=0.8"
]
