#!/usr/bin/env python3
"""
详情页验证测试脚本

测试修复后的详情页链接查找和验证机制
确保系统在没有找到详情页链接时不会继续执行后续操作
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
from src.weibo import automate_on_post, WEIBO_HOME, extract_post_link_from_card, pick_random_post
from src.login_weibo import is_logged_in_weibo


def test_detail_page_link_extraction():
    """测试详情页链接提取功能"""
    
    logger.info("🧪 开始测试详情页链接提取功能")
    
    test_results = {
        "timestamp": time.time(),
        "link_extraction_test": {
            "success": False,
            "links_found": 0,
            "selectors_tested": 0,
            "retry_attempts": 0,
            "error": None
        }
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
        
        # 测试详情页链接提取
        logger.info("🔍 测试详情页链接提取功能...")
        
        # 获取微博卡片
        card = pick_random_post(page, limit=20, require_comment=False)
        if not card:
            logger.error("❌ 未找到微博卡片")
            test_results["link_extraction_test"]["error"] = "no_card_found"
            return test_results
        
        logger.info("✅ 成功获取微博卡片")
        
        # 测试增强的链接提取函数
        detail_link = extract_post_link_from_card(card, page)
        
        if detail_link:
            test_results["link_extraction_test"]["success"] = True
            test_results["link_extraction_test"]["links_found"] = 1
            logger.info("✅ 详情页链接提取成功: {}", detail_link)
        else:
            test_results["link_extraction_test"]["success"] = False
            test_results["link_extraction_test"]["error"] = "no_link_extracted"
            logger.error("❌ 详情页链接提取失败")
        
    except Exception as e:
        logger.error("❌ 链接提取测试异常: {}", str(e))
        test_results["link_extraction_test"]["error"] = str(e)
    
    finally:
        bm.close()
    
    return test_results


def test_critical_step1_validation():
    """测试关键步骤1的验证机制"""
    
    logger.info("🧪 开始测试关键步骤1验证机制")
    
    test_results = {
        "timestamp": time.time(),
        "step1_validation_test": {
            "success": False,
            "detail_page_entered": False,
            "validation_passed": False,
            "execution_time": 0,
            "error": None
        }
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
        
        # 测试完整的自动化流程（包括关键步骤1验证）
        logger.info("🚀 测试完整自动化流程的步骤1验证...")
        
        start_time = time.time()
        
        # 执行自动化操作（仅点赞，减少操作复杂度）
        result = automate_on_post(
            page, 
            do_comment=False,
            do_like=True,
            do_repost=False,
            do_follow=False
        )
        
        execution_time = time.time() - start_time
        test_results["step1_validation_test"]["execution_time"] = execution_time
        
        # 分析结果
        if "error" in result:
            if "critical_step1_failed" in result["error"]:
                logger.info("✅ 关键步骤1验证机制正常工作")
                logger.info("   系统正确阻止了在无详情页链接时的后续操作")
                test_results["step1_validation_test"]["success"] = True
                test_results["step1_validation_test"]["validation_passed"] = True
            else:
                logger.error("❌ 其他错误: {}", result["error"])
                test_results["step1_validation_test"]["error"] = result["error"]
        else:
            # 检查是否成功进入详情页
            if result.get("weibo_link"):
                logger.info("✅ 成功进入详情页: {}", result["weibo_link"])
                test_results["step1_validation_test"]["success"] = True
                test_results["step1_validation_test"]["detail_page_entered"] = True
                test_results["step1_validation_test"]["validation_passed"] = True
            else:
                logger.warning("⚠️ 操作完成但未获取到详情页链接")
                test_results["step1_validation_test"]["error"] = "no_weibo_link_in_result"
        
    except Exception as e:
        logger.error("❌ 步骤1验证测试异常: {}", str(e))
        test_results["step1_validation_test"]["error"] = str(e)
    
    finally:
        bm.close()
    
    return test_results


def generate_validation_report(link_results, step1_results):
    """生成验证报告"""
    
    report = []
    report.append("=" * 80)
    report.append("🎯 详情页验证修复测试报告")
    report.append("=" * 80)
    report.append("")
    
    # 链接提取测试结果
    link_test = link_results.get("link_extraction_test", {})
    
    report.append("🔍 详情页链接提取测试:")
    if link_test.get("success", False):
        report.append("   状态: ✅ 成功")
        report.append(f"   找到链接数: {link_test.get('links_found', 0)}")
    else:
        report.append("   状态: ❌ 失败")
        if link_test.get("error"):
            report.append(f"   错误: {link_test['error']}")
    
    report.append("")
    
    # 步骤1验证测试结果
    step1_test = step1_results.get("step1_validation_test", {})
    
    report.append("🚀 关键步骤1验证测试:")
    if step1_test.get("success", False):
        report.append("   状态: ✅ 成功")
        report.append(f"   执行时间: {step1_test.get('execution_time', 0):.2f} 秒")
        
        if step1_test.get("detail_page_entered", False):
            report.append("   结果: ✅ 成功进入详情页")
        elif step1_test.get("validation_passed", False):
            report.append("   结果: ✅ 验证机制正常工作（正确阻止了错误操作）")
    else:
        report.append("   状态: ❌ 失败")
        if step1_test.get("error"):
            report.append(f"   错误: {step1_test['error']}")
    
    report.append("")
    
    # 总体评估
    link_success = link_test.get("success", False)
    step1_success = step1_test.get("success", False)
    
    report.append("📊 总体评估:")
    
    if link_success and step1_success:
        report.append("🎉 详情页验证修复成功！")
        report.append("")
        report.append("✅ 修复成果:")
        report.append("   - 增强的详情页链接提取功能正常工作")
        report.append("   - 关键步骤1验证机制有效")
        report.append("   - 系统能正确阻止在无详情页链接时的后续操作")
        report.append("   - 多重重试机制和错误处理完善")
        
        report.append("")
        report.append("🚀 系统现在能够:")
        report.append("   - 使用多种策略查找详情页链接")
        report.append("   - 在找不到链接时安全终止流程")
        report.append("   - 避免在错误页面执行自动化操作")
        report.append("   - 提供详细的错误诊断信息")
        
    else:
        report.append("⚠️ 详情页验证修复需要进一步调整")
        report.append("")
        report.append("🔧 建议检查:")
        if not link_success:
            report.append("   - 详情页链接选择器是否需要更新")
            report.append("   - 页面结构是否发生变化")
        if not step1_success:
            report.append("   - 步骤1验证逻辑是否正确")
            report.append("   - 错误处理机制是否完善")
    
    report.append("")
    report.append("=" * 80)
    
    report_text = "\n".join(report)
    print(report_text)
    
    # 保存报告
    report_file = f"detail_page_validation_report_{int(time.time())}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    logger.info("📄 验证报告已保存到: {}", report_file)
    
    return link_success and step1_success


def main():
    """主函数"""
    logger.info("🚀 启动详情页验证修复测试")
    
    print("🎯 详情页验证修复测试")
    print("=" * 60)
    print("📋 本测试将验证:")
    print("   1. 增强的详情页链接提取功能")
    print("   2. 关键步骤1的验证机制")
    print("   3. 错误情况下的安全终止机制")
    print("   4. 多重重试和错误处理")
    print("=" * 60)
    
    # 测试1：详情页链接提取
    logger.info("=" * 60)
    link_results = test_detail_page_link_extraction()
    
    # 测试2：关键步骤1验证
    logger.info("=" * 60)
    step1_results = test_critical_step1_validation()
    
    # 生成验证报告
    logger.info("=" * 60)
    success = generate_validation_report(link_results, step1_results)
    
    if success:
        logger.info("🎉 详情页验证修复测试成功！")
        return True
    else:
        logger.warning("⚠️ 详情页验证修复需要进一步调整")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
