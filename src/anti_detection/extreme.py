"""
极限反爬虫措施
包括代理IP轮换、浏览器实例重建、会话隔离、行为模式随机化等
"""

import random
import time
import os
import tempfile
from typing import Optional, List, Dict, Any
from playwright.sync_api import Page, BrowserContext, Browser
from ..logger import logger
from .enhanced import EnhancedAntiDetection
from .config import DEFAULT_USER_AGENTS


class ExtremeAntiDetection(EnhancedAntiDetection):
    """极限反爬虫检测规避"""
    
    def __init__(self):
        super().__init__()
        self.proxy_pool = []
        self.current_proxy = None
        self.browser_restart_counter = 0
        self.session_data_dir = None
        self.behavior_patterns = self._generate_behavior_patterns()
        
    def _generate_behavior_patterns(self) -> Dict[str, Any]:
        """生成随机化的行为模式"""
        return {
            "typing_speed": random.uniform(0.05, 0.2),  # 每个字符的延时
            "click_delay": random.uniform(0.1, 0.5),
            "scroll_pattern": random.choice(["smooth", "stepped", "random"]),
            "reading_speed": random.choice(["fast", "normal", "slow"]),
            "interaction_probability": random.uniform(0.1, 0.4),
            "exploration_time": random.uniform(3.0, 10.0)
        }
    
    def set_proxy_pool(self, proxies: List[str]) -> None:
        """设置代理池"""
        self.proxy_pool = proxies.copy()
        logger.info("极限反爬虫: 设置代理池，共 {} 个代理", len(self.proxy_pool))
    
    def rotate_proxy(self) -> Optional[str]:
        """轮换代理"""
        if not self.proxy_pool:
            return None
        
        # 避免连续使用同一个代理
        available_proxies = [p for p in self.proxy_pool if p != self.current_proxy]
        if not available_proxies:
            available_proxies = self.proxy_pool
        
        self.current_proxy = random.choice(available_proxies)
        logger.info("极限反爬虫: 切换代理到: {}", self.current_proxy)
        return self.current_proxy
    
    def create_isolated_session_dir(self) -> str:
        """创建隔离的会话目录"""
        try:
            if self.session_data_dir and os.path.exists(self.session_data_dir):
                # 清理旧的会话目录
                import shutil
                shutil.rmtree(self.session_data_dir, ignore_errors=True)
            
            self.session_data_dir = tempfile.mkdtemp(prefix="anti_detect_session_")
            logger.info("极限反爬虫: 创建隔离会话目录: {}", self.session_data_dir)
            return self.session_data_dir
            
        except Exception as e:
            logger.warning("极限反爬虫: 创建会话目录失败: {}", str(e))
            return tempfile.gettempdir()
    
    def setup_browser_context(self, context: BrowserContext) -> None:
        """设置极限的浏览器上下文反爬虫措施"""
        try:
            # 调用增强设置
            super().setup_browser_context(context)
            
            # 设置更多反检测头部
            context.set_extra_http_headers({
                "Accept-Language": self.fingerprint_config["language"],
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0",
                "Pragma": "no-cache",
                "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": f'"{self.fingerprint_config["platform"]}"'
            })
            
            logger.info("极限反爬虫: 已设置极限HTTP头")
            
        except Exception as e:
            logger.warning("极限反爬虫: 设置浏览器上下文失败: {}", str(e))
    
    def setup_page(self, page: Page) -> None:
        """设置极限的页面级别反爬虫措施"""
        try:
            # 调用增强设置
            super().setup_page(page)
            
            # 注入极限反检测脚本
            self._inject_extreme_anti_detection_scripts(page)
            
            # 设置页面事件监听器
            self._setup_page_event_listeners(page)
            
            logger.info("极限反爬虫: 已设置极限页面配置")
            
        except Exception as e:
            logger.warning("极限反爬虫: 设置页面失败: {}", str(e))
    
    def _inject_extreme_anti_detection_scripts(self, page: Page) -> None:
        """注入极限反检测脚本"""
        try:
            extreme_script = """
            // 极限反检测脚本
            
            // 覆盖所有可能的自动化检测点
            const originalDefineProperty = Object.defineProperty;
            Object.defineProperty = function(obj, prop, descriptor) {
                if (prop === 'webdriver' || prop === 'driver' || prop === '__webdriver_script_fn') {
                    return obj;
                }
                return originalDefineProperty.call(this, obj, prop, descriptor);
            };
            
            // 覆盖console.debug以隐藏自动化痕迹
            const originalConsoleDebug = console.debug;
            console.debug = function(...args) {
                if (args.some(arg => typeof arg === 'string' && 
                    (arg.includes('DevTools') || arg.includes('automation') || arg.includes('webdriver')))) {
                    return;
                }
                return originalConsoleDebug.apply(this, args);
            };
            
            // 伪造更多navigator属性
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { 
                get: () => {
                    const plugins = [];
                    plugins.length = Math.floor(Math.random() * 5) + 3;
                    return plugins;
                }
            });
            
            // 伪造电池API
            if (navigator.getBattery) {
                const originalGetBattery = navigator.getBattery;
                navigator.getBattery = function() {
                    return Promise.resolve({
                        charging: Math.random() > 0.5,
                        chargingTime: Math.random() * 10000,
                        dischargingTime: Math.random() * 50000,
                        level: Math.random()
                    });
                };
            }
            
            // 伪造网络连接信息
            if (navigator.connection) {
                Object.defineProperty(navigator, 'connection', {
                    get: () => ({
                        effectiveType: ['slow-2g', '2g', '3g', '4g'][Math.floor(Math.random() * 4)],
                        downlink: Math.random() * 10,
                        rtt: Math.floor(Math.random() * 300) + 50
                    })
                });
            }
            
            // 覆盖Date.now以添加微小的随机偏移
            const originalDateNow = Date.now;
            Date.now = function() {
                return originalDateNow() + Math.floor(Math.random() * 10) - 5;
            };
            
            // 覆盖performance.now
            const originalPerformanceNow = performance.now;
            performance.now = function() {
                return originalPerformanceNow() + Math.random() * 0.1;
            };
            
            // 伪造触摸事件支持
            if (!window.TouchEvent) {
                window.TouchEvent = function() {};
            }
            
            // 移除所有已知的自动化检测属性
            const automationProps = [
                'cdc_adoQpoasnfa76pfcZLmcfl_Array',
                'cdc_adoQpoasnfa76pfcZLmcfl_Promise', 
                'cdc_adoQpoasnfa76pfcZLmcfl_Symbol',
                'cdc_adoQpoasnfa76pfcZLmcfl_JSON',
                'cdc_adoQpoasnfa76pfcZLmcfl_Object',
                'cdc_adoQpoasnfa76pfcZLmcfl_Proxy',
                'cdc_adoQpoasnfa76pfcZLmcfl_Reflect',
                '__webdriver_evaluate',
                '__selenium_evaluate',
                '__webdriver_script_function',
                '__webdriver_script_func',
                '__webdriver_script_fn',
                '__fxdriver_evaluate',
                '__driver_unwrapped',
                '__webdriver_unwrapped',
                '__driver_evaluate',
                '__selenium_unwrapped',
                '__fxdriver_unwrapped'
            ];
            
            automationProps.forEach(prop => {
                delete window[prop];
            });
            
            // 伪造iframe检测
            const originalCreateElement = document.createElement;
            document.createElement = function(tagName) {
                const element = originalCreateElement.call(this, tagName);
                if (tagName.toLowerCase() === 'iframe') {
                    // 添加随机延时
                    setTimeout(() => {
                        if (element.contentWindow) {
                            automationProps.forEach(prop => {
                                delete element.contentWindow[prop];
                            });
                        }
                    }, Math.random() * 100);
                }
                return element;
            };
            
            console.log('极限反检测脚本已加载');
            """
            
            page.add_init_script(extreme_script)
            logger.debug("极限反爬虫: 已注入极限反检测脚本")
            
        except Exception as e:
            logger.warning("极限反爬虫: 注入极限反检测脚本失败: {}", str(e))
    
    def _setup_page_event_listeners(self, page: Page) -> None:
        """设置页面事件监听器"""
        try:
            # 监听页面错误并处理
            def handle_page_error(error):
                logger.debug("极限反爬虫: 页面错误: {}", str(error))
            
            def handle_console_message(msg):
                # 过滤掉可能暴露自动化的控制台消息
                if any(keyword in msg.text.lower() for keyword in 
                       ['webdriver', 'automation', 'selenium', 'playwright']):
                    return
                logger.debug("极限反爬虫: 控制台消息: {}", msg.text)
            
            page.on("pageerror", handle_page_error)
            page.on("console", handle_console_message)
            
        except Exception as e:
            logger.warning("极限反爬虫: 设置页面事件监听器失败: {}", str(e))
    
    def simulate_extreme_human_behavior(self, page: Page) -> None:
        """模拟极限人类行为"""
        try:
            pattern = self.behavior_patterns
            
            # 根据行为模式执行不同的动作
            actions = []
            
            # 页面探索
            if random.random() < pattern["interaction_probability"]:
                actions.append(lambda: self._simulate_page_exploration(page, pattern["exploration_time"]))
            
            # 复杂的鼠标行为
            if random.random() < 0.3:
                actions.append(lambda: self._simulate_complex_mouse_behavior(page))
            
            # 键盘交互
            if random.random() < 0.2:
                actions.append(lambda: self._simulate_keyboard_interaction(page))
            
            # 执行选中的动作
            for action in actions:
                try:
                    action()
                    time.sleep(random.uniform(0.5, 2.0))
                except Exception as e:
                    logger.debug("极限反爬虫: 极限行为模拟失败: {}", str(e))
            
        except Exception as e:
            logger.warning("极限反爬虫: 极限人类行为模拟失败: {}", str(e))
    
    def _simulate_page_exploration(self, page: Page, duration: float) -> None:
        """模拟页面探索"""
        try:
            start_time = time.time()
            while time.time() - start_time < duration:
                action = random.choice(["scroll", "hover", "click_empty", "select_text"])
                
                if action == "scroll":
                    self._simulate_natural_scroll(page)
                elif action == "hover":
                    self._simulate_random_hover(page)
                elif action == "click_empty":
                    self._simulate_empty_click(page)
                elif action == "select_text":
                    self._simulate_text_selection(page)
                
                time.sleep(random.uniform(0.5, 2.0))
                
        except Exception:
            pass
    
    def _simulate_complex_mouse_behavior(self, page: Page) -> None:
        """模拟复杂鼠标行为"""
        try:
            # 模拟鼠标轨迹
            for _ in range(random.randint(3, 8)):
                x = random.randint(100, 1200)
                y = random.randint(100, 800)
                
                # 使用贝塞尔曲线移动
                page.mouse.move(x, y, steps=random.randint(10, 30))
                time.sleep(random.uniform(0.1, 0.5))
                
                # 随机停顿
                if random.random() < 0.3:
                    time.sleep(random.uniform(0.5, 1.5))
            
        except Exception:
            pass
    
    def _simulate_keyboard_interaction(self, page: Page) -> None:
        """模拟键盘交互"""
        try:
            # 模拟各种键盘操作
            keys = ["Tab", "Shift+Tab", "Home", "End", "PageUp", "PageDown"]
            key = random.choice(keys)
            page.keyboard.press(key)
            
        except Exception:
            pass
    
    def before_action(self, page: Page, action_name: str) -> None:
        """极限的操作前处理"""
        try:
            # 调用增强处理
            super().before_action(page, action_name)
            
            # 检查是否需要重启浏览器
            self.browser_restart_counter += 1
            if self.browser_restart_counter >= 20:  # 每20次操作重启
                logger.info("极限反爬虫: 达到重启阈值，建议重启浏览器")
                self.browser_restart_counter = 0
            
            # 极限行为模拟
            if random.random() < 0.4:  # 40%概率
                self.simulate_extreme_human_behavior(page)
            
            # 更长的随机延时
            self.random_delay(1.5, 5.0)
            
        except Exception as e:
            logger.warning("极限反爬虫: 操作前处理失败: {}", str(e))
    
    def should_restart_browser(self) -> bool:
        """判断是否应该重启浏览器"""
        return self.browser_restart_counter >= 20
    
    def reset_session(self) -> None:
        """重置会话"""
        try:
            # 重新生成行为模式
            self.behavior_patterns = self._generate_behavior_patterns()
            
            # 重新生成指纹配置
            self.fingerprint_config = self._generate_fingerprint_config()
            
            # 轮换代理
            if self.proxy_pool:
                self.rotate_proxy()
            
            # 重置计数器
            self.browser_restart_counter = 0
            
            logger.info("极限反爬虫: 会话已重置")
            
        except Exception as e:
            logger.warning("极限反爬虫: 重置会话失败: {}", str(e))
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        stats = super().get_stats()
        stats.update({
            "mode": "extreme",
            "proxy_pool_size": len(self.proxy_pool),
            "current_proxy": self.current_proxy,
            "browser_restart_counter": self.browser_restart_counter,
            "behavior_patterns": self.behavior_patterns
        })
        return stats

    def add_stealth_scripts(self, page: Page) -> None:
        """添加极限版隐身脚本"""
        try:
            # 调用增强版本
            super().add_stealth_scripts(page)

            # 极限版本的额外隐身脚本
            extreme_stealth_script = f"""
            // 极限反检测脚本

            // 完全隐藏自动化特征
            Object.defineProperty(navigator, 'webdriver', {{
                get: () => undefined,
                configurable: true
            }});

            // 删除自动化相关属性
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;

            // 伪造Chrome运行时
            window.chrome = {{
                app: {{
                    isInstalled: false,
                }},
                webstore: {{
                    onInstallStageChanged: {{}},
                    onDownloadProgress: {{}},
                }},
                runtime: {{
                    PlatformOs: {{
                        MAC: 'mac',
                        WIN: 'win',
                        ANDROID: 'android',
                        CROS: 'cros',
                        LINUX: 'linux',
                        OPENBSD: 'openbsd',
                    }},
                    PlatformArch: {{
                        ARM: 'arm',
                        X86_32: 'x86-32',
                        X86_64: 'x86-64',
                    }},
                    PlatformNaclArch: {{
                        ARM: 'arm',
                        X86_32: 'x86-32',
                        X86_64: 'x86-64',
                    }},
                    RequestUpdateCheckStatus: {{
                        THROTTLED: 'throttled',
                        NO_UPDATE: 'no_update',
                        UPDATE_AVAILABLE: 'update_available',
                    }},
                    OnInstalledReason: {{
                        INSTALL: 'install',
                        UPDATE: 'update',
                        CHROME_UPDATE: 'chrome_update',
                        SHARED_MODULE_UPDATE: 'shared_module_update',
                    }},
                    OnRestartRequiredReason: {{
                        APP_UPDATE: 'app_update',
                        OS_UPDATE: 'os_update',
                        PERIODIC: 'periodic',
                    }},
                }},
            }};

            // 伪造权限API
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({{ state: Notification.permission }}) :
                    originalQuery(parameters)
            );

            // 随机化硬件并发数
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {random.choice([2, 4, 8, 12, 16])},
            }});

            // 随机化内存信息
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {random.choice([2, 4, 8, 16])},
            }});

            // 伪造插件信息
            Object.defineProperty(navigator, 'plugins', {{
                get: () => {{
                    const plugins = [];
                    plugins.length = {random.randint(3, 8)};
                    return plugins;
                }},
            }});

            // 随机化语言设置
            Object.defineProperty(navigator, 'language', {{
                get: () => '{random.choice(['zh-CN', 'en-US', 'zh-TW'])}',
            }});

            Object.defineProperty(navigator, 'languages', {{
                get: () => ['{random.choice(['zh-CN', 'en-US', 'zh-TW'])}', 'en'],
            }});
            """

            page.add_init_script(extreme_stealth_script)
            logger.debug("极限反爬虫: 已添加极限版隐身脚本")

        except Exception as e:
            logger.warning("极限反爬虫: 添加隐身脚本失败: {}", str(e))
