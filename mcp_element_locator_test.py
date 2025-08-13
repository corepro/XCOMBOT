#!/usr/bin/env python3
"""
微博自动化MCP元素定位测试系统

使用Playwright MCP (Model Context Protocol) 系统性验证元素定位准确性
目标：实现100%的元素定位成功率
"""

import sys
import time
import json
import traceback
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.browser import BrowserManager
from src.logger import logger
from src.config import CONFIG
from src.weibo import WEIBO_HOME
from src.login_weibo import is_logged_in_weibo


class MCPElementLocatorTest:
    """MCP元素定位测试系统"""
    
    def __init__(self):
        self.test_results = {}
        self.optimization_history = []
        self.current_iteration = 0
        self.max_iterations = 5
        
        # 当前测试的选择器配置
        self.current_selectors = {
            "关注按钮": {
                "primary": "/html/body/div[1]/div[2]/div[2]/div[2]/main/div[1]/div/div[2]/article/div[2]/header/div[2]/button",
                "fallbacks": [
                    "button:has-text('+关注')",
                    "button:has-text('+ 关注')",
                    "button:has-text('关注'):not(:has-text('已关注'))",
                    "[role=button]:has-text('关注'):not(:has-text('已关注'))",
                    "//button[contains(text(), '+关注')]",
                    "//button[contains(text(), '关注') and not(contains(text(), '已关注'))]"
                ],
                "verify_text": ["关注", "+关注", "+ 关注"],
                "exclude_text": ["已关注", "取消关注"]
            },
            "点赞按钮": {
                "primary": "//*[@id=\"app\"]/div[2]/div[2]/div[2]/main/div[1]/div/div[2]/article/footer/div/div[1]/div/div[3]/div/button",
                "fallbacks": [
                    "button:has-text('赞')",
                    "button[aria-label*='赞']",
                    "button[title*='赞']",
                    ".like-btn",
                    "[data-testid*='like']",
                    "//button[contains(@aria-label, '赞')]",
                    "//button[contains(text(), '赞')]"
                ],
                "verify_text": ["赞", "like"],
                "exclude_text": ["已赞", "取消赞"]
            },
            "评论输入框": {
                "primary": "textarea[placeholder*='评论']",
                "fallbacks": [
                    "textarea[placeholder*='说点什么']",
                    "textarea[placeholder*='写评论']",
                    ".comment-input textarea",
                    ".comment-box textarea",
                    "textarea",
                    "[contenteditable='true']",
                    "//textarea[contains(@placeholder, '评论')]"
                ],
                "verify_text": [],
                "exclude_text": []
            },
            "转发选项": {
                "primary": "//*[@id=\"composerEle\"]/div[2]/div/div[3]/div/div[2]/label",
                "fallbacks": [
                    "span:has-text('同时转发')",
                    "label:has-text('同时转发')",
                    "input[type='checkbox']:has-text('同时转发')",
                    "label:has-text('同时转发') input[type='checkbox']",
                    "//span[contains(text(), '同时转发')]",
                    "//label[contains(text(), '同时转发')]"
                ],
                "verify_text": ["同时转发", "转发"],
                "exclude_text": []
            },
            "提交按钮": {
                "primary": "button:has-text('发布')",
                "fallbacks": [
                    "button:has-text('评论')",
                    "button:has-text('发送')",
                    "button:has-text('提交')",
                    ".submit-btn",
                    ".comment-submit",
                    "button[type='submit']",
                    "//button[contains(text(), '发布')]",
                    "//button[contains(text(), '评论')]"
                ],
                "verify_text": ["发布", "评论", "发送"],
                "exclude_text": ["取消", "删除"]
            },
            "微博内容": {
                "primary": "//*[@id=\"app\"]/div[2]/div[2]/div[2]/main/div[1]/div/div[2]/article/div[2]/div/div[1]/div",
                "fallbacks": [
                    "//*[@id='scroller']/div[1]/div[1]/div/article/div/div[1]/div[1]/div",
                    "article .txt",
                    "article [node-type='feed_list_content']",
                    ".detail-content .txt",
                    ".post-content"
                ],
                "verify_text": [],
                "exclude_text": []
            }
        }
    
    def run_mcp_test_cycle(self) -> Dict:
        """运行完整的MCP测试周期"""
        logger.info("🚀 开始MCP元素定位测试周期")
        
        cycle_results = {
            "iteration": self.current_iteration + 1,
            "timestamp": time.time(),
            "element_tests": {},
            "overall_success_rate": 0,
            "optimization_applied": False,
            "next_actions": []
        }
        
        # 设置测试环境
        CONFIG.headless = False
        CONFIG.slow_mo_ms = 200
        
        bm = BrowserManager()
        
        try:
            # 启动浏览器并检查登录
            bm.launch()
            bm.new_context(use_storage=True)
            page = bm.page
            
            page.goto(WEIBO_HOME)
            page.wait_for_load_state("domcontentloaded")
            
            if not is_logged_in_weibo(page):
                logger.error("❌ 未登录，请先登录微博")
                cycle_results["error"] = "not_logged_in"
                return cycle_results
            
            logger.info("✅ 登录状态正常，开始元素定位测试")
            time.sleep(3)  # 等待页面完全加载
            
            # 逐个测试每个元素
            total_elements = len(self.current_selectors)
            successful_elements = 0
            
            for element_name, config in self.current_selectors.items():
                logger.info("🎯 测试元素: {}", element_name)
                
                element_result = self._test_single_element_mcp(page, element_name, config)
                cycle_results["element_tests"][element_name] = element_result
                
                if element_result["success"]:
                    successful_elements += 1
                    logger.info("✅ {} 定位成功", element_name)
                else:
                    logger.error("❌ {} 定位失败: {}", element_name, element_result.get("error"))
                
                time.sleep(1)  # 元素间测试间隔
            
            # 计算总体成功率
            cycle_results["overall_success_rate"] = (successful_elements / total_elements) * 100
            
            # 记录测试结果
            self.test_results[f"iteration_{self.current_iteration + 1}"] = cycle_results
            
            logger.info("📊 本轮测试完成，成功率: {:.1f}% ({}/{})", 
                       cycle_results["overall_success_rate"], successful_elements, total_elements)
            
        except Exception as e:
            logger.error("❌ MCP测试周期异常: {}", str(e))
            cycle_results["error"] = str(e)
            cycle_results["traceback"] = traceback.format_exc()
            
        finally:
            # 保持浏览器打开观察结果
            logger.info("🔍 保持浏览器打开5秒观察结果...")
            time.sleep(5)
            bm.close()
        
        return cycle_results
    
    def _test_single_element_mcp(self, page, element_name: str, config: Dict) -> Dict:
        """使用MCP协议测试单个元素"""
        
        result = {
            "element_name": element_name,
            "success": False,
            "successful_selector": None,
            "selector_type": None,
            "attempts": [],
            "element_info": {},
            "optimization_suggestions": [],
            "error": None
        }
        
        # 构建完整的选择器列表
        all_selectors = [config["primary"]] + config["fallbacks"]
        
        for i, selector in enumerate(all_selectors):
            attempt = {
                "index": i,
                "selector": selector,
                "type": "primary" if i == 0 else "fallback",
                "success": False,
                "response_time": 0,
                "error": None
            }
            
            start_time = time.time()
            
            try:
                logger.debug("   尝试选择器 {}/{}: {}", i+1, len(all_selectors), selector)
                
                # 根据选择器类型进行定位
                if selector.startswith("//") or selector.startswith("/html"):
                    # XPath选择器
                    element = page.query_selector(f"xpath={selector}")
                    attempt["selector_method"] = "xpath"
                else:
                    # CSS选择器
                    element = page.query_selector(selector)
                    attempt["selector_method"] = "css"
                
                attempt["response_time"] = time.time() - start_time
                
                if element:
                    # 验证元素状态
                    element_valid = self._validate_element_mcp(element, config, element_name)
                    
                    if element_valid["valid"]:
                        attempt["success"] = True
                        result["success"] = True
                        result["successful_selector"] = selector
                        result["selector_type"] = attempt["type"]
                        result["element_info"] = element_valid["info"]
                        
                        logger.debug("   ✅ 选择器成功: {}", selector)
                        break
                    else:
                        attempt["validation_failed"] = element_valid["reason"]
                        logger.debug("   ⚠️ 元素找到但验证失败: {}", element_valid["reason"])
                else:
                    attempt["error"] = "element_not_found"
                    logger.debug("   ❌ 元素未找到")
                    
            except Exception as e:
                attempt["error"] = str(e)
                attempt["response_time"] = time.time() - start_time
                logger.debug("   ❌ 选择器异常: {}", str(e))
            
            result["attempts"].append(attempt)
        
        # 如果所有选择器都失败，生成优化建议
        if not result["success"]:
            result["optimization_suggestions"] = self._generate_optimization_suggestions(result, element_name)
            result["error"] = "all_selectors_failed"
        
        return result
    
    def _validate_element_mcp(self, element, config: Dict, element_name: str) -> Dict:
        """使用MCP协议验证元素有效性"""
        
        validation = {
            "valid": False,
            "reason": "",
            "info": {}
        }
        
        try:
            # 基本状态检查
            is_visible = element.is_visible()
            is_attached = element.is_attached()
            is_enabled = element.is_enabled() if hasattr(element, 'is_enabled') else True
            
            validation["info"] = {
                "visible": is_visible,
                "attached": is_attached,
                "enabled": is_enabled,
                "text": "",
                "position": None
            }
            
            # 获取元素文本
            try:
                text = element.inner_text() or element.text_content() or ""
                validation["info"]["text"] = text[:100] + "..." if len(text) > 100 else text
            except:
                pass
            
            # 获取元素位置
            try:
                box = element.bounding_box()
                if box:
                    validation["info"]["position"] = {
                        "x": box["x"], "y": box["y"], 
                        "width": box["width"], "height": box["height"]
                    }
            except:
                pass
            
            # 验证基本状态
            if not is_attached:
                validation["reason"] = "element_not_attached"
                return validation
            
            if not is_visible:
                validation["reason"] = "element_not_visible"
                return validation
            
            # 文本验证
            verify_text = config.get("verify_text", [])
            exclude_text = config.get("exclude_text", [])
            element_text = validation["info"]["text"].lower()
            
            if verify_text:
                text_match = any(text.lower() in element_text for text in verify_text)
                if not text_match:
                    validation["reason"] = f"text_not_match_expected: {verify_text}"
                    return validation
            
            if exclude_text:
                text_exclude = any(text.lower() in element_text for text in exclude_text)
                if text_exclude:
                    validation["reason"] = f"text_contains_excluded: {exclude_text}"
                    return validation
            
            # 特殊元素验证
            if element_name == "微博内容":
                if len(element_text.strip()) < 10:
                    validation["reason"] = "content_too_short"
                    return validation
            
            validation["valid"] = True
            
        except Exception as e:
            validation["reason"] = f"validation_exception: {str(e)}"
        
        return validation
    
    def _generate_optimization_suggestions(self, result: Dict, element_name: str) -> List[str]:
        """生成优化建议"""
        
        suggestions = []
        
        # 分析失败模式
        attempts = result["attempts"]
        
        # 检查是否有元素找到但验证失败的情况
        found_but_invalid = [a for a in attempts if "validation_failed" in a]
        if found_but_invalid:
            suggestions.append(f"调整{element_name}的文本验证条件")
            suggestions.append("检查元素状态要求是否过于严格")
        
        # 检查响应时间
        slow_selectors = [a for a in attempts if a["response_time"] > 2.0]
        if slow_selectors:
            suggestions.append("优化慢速选择器，考虑更精确的定位方式")
        
        # 检查XPath vs CSS选择器成功率
        xpath_attempts = [a for a in attempts if a.get("selector_method") == "xpath"]
        css_attempts = [a for a in attempts if a.get("selector_method") == "css"]
        
        if xpath_attempts and not any(a["success"] for a in xpath_attempts):
            suggestions.append("XPath选择器全部失败，可能需要更新路径")
        
        if css_attempts and not any(a["success"] for a in css_attempts):
            suggestions.append("CSS选择器全部失败，考虑使用更稳定的属性选择器")
        
        # 通用建议
        suggestions.append(f"为{element_name}添加更多备选选择器")
        suggestions.append("检查页面结构是否发生变化")
        
        return suggestions


