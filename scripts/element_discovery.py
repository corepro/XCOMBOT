#!/usr/bin/env python3
"""
全自动元素获取与分析工具
用于获取微博平台的最新元素定位信息
"""
from __future__ import annotations
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import CONFIG
from src.browser import BrowserManager
from src.logger import logger
from src.login_weibo import ensure_login_weibo

class ElementDiscovery:
    """元素发现和分析工具"""
    
    def __init__(self):
        self.discovered_elements = {}
        self.operation_log = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def log_operation(self, operation: str, element_info: dict, success: bool, details: str = ""):
        """记录操作日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "element_info": element_info,
            "success": success,
            "details": details
        }
        self.operation_log.append(log_entry)
        logger.info("操作记录: {} - {} - {}", operation, "成功" if success else "失败", details)
    
    def discover_page_elements(self, page, page_name: str):
        """发现页面中的关键元素"""
        logger.info("开始分析页面: {}", page_name)
        
        # 等待页面加载完成
        page.wait_for_load_state("domcontentloaded")
        time.sleep(2)
        
        elements = {}
        
        # 1. 查找评论相关元素
        logger.info("查找评论相关元素...")
        comment_elements = self._find_comment_elements(page)
        elements.update(comment_elements)
        
        # 2. 查找点赞相关元素
        logger.info("查找点赞相关元素...")
        like_elements = self._find_like_elements(page)
        elements.update(like_elements)
        
        # 3. 查找转发相关元素
        logger.info("查找转发相关元素...")
        repost_elements = self._find_repost_elements(page)
        elements.update(repost_elements)
        
        # 4. 查找关注相关元素
        logger.info("查找关注相关元素...")
        follow_elements = self._find_follow_elements(page)
        elements.update(follow_elements)
        
        self.discovered_elements[page_name] = elements
        return elements
    
    def _find_comment_elements(self, page):
        """查找评论相关元素"""
        elements = {}
        
        # 评论按钮候选选择器
        comment_btn_selectors = [
            "button:has-text('评论')",
            "[role=button]:has-text('评论')",
            "button[title*='评论']",
            ".comment-btn",
            "[data-testid*='comment']",
            "button[aria-label*='评论']"
        ]
        
        for i, selector in enumerate(comment_btn_selectors):
            try:
                elements_found = page.locator(selector).all()
                for j, elem in enumerate(elements_found):
                    if elem.is_visible():
                        element_info = {
                            "selector": selector,
                            "xpath": self._get_xpath(elem),
                            "text": elem.inner_text() or "",
                            "enabled": elem.is_enabled(),
                            "visible": elem.is_visible(),
                            "bounding_box": elem.bounding_box()
                        }
                        elements[f"comment_btn_{i}_{j}"] = element_info
                        logger.info("发现评论按钮: {} - {}", selector, element_info["text"])
            except Exception as e:
                logger.debug("评论按钮选择器 {} 失败: {}", selector, e)
        
        # 评论输入框候选选择器
        comment_box_selectors = [
            "textarea[placeholder*='评论']",
            "textarea[placeholder*='说点什么']",
            "#comment-textarea",
            ".comment-textarea",
            "textarea",
            "[role='textbox']"
        ]
        
        for i, selector in enumerate(comment_box_selectors):
            try:
                elements_found = page.locator(selector).all()
                for j, elem in enumerate(elements_found):
                    if elem.is_visible():
                        element_info = {
                            "selector": selector,
                            "xpath": self._get_xpath(elem),
                            "placeholder": elem.get_attribute("placeholder") or "",
                            "enabled": elem.is_enabled(),
                            "visible": elem.is_visible(),
                            "bounding_box": elem.bounding_box()
                        }
                        elements[f"comment_box_{i}_{j}"] = element_info
                        logger.info("发现评论输入框: {} - {}", selector, element_info["placeholder"])
            except Exception as e:
                logger.debug("评论输入框选择器 {} 失败: {}", selector, e)
        
        return elements
    
    def _find_like_elements(self, page):
        """查找点赞相关元素"""
        elements = {}
        
        like_btn_selectors = [
            "button:has-text('赞')",
            "[role=button][aria-label*='赞']",
            "button[title*='赞']",
            ".like-btn",
            "[data-testid*='like']",
            "button[aria-label*='Like']"
        ]
        
        for i, selector in enumerate(like_btn_selectors):
            try:
                elements_found = page.locator(selector).all()
                for j, elem in enumerate(elements_found):
                    if elem.is_visible():
                        element_info = {
                            "selector": selector,
                            "xpath": self._get_xpath(elem),
                            "text": elem.inner_text() or "",
                            "aria_label": elem.get_attribute("aria-label") or "",
                            "class": elem.get_attribute("class") or "",
                            "enabled": elem.is_enabled(),
                            "visible": elem.is_visible(),
                            "bounding_box": elem.bounding_box()
                        }
                        elements[f"like_btn_{i}_{j}"] = element_info
                        logger.info("发现点赞按钮: {} - {}", selector, element_info["text"])
            except Exception as e:
                logger.debug("点赞按钮选择器 {} 失败: {}", selector, e)
        
        return elements
    
    def _find_repost_elements(self, page):
        """查找转发相关元素"""
        elements = {}
        
        repost_btn_selectors = [
            "button:has-text('转发')",
            "[role=button]:has-text('转发')",
            "button[title*='转发']",
            ".repost-btn",
            "[data-testid*='repost']"
        ]
        
        for i, selector in enumerate(repost_btn_selectors):
            try:
                elements_found = page.locator(selector).all()
                for j, elem in enumerate(elements_found):
                    if elem.is_visible():
                        element_info = {
                            "selector": selector,
                            "xpath": self._get_xpath(elem),
                            "text": elem.inner_text() or "",
                            "enabled": elem.is_enabled(),
                            "visible": elem.is_visible(),
                            "bounding_box": elem.bounding_box()
                        }
                        elements[f"repost_btn_{i}_{j}"] = element_info
                        logger.info("发现转发按钮: {} - {}", selector, element_info["text"])
            except Exception as e:
                logger.debug("转发按钮选择器 {} 失败: {}", selector, e)
        
        return elements
    
    def _find_follow_elements(self, page):
        """查找关注相关元素"""
        elements = {}
        
        follow_btn_selectors = [
            "button:has-text('关注')",
            "[role=button]:has-text('关注')",
            "a:has-text('关注')",
            ".follow-btn",
            "[data-testid*='follow']"
        ]
        
        for i, selector in enumerate(follow_btn_selectors):
            try:
                elements_found = page.locator(selector).all()
                for j, elem in enumerate(elements_found):
                    if elem.is_visible():
                        element_info = {
                            "selector": selector,
                            "xpath": self._get_xpath(elem),
                            "text": elem.inner_text() or "",
                            "enabled": elem.is_enabled(),
                            "visible": elem.is_visible(),
                            "bounding_box": elem.bounding_box()
                        }
                        elements[f"follow_btn_{i}_{j}"] = element_info
                        logger.info("发现关注按钮: {} - {}", selector, element_info["text"])
            except Exception as e:
                logger.debug("关注按钮选择器 {} 失败: {}", selector, e)
        
        return elements
    
    def _get_xpath(self, element):
        """获取元素的XPath"""
        try:
            # 这是一个简化的XPath获取，实际可能需要更复杂的逻辑
            return element.evaluate("el => { const getXPath = (element) => { if (element.id !== '') return 'id(\"' + element.id + '\")'; if (element === document.body) return element.tagName; let ix = 0; const siblings = element.parentNode.childNodes; for (let i = 0; i < siblings.length; i++) { const sibling = siblings[i]; if (sibling === element) return getXPath(element.parentNode) + '/' + element.tagName + '[' + (ix + 1) + ']'; if (sibling.nodeType === 1 && sibling.tagName === element.tagName) ix++; } }; return getXPath(el); }")
        except Exception:
            return ""
    
    def test_element_interaction(self, page, element_info: dict, operation: str):
        """测试元素交互"""
        try:
            selector = element_info["selector"]
            elem = page.locator(selector).first
            
            if operation == "click":
                elem.click()
                self.log_operation("click", element_info, True, f"成功点击元素: {selector}")
                return True
            elif operation == "type":
                elem.type("测试文本")
                self.log_operation("type", element_info, True, f"成功输入文本: {selector}")
                return True
                
        except Exception as e:
            self.log_operation(operation, element_info, False, f"操作失败: {e}")
            return False
    
    def save_results(self):
        """保存发现的元素信息"""
        # 保存元素信息
        elements_file = project_root / f"discovered_elements_{self.timestamp}.json"
        with open(elements_file, 'w', encoding='utf-8') as f:
            json.dump(self.discovered_elements, f, ensure_ascii=False, indent=2)
        
        # 保存操作日志
        log_file = project_root / f"operation_log_{self.timestamp}.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(self.operation_log, f, ensure_ascii=False, indent=2)
        
        logger.info("结果已保存:")
        logger.info("- 元素信息: {}", elements_file)
        logger.info("- 操作日志: {}", log_file)

def main():
    """主函数"""
    logger.info("启动全自动元素获取与分析工具")
    
    # 配置
    CONFIG.platform = "weibo"
    CONFIG.headless = False
    CONFIG.anti_detection_mode = "off"
    
    discovery = ElementDiscovery()
    bm = BrowserManager()
    
    try:
        bm.launch()
        bm.new_context(use_storage=True)
        page = bm.page
        assert page is not None
        
        # 确保登录
        ensure_login_weibo(page)
        
        # 1. 分析首页元素
        page.goto("https://weibo.com")
        page.wait_for_load_state("domcontentloaded")
        time.sleep(3)
        discovery.discover_page_elements(page, "weibo_home")
        
        # 2. 进入一个详情页分析
        logger.info("获取详情页链接...")
        cards = page.locator("article").all()
        if cards:
            # 获取第一个卡片的详情页链接
            time_links = cards[0].locator("time a").all()
            for link in time_links:
                href = link.get_attribute("href")
                if href and ("weibo.com" in href or "/status/" in href):
                    if href.startswith("/"):
                        detail_link = f"https://weibo.com{href}"
                    else:
                        detail_link = href
                    detail_link = detail_link.split("?")[0]
                    
                    logger.info("进入详情页: {}", detail_link)
                    page.goto(detail_link)
                    page.wait_for_load_state("domcontentloaded")
                    time.sleep(3)
                    discovery.discover_page_elements(page, "weibo_detail")
                    break
        
        # 保存结果
        discovery.save_results()
        
        logger.info("元素发现完成！")
        input("按回车键关闭浏览器...")
        
    except Exception as e:
        logger.exception("元素发现过程失败: {}", e)
    finally:
        bm.close()

if __name__ == "__main__":
    main()
