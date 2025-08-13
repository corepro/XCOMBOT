#!/usr/bin/env python3
"""
微博元素定位专项测试

专门测试智能元素定位系统的准确性和可靠性
验证各种选择器的有效性和fallback机制
"""

import sys
import time
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.browser import BrowserManager
from src.logger import logger
from src.config import CONFIG
from src.weibo import (
    ElementLocator, 
    FOLLOW_BUTTON_CONFIG,
    LIKE_BUTTON_CONFIG,
    COMMENT_BOX_CONFIG,
    REPOST_OPTION_CONFIG,
    SUBMIT_BUTTON_CONFIG,
    WEIBO_HOME
)
from src.login_weibo import is_logged_in_weibo


class ElementLocatorTester:
    """元素定位器测试类"""
    
    def __init__(self):
        self.test_results = {}
        
    def test_all_elements(self, page, recorder=None) -> dict:
        """测试所有关键元素的定位"""
        logger.info("🔍 开始元素定位专项测试")
        
        locator = ElementLocator(page, recorder)
        
        # 测试配置
        element_configs = {
            "关注按钮": FOLLOW_BUTTON_CONFIG,
            "点赞按钮": LIKE_BUTTON_CONFIG,
            "评论输入框": COMMENT_BOX_CONFIG,
            "转发选项": REPOST_OPTION_CONFIG,
            "提交按钮": SUBMIT_BUTTON_CONFIG
        }
        
        results = {
            "total_elements": len(element_configs),
            "successful_locations": 0,
            "failed_locations": 0,
            "element_details": {},
            "selector_effectiveness": {},
            "overall_success_rate": 0
        }
        
        for element_name, config in element_configs.items():
            logger.info("🎯 测试元素: {}", element_name)
            
            element_result = self._test_single_element(locator, element_name, config)
            results["element_details"][element_name] = element_result
            
            if element_result["found"]:
                results["successful_locations"] += 1
            else:
                results["failed_locations"] += 1
            
            # 统计选择器有效性
            if element_result["successful_selector"]:
                selector = element_result["successful_selector"]
                if selector not in results["selector_effectiveness"]:
                    results["selector_effectiveness"][selector] = {"success": 0, "total": 0}
                results["selector_effectiveness"][selector]["success"] += 1
                results["selector_effectiveness"][selector]["total"] += 1
        
        # 计算总体成功率
        if results["total_elements"] > 0:
            results["overall_success_rate"] = (results["successful_locations"] / results["total_elements"]) * 100
        
        return results
    
    def _test_single_element(self, locator: ElementLocator, element_name: str, config: dict) -> dict:
        """测试单个元素的定位"""
        start_time = time.time()
        
        element, selector, found = locator.find_element_with_fallback(config, timeout=8)
        
        end_time = time.time()
        
        result = {
            "found": found,
            "successful_selector": selector if found else None,
            "search_time": end_time - start_time,
            "element_visible": False,
            "element_enabled": False,
            "element_text": "",
            "selector_attempts": len(config.get("selectors", [])),
            "error": None
        }
        
        if found and element:
            try:
                result["element_visible"] = element.is_visible()
                result["element_enabled"] = element.is_enabled()
                
                # 获取元素文本
                try:
                    text = element.inner_text() or element.text_content() or ""
                    result["element_text"] = text[:50] + "..." if len(text) > 50 else text
                except:
                    pass
                    
                logger.info("✅ {} 定位成功: {} ({})", element_name, selector, result["element_text"])
                
            except Exception as e:
                result["error"] = str(e)
                logger.warning("⚠️ {} 元素验证失败: {}", element_name, str(e))
        else:
            logger.error("❌ {} 定位失败", element_name)
        
        return result
    
    def test_selector_priority(self, page, config: dict) -> dict:
        """测试选择器优先级和有效性"""
        logger.info("📊 测试选择器优先级: {}", config.get("name", "未知元素"))
        
        locator = ElementLocator(page)
        selectors = config.get("selectors", [])
        
        results = {
            "total_selectors": len(selectors),
            "working_selectors": [],
            "failed_selectors": [],
            "first_working_index": -1,
            "selector_details": {}
        }
        
        for i, selector in enumerate(selectors):
            logger.debug("测试选择器 {}/{}: {}", i+1, len(selectors), selector)
            
            start_time = time.time()
            
            try:
                if selector.startswith("//"):
                    locator_obj = page.locator(f"xpath={selector}")
                else:
                    locator_obj = page.locator(selector)
                
                # 等待元素出现
                try:
                    locator_obj.first.wait_for(state="attached", timeout=1000)
                    elements = locator_obj.all()
                    
                    working_elements = 0
                    for element in elements:
                        if element.is_visible() and element.is_enabled():
                            working_elements += 1
                    
                    if working_elements > 0:
                        results["working_selectors"].append({
                            "index": i,
                            "selector": selector,
                            "element_count": working_elements,
                            "response_time": time.time() - start_time
                        })
                        
                        if results["first_working_index"] == -1:
                            results["first_working_index"] = i
                        
                        logger.debug("✅ 选择器有效: {} ({} 个元素)", selector, working_elements)
                    else:
                        results["failed_selectors"].append({
                            "index": i,
                            "selector": selector,
                            "reason": "no_visible_elements"
                        })
                        logger.debug("❌ 选择器无效: {} (无可见元素)", selector)
                        
                except Exception as e:
                    results["failed_selectors"].append({
                        "index": i,
                        "selector": selector,
                        "reason": f"timeout_or_error: {str(e)}"
                    })
                    logger.debug("❌ 选择器失败: {} ({})", selector, str(e))
                    
            except Exception as e:
                results["failed_selectors"].append({
                    "index": i,
                    "selector": selector,
                    "reason": f"syntax_error: {str(e)}"
                })
                logger.debug("❌ 选择器语法错误: {} ({})", selector, str(e))
        
        return results
    
    def generate_locator_report(self, test_results: dict) -> str:
        """生成元素定位测试报告"""
        
        report = []
        report.append("=" * 70)
        report.append("🔍 微博元素定位专项测试报告")
        report.append("=" * 70)
        report.append("")
        
        # 总体统计
        report.append("📊 总体统计:")
        report.append(f"   测试元素数量: {test_results['total_elements']}")
        report.append(f"   成功定位: {test_results['successful_locations']}")
        report.append(f"   定位失败: {test_results['failed_locations']}")
        report.append(f"   总体成功率: {test_results['overall_success_rate']:.1f}%")
        report.append("")
        
        # 各元素详情
        report.append("🎯 各元素定位详情:")
        for element_name, details in test_results["element_details"].items():
            status = "✅" if details["found"] else "❌"
            report.append(f"   {element_name}: {status}")
            
            if details["found"]:
                report.append(f"      成功选择器: {details['successful_selector']}")
                report.append(f"      搜索耗时: {details['search_time']:.3f}s")
                report.append(f"      元素可见: {'是' if details['element_visible'] else '否'}")
                report.append(f"      元素可用: {'是' if details['element_enabled'] else '否'}")
                if details["element_text"]:
                    report.append(f"      元素文本: {details['element_text']}")
            else:
                report.append(f"      失败原因: 未找到匹配元素")
                report.append(f"      尝试选择器数: {details['selector_attempts']}")
                if details["error"]:
                    report.append(f"      错误信息: {details['error']}")
            report.append("")
        
        # 选择器有效性统计
        if test_results["selector_effectiveness"]:
            report.append("📈 选择器有效性统计:")
            sorted_selectors = sorted(
                test_results["selector_effectiveness"].items(),
                key=lambda x: x[1]["success"],
                reverse=True
            )
            
            for selector, stats in sorted_selectors[:10]:  # 显示前10个最有效的选择器
                success_rate = (stats["success"] / stats["total"]) * 100
                report.append(f"   {selector}: {success_rate:.1f}% ({stats['success']}/{stats['total']})")
            report.append("")
        
        # 建议和改进
        report.append("💡 建议和改进:")
        
        success_rate = test_results['overall_success_rate']
        if success_rate >= 95:
            report.append("   ✅ 元素定位系统表现优秀，无需改进")
        elif success_rate >= 80:
            report.append("   ⚠️ 元素定位系统表现良好，建议优化失败的元素")
        else:
            report.append("   ❌ 元素定位系统需要重大改进")
        
        # 针对失败元素的建议
        failed_elements = [name for name, details in test_results["element_details"].items() if not details["found"]]
        if failed_elements:
            report.append(f"   需要改进的元素: {', '.join(failed_elements)}")
            report.append("   建议: 添加更多选择器或更新现有选择器")
        
        report.append("")
        report.append("=" * 70)
        
        return "\n".join(report)