def main():
    """主函数"""
    logger.info("🚀 启动MCP元素定位测试系统")
    
    tester = MCPElementLocatorTest()
    
    # 运行测试周期
    cycle_result = tester.run_mcp_test_cycle()
    
    # 生成详细报告
    generate_mcp_test_report(cycle_result)
    
    # 判断是否需要优化
    success_rate = cycle_result.get("overall_success_rate", 0)
    
    if success_rate >= 100:
        logger.info("🎉 MCP测试完美通过！所有元素100%定位成功")
        return True
    elif success_rate >= 80:
        logger.info("⚠️ MCP测试基本通过，但仍有优化空间")
        return True
    else:
        logger.warning("❌ MCP测试未通过，需要进行优化")
        return False


def generate_mcp_test_report(result: Dict):
    """生成MCP测试报告"""
    
    report = []
    report.append("=" * 80)
    report.append("🧪 微博自动化MCP元素定位测试报告")
    report.append("=" * 80)
    report.append("")
    
    # 基本信息
    report.append(f"📊 测试轮次: {result.get('iteration', 'N/A')}")
    report.append(f"⏰ 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(result.get('timestamp', time.time())))}")
    report.append(f"🎯 总体成功率: {result.get('overall_success_rate', 0):.1f}%")
    report.append("")
    
    # 详细元素测试结果
    element_tests = result.get("element_tests", {})
    if element_tests:
        report.append("🔍 详细元素测试结果:")
        
        for element_name, element_result in element_tests.items():
            status = "✅" if element_result["success"] else "❌"
            report.append(f"   {element_name}: {status}")
            
            if element_result["success"]:
                report.append(f"      成功选择器: {element_result['successful_selector']}")
                report.append(f"      选择器类型: {element_result['selector_type']}")
                
                info = element_result.get("element_info", {})
                if info:
                    report.append(f"      元素状态: 可见={info.get('visible')}, 可用={info.get('enabled')}")
                    if info.get("text"):
                        report.append(f"      元素文本: {info['text'][:50]}...")
            else:
                report.append(f"      失败原因: {element_result.get('error', '未知')}")
                
                # 显示尝试的选择器数量
                attempts = element_result.get("attempts", [])
                report.append(f"      尝试选择器数: {len(attempts)}")
                
                # 显示优化建议
                suggestions = element_result.get("optimization_suggestions", [])
                if suggestions:
                    report.append("      优化建议:")
                    for suggestion in suggestions[:3]:  # 只显示前3个建议
                        report.append(f"        - {suggestion}")
            
            report.append("")
    
    # 总体建议
    success_rate = result.get("overall_success_rate", 0)
    report.append("💡 总体建议:")
    
    if success_rate >= 100:
        report.append("   🎉 完美！所有元素都能成功定位")
        report.append("   ✅ 可以进入下一阶段：操作流程测试")
    elif success_rate >= 80:
        report.append("   ⚠️ 大部分元素定位成功，建议优化失败的元素")
        report.append("   🔧 重点关注失败元素的选择器配置")
    else:
        report.append("   ❌ 元素定位成功率较低，需要全面优化")
        report.append("   🔧 建议重新检查页面结构和选择器配置")
    
    report.append("")
    report.append("=" * 80)
    
    report_text = "\n".join(report)
    print(report_text)
    
    # 保存报告
    report_file = f"mcp_element_test_report_{int(time.time())}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    logger.info("📄 MCP测试报告已保存到: {}", report_file)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
