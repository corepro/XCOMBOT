#!/usr/bin/env python3
"""
XPath优化测试脚本

测试用户提供的精确XPath选择器的有效性和优化效果
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
from src.weibo import automate_on_post, WEIBO_HOME
from src.login_weibo import is_logged_in_weibo


def test_xpath_selectors():
    """测试XPath选择器的有效性"""
    
    logger.info("🧪 开始测试XPath选择器优化")
    
    test_results = {
        "timestamp": time.time(),
        "xpath_tests": {
            "follow_button": {"found": False, "xpath": "", "error": None},
            "like_button": {"found": False, "xpath": "", "error": None},
            "comment_box": {"found": False, "xpath": "", "error": None}
        },
        "automation_test": {
            "success": False,
            "operations": {},
            "execution_time": 0,
            "error": None
        }
    }
    
    # 用户提供的精确XPath选择器
    xpath_selectors = {
        "follow_button": "//*[@id=\"app\"]/div[2]/div[2]/div[2]/main/div[1]/div/div[2]/article/div[2]/header/div[2]/button",
        "like_button": "//*[@id=\"app\"]/div[2]/div[2]/div[2]/main/div/div/div[2]/article/footer/div/div[1]/div/div[3]/div/button",
        "comment_box": "textarea[placeholder*='评论']"
    }
    
    bm = BrowserManager()
    
    try:
        # 启动浏览器
        bm.launch()
        bm.new_context(use_storage=True)
        page = bm.page
        
        # 检查登录状态
        page.goto(WEIBO_HOME)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(3)
        
        if not is_logged_in_weibo(page):
            logger.error("❌ 未登录，请先登录微博")
            print("\n🔑 请在浏览器中完成登录，然后按回车继续...")
            input("登录完成后按回车键继续...")
            
            page.reload()
            page.wait_for_load_state("domcontentloaded")
            time.sleep(2)
            
            if not is_logged_in_weibo(page):
                logger.error("❌ 登录验证失败")
                return test_results
        
        logger.info("✅ 登录状态验证通过")
        
        # 进入一个微博详情页进行测试
        logger.info("🔍 寻找微博详情页进行测试...")
        
        # 尝试点击第一个微博进入详情页
        try:
            # 等待页面加载
            time.sleep(3)
            
            # 查找微博卡片
            weibo_cards = page.query_selector_all("article")
            if weibo_cards:
                first_card = weibo_cards[0]
                
                # 尝试点击进入详情页
                try:
                    # 查找时间链接或详情链接
                    time_link = first_card.query_selector("time a, .time a, [href*='/detail/']")
                    if time_link:
                        time_link.click()
                        page.wait_for_load_state("domcontentloaded")
                        time.sleep(3)
                        logger.info("✅ 成功进入微博详情页")
                    else:
                        logger.warning("⚠️ 未找到详情页链接，使用当前页面测试")
                except Exception as e:
                    logger.warning("⚠️ 进入详情页失败: {}，使用当前页面测试", str(e))
            else:
                logger.warning("⚠️ 未找到微博卡片，使用当前页面测试")
        
        except Exception as e:
            logger.warning("⚠️ 页面导航失败: {}，使用当前页面测试", str(e))
        
        # 测试各个XPath选择器
        logger.info("🔍 开始测试XPath选择器...")
        
        # 测试关注按钮
        logger.info("测试关注按钮XPath...")
        try:
            follow_xpath = xpath_selectors["follow_button"]
            follow_element = page.query_selector(f"xpath={follow_xpath}")
            
            if follow_element and follow_element.is_visible():
                test_results["xpath_tests"]["follow_button"]["found"] = True
                test_results["xpath_tests"]["follow_button"]["xpath"] = follow_xpath
                logger.info("✅ 关注按钮XPath有效")
            else:
                test_results["xpath_tests"]["follow_button"]["found"] = False
                logger.warning("⚠️ 关注按钮XPath无效或元素不可见")
        except Exception as e:
            test_results["xpath_tests"]["follow_button"]["error"] = str(e)
            logger.error("❌ 关注按钮XPath测试失败: {}", str(e))
        
        # 测试点赞按钮
        logger.info("测试点赞按钮XPath...")
        try:
            like_xpath = xpath_selectors["like_button"]
            like_element = page.query_selector(f"xpath={like_xpath}")
            
            if like_element and like_element.is_visible():
                test_results["xpath_tests"]["like_button"]["found"] = True
                test_results["xpath_tests"]["like_button"]["xpath"] = like_xpath
                logger.info("✅ 点赞按钮XPath有效")
            else:
                test_results["xpath_tests"]["like_button"]["found"] = False
                logger.warning("⚠️ 点赞按钮XPath无效或元素不可见")
        except Exception as e:
            test_results["xpath_tests"]["like_button"]["error"] = str(e)
            logger.error("❌ 点赞按钮XPath测试失败: {}", str(e))
        
        # 测试评论框
        logger.info("测试评论框选择器...")
        try:
            comment_selector = xpath_selectors["comment_box"]
            comment_element = page.query_selector(comment_selector)
            
            if comment_element:
                test_results["xpath_tests"]["comment_box"]["found"] = True
                test_results["xpath_tests"]["comment_box"]["xpath"] = comment_selector
                logger.info("✅ 评论框选择器有效")
            else:
                test_results["xpath_tests"]["comment_box"]["found"] = False
                logger.warning("⚠️ 评论框选择器无效")
        except Exception as e:
            test_results["xpath_tests"]["comment_box"]["error"] = str(e)
            logger.error("❌ 评论框选择器测试失败: {}", str(e))
        
        # 执行完整的自动化测试
        logger.info("🚀 开始执行完整的自动化测试...")
        start_time = time.time()
        
        try:
            # 执行自动化操作（仅点赞，避免过多操作）
            result = automate_on_post(page, do_comment=False, do_like=True, do_repost=False, do_follow=False)
            
            execution_time = time.time() - start_time
            test_results["automation_test"]["execution_time"] = execution_time
            
            if "error" in result:
                test_results["automation_test"]["error"] = result["error"]
                test_results["automation_test"]["success"] = False
                logger.error("❌ 自动化测试失败: {}", result["error"])
            else:
                test_results["automation_test"]["operations"] = {
                    "follow_executed": result.get("follow_executed", False),
                    "like_executed": result.get("like_executed", False),
                    "comment_executed": result.get("comment_executed", False),
                    "repost_executed": result.get("repost_executed", False)
                }
                
                # 检查点赞是否成功
                test_results["automation_test"]["success"] = result.get("like_executed", False)
                
                if test_results["automation_test"]["success"]:
                    logger.info("✅ 自动化测试成功")
                else:
                    logger.warning("⚠️ 自动化测试未完全成功")
        
        except Exception as e:
            test_results["automation_test"]["error"] = str(e)
            test_results["automation_test"]["execution_time"] = time.time() - start_time
            logger.error("❌ 自动化测试异常: {}", str(e))
    
    except Exception as e:
        logger.error("❌ 测试过程异常: {}", str(e))
        test_results["error"] = str(e)
    
    finally:
        bm.close()
    
    return test_results


def generate_test_report(results):
    """生成测试报告"""
    
    report = []
    report.append("=" * 80)
    report.append("🎯 XPath选择器优化测试报告")
    report.append("=" * 80)
    report.append("")
    
    # XPath选择器测试结果
    xpath_tests = results.get("xpath_tests", {})
    
    report.append("🔍 XPath选择器测试结果:")
    
    for selector_name, test_result in xpath_tests.items():
        status = "✅" if test_result.get("found", False) else "❌"
        report.append(f"   {selector_name}: {status}")
        
        if test_result.get("xpath"):
            report.append(f"      XPath: {test_result['xpath']}")
        
        if test_result.get("error"):
            report.append(f"      错误: {test_result['error']}")
    
    report.append("")
    
    # 自动化测试结果
    automation_test = results.get("automation_test", {})
    
    report.append("🚀 自动化测试结果:")
    
    if automation_test.get("success", False):
        report.append("   状态: ✅ 成功")
    else:
        report.append("   状态: ❌ 失败")
    
    report.append(f"   执行时间: {automation_test.get('execution_time', 0):.2f} 秒")
    
    operations = automation_test.get("operations", {})
    if operations:
        report.append("   操作结果:")
        for op_name, success in operations.items():
            op_status = "✅" if success else "❌"
            report.append(f"      {op_name}: {op_status}")
    
    if automation_test.get("error"):
        report.append(f"   错误: {automation_test['error']}")
    
    report.append("")
    
    # 总体评估
    xpath_success_count = sum(1 for test in xpath_tests.values() if test.get("found", False))
    xpath_total = len(xpath_tests)
    automation_success = automation_test.get("success", False)
    
    report.append("📊 总体评估:")
    report.append(f"   XPath选择器有效性: {xpath_success_count}/{xpath_total}")
    report.append(f"   自动化测试: {'✅ 通过' if automation_success else '❌ 失败'}")
    
    if xpath_success_count >= 2 and automation_success:
        report.append("")
        report.append("🎉 XPath优化测试成功！")
        report.append("   - 大部分XPath选择器有效")
        report.append("   - 自动化流程正常工作")
        report.append("   - 系统已准备好使用优化的选择器")
    else:
        report.append("")
        report.append("⚠️ XPath优化需要进一步调整")
        report.append("   建议:")
        if xpath_success_count < 2:
            report.append("   - 检查XPath选择器的准确性")
            report.append("   - 确认页面结构是否发生变化")
        if not automation_success:
            report.append("   - 检查自动化流程的稳定性")
            report.append("   - 验证元素定位逻辑")
    
    report.append("")
    report.append("=" * 80)
    
    report_text = "\n".join(report)
    print(report_text)
    
    # 保存报告
    report_file = f"xpath_optimization_test_report_{int(time.time())}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    logger.info("📄 测试报告已保存到: {}", report_file)
    
    return xpath_success_count >= 2 and automation_success


def main():
    """主函数"""
    logger.info("🚀 启动XPath选择器优化测试")
    
    results = test_xpath_selectors()
    success = generate_test_report(results)
    
    if success:
        logger.info("🎉 XPath优化测试成功！")
        return True
    else:
        logger.warning("⚠️ XPath优化测试需要进一步调整")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
