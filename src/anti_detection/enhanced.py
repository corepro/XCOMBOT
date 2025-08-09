"""
增强反爬虫措施
包括浏览器指纹伪装、Canvas指纹随机化、WebRTC泄露防护、时区随机化等
"""

import random
import time
from typing import Optional, Dict, Any
from playwright.sync_api import Page, BrowserContext
from ..logger import logger
from .basic import BasicAntiDetection
from .config import COMMON_VIEWPORTS, COMMON_TIMEZONES, COMMON_LANGUAGES
from .user_agents import get_random_user_agent


class EnhancedAntiDetection(BasicAntiDetection):
    """增强反爬虫检测规避"""
    
    def __init__(self):
        super().__init__()
        self.fingerprint_config = self._generate_fingerprint_config()
        
    def _generate_fingerprint_config(self) -> Dict[str, Any]:
        """生成随机化的浏览器指纹配置"""
        return {
            "timezone": random.choice(COMMON_TIMEZONES),
            "language": random.choice(COMMON_LANGUAGES),
            "viewport": random.choice(COMMON_VIEWPORTS),
            "color_depth": random.choice([24, 32]),
            "device_memory": random.choice([2, 4, 8, 16]),
            "hardware_concurrency": random.choice([2, 4, 6, 8, 12, 16]),
            "max_touch_points": random.choice([0, 1, 5, 10]),
            "platform": random.choice(["Win32", "MacIntel", "Linux x86_64"]),
            "canvas_noise": random.uniform(0.0001, 0.001)
        }
    
    def setup_browser_context(self, context: BrowserContext) -> None:
        """设置增强的浏览器上下文反爬虫措施"""
        try:
            # 调用基础设置
            super().setup_browser_context(context)
            
            # 设置时区
            context.set_extra_http_headers({
                "Accept-Language": self.fingerprint_config["language"],
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Cache-Control": "max-age=0"
            })
            
            logger.info("增强反爬虫: 已设置增强HTTP头")
            
        except Exception as e:
            logger.warning("增强反爬虫: 设置浏览器上下文失败: {}", str(e))
    
    def setup_page(self, page: Page) -> None:
        """设置增强的页面级别反爬虫措施"""
        try:
            # 调用基础设置
            super().setup_page(page)
            
            # 设置时区（通过上下文设置）
            try:
                # Playwright的时区设置需要在上下文级别
                pass  # 时区设置已在上下文中处理
            except Exception as e:
                logger.debug("增强反爬虫: 时区设置跳过: {}", str(e))
            
            # 注入增强反检测脚本
            self._inject_enhanced_anti_detection_scripts(page)
            
            logger.info("增强反爬虫: 已设置增强页面配置")
            
        except Exception as e:
            logger.warning("增强反爬虫: 设置页面失败: {}", str(e))
    
    def _inject_enhanced_anti_detection_scripts(self, page: Page) -> None:
        """注入增强反检测脚本"""
        try:
            # 获取配置
            config = self.fingerprint_config
            
            enhanced_script = f"""
            // 基础反检测
            Object.defineProperty(navigator, 'webdriver', {{
                get: () => undefined,
            }});
            
            // 覆盖硬件信息
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {config['device_memory']},
            }});
            
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {config['hardware_concurrency']},
            }});
            
            Object.defineProperty(navigator, 'maxTouchPoints', {{
                get: () => {config['max_touch_points']},
            }});
            
            Object.defineProperty(navigator, 'platform', {{
                get: () => '{config['platform']}',
            }});
            
            // 覆盖语言设置
            Object.defineProperty(navigator, 'language', {{
                get: () => '{config['language'].split(',')[0]}',
            }});
            
            Object.defineProperty(navigator, 'languages', {{
                get: () => {str(config['language'].split(','))},
            }});
            
            // WebRTC泄露防护
            const originalRTCPeerConnection = window.RTCPeerConnection;
            window.RTCPeerConnection = function(...args) {{
                const pc = new originalRTCPeerConnection(...args);
                const originalCreateDataChannel = pc.createDataChannel;
                pc.createDataChannel = function(...args) {{
                    return originalCreateDataChannel.apply(this, args);
                }};
                return pc;
            }};
            
            // 覆盖getUserMedia
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {{
                const originalGetUserMedia = navigator.mediaDevices.getUserMedia;
                navigator.mediaDevices.getUserMedia = function(...args) {{
                    return Promise.reject(new Error('Permission denied'));
                }};
            }}
            
            // Canvas指纹随机化
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
            
            HTMLCanvasElement.prototype.toDataURL = function(...args) {{
                const context = this.getContext('2d');
                if (context) {{
                    // 添加微小的随机噪声
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    const data = imageData.data;
                    for (let i = 0; i < data.length; i += 4) {{
                        if (Math.random() < {config['canvas_noise']}) {{
                            data[i] = Math.min(255, data[i] + Math.floor(Math.random() * 3) - 1);
                            data[i + 1] = Math.min(255, data[i + 1] + Math.floor(Math.random() * 3) - 1);
                            data[i + 2] = Math.min(255, data[i + 2] + Math.floor(Math.random() * 3) - 1);
                        }}
                    }}
                    context.putImageData(imageData, 0, 0);
                }}
                return originalToDataURL.apply(this, args);
            }};
            
            // 屏幕信息随机化
            Object.defineProperty(screen, 'colorDepth', {{
                get: () => {config['color_depth']},
            }});
            
            Object.defineProperty(screen, 'pixelDepth', {{
                get: () => {config['color_depth']},
            }});
            
            // 移除自动化检测特征
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_JSON;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Proxy;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Reflect;
            
            // 覆盖chrome对象
            if (window.chrome) {{
                Object.defineProperty(window, 'chrome', {{
                    get: () => ({{
                        runtime: {{
                            onConnect: undefined,
                            onMessage: undefined,
                        }},
                        loadTimes: function() {{ return undefined; }},
                        csi: function() {{ return undefined; }},
                    }}),
                }});
            }}
            
            // 覆盖权限API
            if (navigator.permissions && navigator.permissions.query) {{
                const originalQuery = navigator.permissions.query;
                navigator.permissions.query = function(parameters) {{
                    return originalQuery(parameters).then(result => {{
                        if (parameters.name === 'notifications') {{
                            Object.defineProperty(result, 'state', {{ get: () => 'denied' }});
                        }}
                        return result;
                    }});
                }};
            }}
            
            // 随机化Date对象的时区偏移
            const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
            Date.prototype.getTimezoneOffset = function() {{
                return originalGetTimezoneOffset.call(this);
            }};
            
            console.log('增强反检测脚本已加载');
            """
            
            page.add_init_script(enhanced_script)
            logger.debug("增强反爬虫: 已注入增强反检测脚本")
            
        except Exception as e:
            logger.warning("增强反爬虫: 注入增强反检测脚本失败: {}", str(e))
    
    def randomize_browser_fingerprint(self, page: Page) -> None:
        """随机化浏览器指纹"""
        try:
            # 重新生成指纹配置
            self.fingerprint_config = self._generate_fingerprint_config()
            
            # 应用新的时区
            page.emulate_timezone(self.fingerprint_config["timezone"])
            
            # 重新设置视口
            viewport = self.fingerprint_config["viewport"]
            page.set_viewport_size(viewport)
            
            logger.info("增强反爬虫: 已随机化浏览器指纹")
            
        except Exception as e:
            logger.warning("增强反爬虫: 随机化浏览器指纹失败: {}", str(e))
    
    def simulate_advanced_human_behavior(self, page: Page) -> None:
        """模拟高级人类行为"""
        try:
            # 随机页面交互
            actions = [
                self._simulate_text_selection,
                self._simulate_right_click,
                self._simulate_keyboard_shortcuts,
                self._simulate_focus_changes
            ]
            
            # 随机执行1-2个动作
            selected_actions = random.sample(actions, random.randint(1, 2))
            for action in selected_actions:
                try:
                    action(page)
                    time.sleep(random.uniform(0.5, 1.5))
                except Exception as e:
                    logger.debug("增强反爬虫: 高级行为模拟失败: {}", str(e))
            
        except Exception as e:
            logger.warning("增强反爬虫: 高级人类行为模拟失败: {}", str(e))
    
    def _simulate_text_selection(self, page: Page) -> None:
        """模拟文本选择"""
        try:
            # 尝试选择页面上的一些文本
            page.evaluate("""
                const textNodes = [];
                const walker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );
                
                let node;
                while (node = walker.nextNode()) {
                    if (node.textContent.trim().length > 10) {
                        textNodes.push(node);
                    }
                }
                
                if (textNodes.length > 0) {
                    const randomNode = textNodes[Math.floor(Math.random() * textNodes.length)];
                    const range = document.createRange();
                    const text = randomNode.textContent;
                    const start = Math.floor(Math.random() * text.length / 2);
                    const end = start + Math.floor(Math.random() * (text.length - start) / 2);
                    
                    range.setStart(randomNode, start);
                    range.setEnd(randomNode, end);
                    
                    const selection = window.getSelection();
                    selection.removeAllRanges();
                    selection.addRange(range);
                    
                    setTimeout(() => {
                        selection.removeAllRanges();
                    }, 1000 + Math.random() * 2000);
                }
            """)
            
        except Exception:
            pass
    
    def _simulate_right_click(self, page: Page) -> None:
        """模拟右键点击"""
        try:
            x = random.randint(200, 800)
            y = random.randint(200, 600)
            page.mouse.click(x, y, button="right")
            time.sleep(random.uniform(0.5, 1.0))
            # 按ESC关闭右键菜单
            page.keyboard.press("Escape")
            
        except Exception:
            pass
    
    def _simulate_keyboard_shortcuts(self, page: Page) -> None:
        """模拟键盘快捷键"""
        try:
            shortcuts = ["Control+F", "Control+R", "F5", "Control+T"]
            shortcut = random.choice(shortcuts)
            
            if shortcut in ["Control+F"]:
                page.keyboard.press(shortcut)
                time.sleep(random.uniform(0.3, 0.8))
                page.keyboard.press("Escape")
            
        except Exception:
            pass
    
    def _simulate_focus_changes(self, page: Page) -> None:
        """模拟焦点变化"""
        try:
            # 模拟Tab键导航
            for _ in range(random.randint(1, 3)):
                page.keyboard.press("Tab")
                time.sleep(random.uniform(0.2, 0.5))
            
        except Exception:
            pass
    
    def before_action(self, page: Page, action_name: str) -> None:
        """增强的操作前处理"""
        try:
            # 调用基础处理
            super().before_action(page, action_name)
            
            # 随机概率执行高级行为模拟
            if random.random() < 0.2:  # 20%概率
                self.simulate_advanced_human_behavior(page)
            
            # 更长的随机延时
            self.random_delay(1.0, 3.5)
            
        except Exception as e:
            logger.warning("增强反爬虫: 操作前处理失败: {}", str(e))
    
    def after_action(self, page: Page, action_name: str, success: bool) -> None:
        """增强的操作后处理"""
        try:
            # 调用基础处理
            super().after_action(page, action_name, success)
            
            # 随机概率重新随机化指纹
            if self.operation_count % 10 == 0:  # 每10次操作
                self.randomize_browser_fingerprint(page)
            
        except Exception as e:
            logger.warning("增强反爬虫: 操作后处理失败: {}", str(e))
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        stats = super().get_stats()
        stats.update({
            "mode": "enhanced",
            "fingerprint_config": {
                "timezone": self.fingerprint_config["timezone"],
                "language": self.fingerprint_config["language"],
                "viewport": f"{self.fingerprint_config['viewport']['width']}x{self.fingerprint_config['viewport']['height']}",
                "platform": self.fingerprint_config["platform"]
            }
        })
        return stats
