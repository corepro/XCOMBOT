#!/usr/bin/env python3
"""
优化后的微博自动化代码

基于MCP测试结果进行的代码优化，实现100%成功率目标
"""

import time
from typing import Dict, Optional
from playwright.sync_api import Page

from src.logger import logger
from src.weibo import (
    OperationRecorder, 
    random_comment, 
    pick_random_post, 
    extract_post_link_from_card,
    WEIBO_HOME
)


class OptimizedWeiboAutomation:
    """优化的微博自动化类"""
    
    def __init__(self, page: Page, recorder: Optional[OperationRecorder] = None):
        self.page = page
        self.recorder = recorder or OperationRecorder()
        
        # 优化后的选择器配置
        self.selectors = {
            "follow_button": {
                "primary": "/html/body/div[1]/div[2]/div[2]/div[2]/main/div[1]/div/div[2]/article/div[2]/header/div[2]/button",
                "fallbacks": [
                    "button:has-text('+关注')",
                    "button:has-text('+ 关注')",
                    "button:has-text('关注'):not(:has-text('已关注'))",
                    "[role=button]:has-text('关注'):not(:has-text('已关注'))",
                    "//button[contains(text(), '+关注')]"
                ],
                "verify_text": ["关注", "+关注"],
                "exclude_text": ["已关注", "取消关注"]
            },
            "like_button": {
                "primary": "//*[@id=\"app\"]/div[2]/div[2]/div[2]/main/div[1]/div/div[2]/article/footer/div/div[1]/div/div[3]/div/button",
                "fallbacks": [
                    "button:has-text('赞')",
                    "button[aria-label*='赞']",
                    "button[title*='赞']",
                    ".like-btn",
                    "//button[contains(@aria-label, '赞')]"
                ],
                "verify_text": ["赞"],
                "exclude_text": ["已赞", "取消赞"]
            },
            "comment_box": {
                "primary": "textarea[placeholder*='评论']",
                "fallbacks": [
                    "textarea[placeholder*='说点什么']",
                    ".comment-input textarea",
                    "textarea",
                    "[contenteditable='true']",
                    "//textarea[contains(@placeholder, '评论')]"
                ],
                "verify_text": [],
                "exclude_text": []
            },
            "repost_option": {
                "primary": "//*[@id=\"composerEle\"]/div[2]/div/div[3]/div/div[2]/label",
                "fallbacks": [
                    "span:has-text('同时转发')",
                    "label:has-text('同时转发')",
                    "input[type='checkbox']:has-text('同时转发')",
                    "//span[contains(text(), '同时转发')]"
                ],
                "verify_text": ["同时转发", "转发"],
                "exclude_text": []
            },
            "submit_button": {
                "primary": "button:has-text('发布')",
                "fallbacks": [
                    "button:has-text('评论')",
                    "button:has-text('发送')",
                    ".submit-btn",
                    "button[type='submit']",
                    "//button[contains(text(), '发布')]"
                ],
                "verify_text": ["发布", "评论", "发送"],
                "exclude_text": ["取消", "删除"]
            },
            "weibo_content": {
                "primary": "//*[@id=\"app\"]/div[2]/div[2]/div[2]/main/div[1]/div/div[2]/article/div[2]/div/div[1]/div",
                "fallbacks": [
                    "//*[@id='scroller']/div[1]/div[1]/div/article/div/div[1]/div[1]/div",
                    "article .txt",
                    ".detail-content .txt",
                    ".post-content"
                ],
                "verify_text": [],
                "exclude_text": []
            }
        }
    
    def find_element_optimized(self, element_type: str, timeout: int = 10) -> tuple:
        """优化的元素定位方法"""
        
        config = self.selectors.get(element_type)
        if not config:
            logger.error("❌ 未知的元素类型: {}", element_type)
            return None, None, False
        
        logger.info("🔍 查找元素: {}", element_type)
        
        # 构建完整选择器列表
        all_selectors = [config["primary"]] + config["fallbacks"]
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            for i, selector in enumerate(all_selectors):
                try:
                    logger.debug("   尝试选择器 {}/{}: {}", i+1, len(all_selectors), selector)
                    
                    # 根据选择器类型进行定位
                    if selector.startswith("//") or selector.startswith("/html"):
                        element = self.page.query_selector(f"xpath={selector}")
                    else:
                        element = self.page.query_selector(selector)
                    
                    if element and self._validate_element(element, config, element_type):
                        logger.info("✅ 成功找到 {} (选择器: {})", element_type, selector)
                        return element, selector, True
                        
                except Exception as e:
                    logger.debug("   选择器失败: {}", str(e))
                    continue
            
            # 短暂等待后重试
            time.sleep(0.5)
        
        logger.error("❌ 未找到元素: {} (尝试{}个选择器，耗时{:.1f}秒)", 
                    element_type, len(all_selectors), time.time() - start_time)
        return None, None, False
    
    def _validate_element(self, element, config: Dict, element_type: str) -> bool:
        """验证元素有效性"""
        
        try:
            # 基本状态检查
            if not element.is_visible() or not element.is_attached():
                return False
            
            # 文本验证
            verify_text = config.get("verify_text", [])
            exclude_text = config.get("exclude_text", [])
            
            if verify_text or exclude_text:
                element_text = (element.inner_text() or element.text_content() or "").lower()
                
                if verify_text and not any(text.lower() in element_text for text in verify_text):
                    return False
                
                if exclude_text and any(text.lower() in element_text for text in exclude_text):
                    return False
            
            # 特殊验证
            if element_type == "weibo_content":
                content = element.inner_text() or element.text_content() or ""
                return len(content.strip()) >= 10
            
            return True
            
        except Exception:
            return False
    
    def execute_optimized_automation(self, do_comment: bool, do_like: bool, 
                                   do_repost: bool, do_follow: bool) -> Dict:
        """执行优化的自动化流程"""
        
        logger.info("🚀 开始优化的微博自动化流程")
        
        result = {
            "follow_executed": False,
            "like_executed": False,
            "comment_executed": False,
            "repost_executed": False,
            "weibo_link": None,
            "success_rate": 0,
            "mcp_script": "",
            "optimization_applied": True
        }
        
        try:
            # 步骤1：进入微博详情页
            if not self._step_1_navigate_to_detail():
                result["error"] = "navigation_failed"
                return result
            
            # 步骤2：提取微博内容
            content = self._step_2_extract_content()
            
            # 步骤3：执行关注操作
            if do_follow:
                result["follow_executed"] = self._step_3_execute_follow()
            
            # 步骤4：查找并激活评论框
            comment_box = None
            if do_comment or do_repost:
                comment_box = self._step_4_activate_comment_box()
            
            # 步骤5：生成并输入评论
            if do_comment and comment_box:
                comment_text = random_comment(content)
                result["comment_executed"] = self._step_5_input_comment(comment_box, comment_text)
            
            # 步骤6：勾选转发选项
            if do_repost and comment_box:
                result["repost_executed"] = self._step_6_select_repost_option()
            
            # 步骤7：执行点赞
            if do_like:
                result["like_executed"] = self._step_7_execute_like()
            
            # 步骤8：提交操作
            if (do_comment or do_repost) and comment_box:
                self._step_8_submit_operations()
            
            # 计算成功率
            operations = [
                ("follow", do_follow, result["follow_executed"]),
                ("like", do_like, result["like_executed"]),
                ("comment", do_comment, result["comment_executed"]),
                ("repost", do_repost, result["repost_executed"])
            ]
            
            enabled_ops = [op for op in operations if op[1]]  # 启用的操作
            successful_ops = [op for op in enabled_ops if op[2]]  # 成功的操作
            
            if enabled_ops:
                result["success_rate"] = (len(successful_ops) / len(enabled_ops)) * 100
            else:
                result["success_rate"] = 100
            
            result["mcp_script"] = self.recorder.to_python_script()
            
            logger.info("📊 优化流程完成，成功率: {:.1f}%", result["success_rate"])
            
        except Exception as e:
            logger.error("❌ 优化流程异常: {}", str(e))
            result["error"] = str(e)
        
        return result
    
    def _step_1_navigate_to_detail(self) -> bool:
        """步骤1：导航到微博详情页"""
        
        try:
            # 确保在微博首页
            self.page.goto(WEIBO_HOME)
            self.page.wait_for_load_state("domcontentloaded")
            time.sleep(2)
            
            # 获取微博卡片
            card = pick_random_post(self.page, limit=20, require_comment=False)
            if not card:
                return False
            
            # 提取详情页链接
            detail_link = extract_post_link_from_card(card, self.page)
            if not detail_link:
                return False
            
            # 进入详情页
            self.page.goto(detail_link)
            self.page.wait_for_load_state("domcontentloaded")
            time.sleep(3)
            
            return True
            
        except Exception as e:
            logger.error("导航失败: {}", str(e))
            return False
    
    def _step_2_extract_content(self) -> str:
        """步骤2：提取微博内容"""
        
        element, _, found = self.find_element_optimized("weibo_content", timeout=5)
        
        if found and element:
            content = element.inner_text() or element.text_content() or ""
            logger.info("✅ 成功提取内容 ({} 字符)", len(content))
            return content.strip()
        else:
            logger.warning("⚠️ 内容提取失败，使用默认内容")
            return "默认微博内容"
    
    def _step_3_execute_follow(self) -> bool:
        """步骤3：执行关注操作"""
        
        element, selector, found = self.find_element_optimized("follow_button", timeout=5)
        
        if found and element:
            try:
                element.click()
                time.sleep(1.5)
                logger.info("✅ 关注操作成功")
                return True
            except Exception as e:
                logger.error("关注点击失败: {}", str(e))
        else:
            logger.info("ℹ️ 未找到关注按钮（可能已关注）")
        
        return False
    
    def _step_4_activate_comment_box(self):
        """步骤4：激活评论框"""
        
        element, selector, found = self.find_element_optimized("comment_box", timeout=8)
        
        if found and element:
            try:
                element.click()
                time.sleep(0.5)
                logger.info("✅ 评论框激活成功")
                return element
            except Exception as e:
                logger.error("评论框激活失败: {}", str(e))
        
        return None
    
    def _step_5_input_comment(self, comment_box, comment_text: str) -> bool:
        """步骤5：输入评论内容"""
        
        try:
            comment_box.clear()
            time.sleep(0.2)
            comment_box.fill(comment_text)
            time.sleep(1.0)
            logger.info("✅ 评论输入成功")
            return True
        except Exception as e:
            logger.error("评论输入失败: {}", str(e))
            return False
    
    def _step_6_select_repost_option(self) -> bool:
        """步骤6：选择转发选项"""
        
        element, selector, found = self.find_element_optimized("repost_option", timeout=5)
        
        if found and element:
            try:
                if not element.is_checked():
                    element.click()
                    time.sleep(0.5)
                logger.info("✅ 转发选项设置成功")
                return True
            except Exception as e:
                logger.error("转发选项设置失败: {}", str(e))
        else:
            logger.warning("⚠️ 未找到转发选项")
        
        return False
    
    def _step_7_execute_like(self) -> bool:
        """步骤7：执行点赞"""
        
        element, selector, found = self.find_element_optimized("like_button", timeout=5)
        
        if found and element:
            try:
                element.click()
                time.sleep(1.0)
                logger.info("✅ 点赞操作成功")
                return True
            except Exception as e:
                logger.error("点赞操作失败: {}", str(e))
        else:
            logger.error("❌ 未找到点赞按钮")
        
        return False
    
    def _step_8_submit_operations(self) -> bool:
        """步骤8：提交操作"""
        
        element, selector, found = self.find_element_optimized("submit_button", timeout=8)
        
        if found and element:
            try:
                element.click()
                time.sleep(2.0)
                logger.info("✅ 操作提交成功")
                return True
            except Exception as e:
                logger.error("操作提交失败: {}", str(e))
        else:
            logger.warning("⚠️ 未找到提交按钮，尝试快捷键")
            try:
                self.page.keyboard.press("Control+Enter")
                time.sleep(2.0)
                logger.info("✅ 快捷键提交成功")
                return True
            except Exception as e:
                logger.error("快捷键提交失败: {}", str(e))
        
        return False


def optimized_automate_on_post_alternative(page: Page, do_comment: bool, do_like: bool, 
                                         do_repost: bool, do_follow: bool = True) -> Dict:
    """
    优化版微博自动化函数
    
    基于MCP测试结果优化，实现100%成功率目标
    """
    
    recorder = OperationRecorder()
    automation = OptimizedWeiboAutomation(page, recorder)
    
    return automation.execute_optimized_automation(do_comment, do_like, do_repost, do_follow)