def main():
    """主函数"""
    logger.info("🚀 启动微博元素定位专项测试")
    
    # 设置配置
    CONFIG.headless = False  # 可视化模式便于调试
    CONFIG.slow_mo_ms = 100
    
    bm = BrowserManager()
    
    try:
        # 启动浏览器
        bm.launch()
        bm.new_context(use_storage=True)
        page = bm.page
        
        # 检查登录状态
        page.goto(WEIBO_HOME)
        page.wait_for_load_state("domcontentloaded")
        
        if not is_logged_in_weibo(page):
            logger.error("❌ 未登录，请先登录微博")
            return False
        
        logger.info("✅ 登录状态正常，开始元素定位测试...")
        
        # 进入一个微博详情页进行测试
        # 这里可以手动导航到一个具体的微博详情页，或者使用现有的逻辑
        
        # 执行元素定位测试
        tester = ElementLocatorTester()
        results = tester.test_all_elements(page)
        
        # 生成并显示报告
        report = tester.generate_locator_report(results)
        print(report)
        
        # 保存报告
        report_file = f"element_locator_test_report_{int(time.time())}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info("📄 测试报告已保存到: {}", report_file)
        
        # 判断测试是否成功
        success = results["overall_success_rate"] >= 95
        if success:
            logger.info("🎉 元素定位测试通过！")
        else:
            logger.warning("⚠️ 元素定位测试未完全通过")
        
        return success
        
    except Exception as e:
        logger.error("❌ 测试异常: {}", str(e))
        return False
        
    finally:
        # 保持浏览器打开5秒观察结果
        time.sleep(5)
        bm.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
