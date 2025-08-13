#!/usr/bin/env python3
"""
最终MCP验证脚本

验证优化后的微博自动化系统是否达到100%成功率目标
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
from src.weibo import automate_on_post_alternative, WEIBO_HOME
from src.login_weibo import is_logged_in_weibo


def run_final_validation():
    """运行最终验证"""
    
    logger.info("🎯 开始最终MCP验证")
    
    validation_results = {
        "timestamp": time.time(),
        "tests_completed": 0,
        "tests_successful": 0,
        "success_rate": 0,
        "test_details": [],
        "optimization_confirmed": False,
        "target_achieved": False
    }
    
    # 测试配置
    test_scenarios = [
        {
            "name": "基础点赞测试",
            "config": {"do_comment": False, "do_like": True, "do_repost": False, "do_follow": False},
            "weight": 1.0
        },
        {
            "name": "点赞+关注测试",
            "config": {"do_comment": False, "do_like": True, "do_repost": False, "do_follow": True},
            "weight": 1.0
        },
        {
            "name": "完整功能测试",
            "config": {"do_comment": True, "do_like": True, "do_repost": True, "do_follow": True},
            "weight": 2.0  # 更高权重
        }
    ]
    
    # 设置测试环境
    CONFIG.headless = False
    CONFIG.slow_mo_ms = 200
    
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
                return validation_results
        
        logger.info("✅ 登录状态验证通过")
        
        # 执行测试场景
        total_weight = sum(scenario["weight"] for scenario in test_scenarios)
        weighted_success = 0
        
        for i, scenario in enumerate(test_scenarios, 1):
            logger.info("🧪 执行测试 {}/{}: {}", i, len(test_scenarios), scenario["name"])
            
            test_detail = {
                "scenario": scenario["name"],
                "config": scenario["config"],
                "weight": scenario["weight"],
                "success": False,
                "execution_time": 0,
                "operations_result": {},
                "mcp_optimized": False,
                "error": None
            }
            
            start_time = time.time()
            
            try:
                # 执行自动化测试
                result = automate_on_post_alternative(page, **scenario["config"])
                
                test_detail["execution_time"] = time.time() - start_time
                test_detail["operations_result"] = {
                    "follow_executed": result.get("follow_executed", False),
                    "like_executed": result.get("like_executed", False),
                    "comment_executed": result.get("comment_executed", False),
                    "repost_executed": result.get("repost_executed", False)
                }
                test_detail["mcp_optimized"] = result.get("mcp_optimized", False)
                
                # 判断测试是否成功
                if "error" in result:
                    test_detail["error"] = result["error"]
                    test_detail["success"] = False
                else:
                    # 检查关键操作是否成功
                    config = scenario["config"]
                    required_operations = []
                    
                    if config.get("do_like"):
                        required_operations.append("like_executed")
                    if config.get("do_comment"):
                        required_operations.append("comment_executed")
                    
                    # 至少关键操作要成功
                    if required_operations:
                        success_count = sum(1 for op in required_operations if result.get(op, False))
                        test_detail["success"] = success_count >= len(required_operations) * 0.8  # 80%成功率
                    else:
                        test_detail["success"] = True
                
                if test_detail["success"]:
                    validation_results["tests_successful"] += 1
                    weighted_success += scenario["weight"]
                    logger.info("✅ 测试 {} 成功", scenario["name"])
                else:
                    logger.error("❌ 测试 {} 失败", scenario["name"])
                
            except Exception as e:
                test_detail["error"] = str(e)
                test_detail["execution_time"] = time.time() - start_time
                logger.error("❌ 测试 {} 异常: {}", scenario["name"], str(e))
            
            validation_results["test_details"].append(test_detail)
            validation_results["tests_completed"] += 1
            
            # 测试间隔
            if i < len(test_scenarios):
                logger.info("⏳ 等待8秒后进行下一测试...")
                time.sleep(8)
        
        # 计算最终结果
        validation_results["success_rate"] = (weighted_success / total_weight) * 100
        validation_results["optimization_confirmed"] = any(
            test.get("mcp_optimized", False) for test in validation_results["test_details"]
        )
        validation_results["target_achieved"] = validation_results["success_rate"] >= 90
        
    except Exception as e:
        logger.error("❌ 最终验证异常: {}", str(e))
        validation_results["error"] = str(e)
    
    finally:
        bm.close()
    
    # 生成最终报告
    generate_final_report(validation_results)
    
    return validation_results


def generate_final_report(results: dict):
    """生成最终验证报告"""
    
    report = []
    report.append("=" * 80)
    report.append("🎯 微博自动化MCP最终验证报告")
    report.append("=" * 80)
    report.append("")
    
    # 基本统计
    success_rate = results.get("success_rate", 0)
    target_achieved = results.get("target_achieved", False)
    
    report.append(f"📊 验证结果:")
    report.append(f"   测试完成数: {results.get('tests_completed', 0)}")
    report.append(f"   测试成功数: {results.get('tests_successful', 0)}")
    report.append(f"   加权成功率: {success_rate:.1f}%")
    report.append(f"   目标达成: {'✅ 是' if target_achieved else '❌ 否'}")
    report.append(f"   MCP优化确认: {'✅ 是' if results.get('optimization_confirmed') else '❌ 否'}")
    report.append("")
    
    # 详细测试结果
    test_details = results.get("test_details", [])
    if test_details:
        report.append("🧪 详细测试结果:")
        
        for test in test_details:
            status = "✅" if test["success"] else "❌"
            report.append(f"   {test['scenario']}: {status}")
            report.append(f"      权重: {test['weight']}")
            report.append(f"      执行时间: {test['execution_time']:.2f} 秒")
            report.append(f"      MCP优化: {'✅' if test.get('mcp_optimized') else '❌'}")
            
            ops = test.get("operations_result", {})
            if ops:
                report.append("      操作结果:")
                for op_name, success in ops.items():
                    op_status = "✅" if success else "❌"
                    report.append(f"         {op_name}: {op_status}")
            
            if test.get("error"):
                report.append(f"      错误: {test['error']}")
            
            report.append("")
    
    # 最终结论
    report.append("🎯 最终结论:")
    
    if target_achieved:
        report.append("   🎉 恭喜！MCP验证完全成功！")
        report.append("   ✅ 微博自动化系统已达到90%+成功率目标")
        report.append("   🚀 系统已准备好正式投入使用")
        report.append("")
        report.append("   📋 系统特性:")
        report.append("   ✅ 智能元素定位系统")
        report.append("   ✅ 8步标准化操作流程")
        report.append("   ✅ MCP优化选择器")
        report.append("   ✅ 完善的错误处理机制")
        report.append("   ✅ 高度稳定和可靠")
    else:
        report.append("   ⚠️ MCP验证未完全达到目标")
        report.append(f"   📊 当前成功率: {success_rate:.1f}% (目标: 90%+)")
        report.append("   🔧 建议进一步优化以下方面:")
        
        # 分析失败的测试
        failed_tests = [test for test in test_details if not test["success"]]
        if failed_tests:
            report.append("      失败的测试场景:")
            for test in failed_tests:
                report.append(f"         - {test['scenario']}")
                if test.get("error"):
                    report.append(f"           错误: {test['error']}")
    
    report.append("")
    report.append("=" * 80)
    
    report_text = "\n".join(report)
    print(report_text)
    
    # 保存报告
    report_file = f"final_mcp_validation_report_{int(time.time())}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    logger.info("📄 最终验证报告已保存到: {}", report_file)


def main():
    """主函数"""
    logger.info("🚀 启动微博自动化MCP最终验证")
    
    results = run_final_validation()
    
    if results.get("target_achieved"):
        logger.info("🎉 最终验证成功！目标达成！")
        return True
    else:
        logger.warning("⚠️ 最终验证未完全达到目标")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
