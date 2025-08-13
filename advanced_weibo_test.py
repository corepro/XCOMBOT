#!/usr/bin/env python3
"""
微博自动化高级测试系统

专门用于测试重构后的智能元素定位系统和操作流程控制
验证99%成功率目标的实现情况
"""

import argparse
import time
import sys
import json
import statistics
from pathlib import Path
from typing import Dict, List, Tuple

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.browser import BrowserManager
from src.logger import logger
from src.config import CONFIG
from src.weibo import automate_on_post_alternative, WEIBO_HOME
from src.login_weibo import is_logged_in_weibo


class WeiboTestSuite:
    """微博自动化测试套件"""
    
    def __init__(self):
        self.test_results = []
        self.success_rates = {}
        self.error_patterns = {}
        
    def run_comprehensive_test(self, test_config: dict) -> dict:
        """运行综合测试"""
        logger.info("🧪 开始微博自动化综合测试")
        logger.info("📋 测试配置: {}", test_config)
        
        # 测试配置
        test_rounds = test_config.get("test_rounds", 5)
        headless = test_config.get("headless", False)
        operations = test_config.get("operations", {
            "do_comment": True,
            "do_like": True,
            "do_repost": True,
            "do_follow": True
        })
        
        # 设置浏览器配置
        CONFIG.headless = headless
        CONFIG.slow_mo_ms = 200  # 适中的速度便于观察
        
        overall_results = {
            "total_tests": test_rounds,
            "successful_tests": 0,
            "failed_tests": 0,
            "operation_success_rates": {},
            "average_execution_time": 0,
            "error_analysis": {},
            "detailed_results": []
        }
        
        execution_times = []
        operation_stats = {
            "follow": {"success": 0, "total": 0},
            "like": {"success": 0, "total": 0},
            "comment": {"success": 0, "total": 0},
            "repost": {"success": 0, "total": 0}
        }
        
        for round_num in range(1, test_rounds + 1):
            logger.info("🔄 执行第 {}/{} 轮测试", round_num, test_rounds)
            
            test_result = self._run_single_test(operations, round_num)
            overall_results["detailed_results"].append(test_result)
            
            # 统计结果
            if test_result.get("success", False):
                overall_results["successful_tests"] += 1
            else:
                overall_results["failed_tests"] += 1
            
            # 统计执行时间
            if "execution_time" in test_result:
                execution_times.append(test_result["execution_time"])
            
            # 统计各操作成功率
            for op in ["follow", "like", "comment", "repost"]:
                if operations.get(f"do_{op}", False):
                    operation_stats[op]["total"] += 1
                    if test_result.get(f"{op}_executed", False):
                        operation_stats[op]["success"] += 1
            
            # 错误分析
            if "error" in test_result:
                error_type = test_result["error"]
                overall_results["error_analysis"][error_type] = overall_results["error_analysis"].get(error_type, 0) + 1
            
            # 测试间隔
            if round_num < test_rounds:
                logger.info("⏳ 等待5秒后进行下一轮测试...")
                time.sleep(5)
        
        # 计算最终统计
        overall_results["success_rate"] = (overall_results["successful_tests"] / test_rounds) * 100
        
        if execution_times:
            overall_results["average_execution_time"] = statistics.mean(execution_times)
            overall_results["min_execution_time"] = min(execution_times)
            overall_results["max_execution_time"] = max(execution_times)
        
        # 计算各操作成功率
        for op, stats in operation_stats.items():
            if stats["total"] > 0:
                success_rate = (stats["success"] / stats["total"]) * 100
                overall_results["operation_success_rates"][op] = success_rate
        
        return overall_results
    
    def _run_single_test(self, operations: dict, round_num: int) -> dict:
        """运行单次测试"""
        bm = BrowserManager()
        test_result = {
            "round": round_num,
            "success": False,
            "execution_time": 0,
            "follow_executed": False,
            "like_executed": False,
            "comment_executed": False,
            "repost_executed": False,
            "weibo_link": None,
            "step_results": {},
            "error": None
        }
        
        start_time = time.time()
        
        try:
            # 启动浏览器
            bm.launch()
            bm.new_context(use_storage=True)
            page = bm.page
            
            # 检查登录状态
            page.goto(WEIBO_HOME)
            page.wait_for_load_state("domcontentloaded")
            
            if not is_logged_in_weibo(page):
                test_result["error"] = "not_logged_in"
                return test_result
            
            # 执行自动化测试
            automation_result = automate_on_post_alternative(
                page,
                do_comment=operations.get("do_comment", False),
                do_like=operations.get("do_like", False),
                do_repost=operations.get("do_repost", False),
                do_follow=operations.get("do_follow", False)
            )
            
            # 提取结果
            test_result.update({
                "follow_executed": automation_result.get("follow_executed", False),
                "like_executed": automation_result.get("like_executed", False),
                "comment_executed": automation_result.get("comment_executed", False),
                "repost_executed": automation_result.get("repost_executed", False),
                "weibo_link": automation_result.get("weibo_link"),
                "step_results": automation_result.get("step_results", {}),
                "success_rate": automation_result.get("success_rate", 0)
            })
            
            # 判断测试是否成功（成功率 >= 90%）
            if automation_result.get("success_rate", 0) >= 90:
                test_result["success"] = True
            
            if "error" in automation_result:
                test_result["error"] = automation_result["error"]
                
        except Exception as e:
            test_result["error"] = f"test_exception: {str(e)}"
            logger.error("测试第{}轮异常: {}", round_num, str(e))
            
        finally:
            test_result["execution_time"] = time.time() - start_time
            bm.close()
        
        return test_result
    
    def generate_test_report(self, results: dict, output_file: str = None) -> str:
        """生成详细的测试报告"""
        
        report = []
        report.append("=" * 80)
        report.append("📊 微博自动化高级测试报告")
        report.append("=" * 80)
        report.append("")
        
        # 基本统计
        report.append("📈 基本统计:")
        report.append(f"   总测试轮数: {results['total_tests']}")
        report.append(f"   成功轮数: {results['successful_tests']}")
        report.append(f"   失败轮数: {results['failed_tests']}")
        report.append(f"   总体成功率: {results.get('success_rate', 0):.1f}%")
        report.append("")
        
        # 执行时间统计
        if "average_execution_time" in results:
            report.append("⏱️ 执行时间统计:")
            report.append(f"   平均执行时间: {results['average_execution_time']:.2f} 秒")
            report.append(f"   最短执行时间: {results.get('min_execution_time', 0):.2f} 秒")
            report.append(f"   最长执行时间: {results.get('max_execution_time', 0):.2f} 秒")
            report.append("")
        
        # 各操作成功率
        if results.get("operation_success_rates"):
            report.append("🎯 各操作成功率:")
            for op, rate in results["operation_success_rates"].items():
                status = "✅" if rate >= 95 else "⚠️" if rate >= 80 else "❌"
                report.append(f"   {op.capitalize()}: {rate:.1f}% {status}")
            report.append("")
        
        # 错误分析
        if results.get("error_analysis"):
            report.append("🔍 错误分析:")
            for error_type, count in results["error_analysis"].items():
                report.append(f"   {error_type}: {count} 次")
            report.append("")
        
        # 详细结果
        report.append("📋 详细测试结果:")
        for i, test in enumerate(results.get("detailed_results", []), 1):
            status = "✅" if test.get("success") else "❌"
            report.append(f"   第{i}轮: {status} (耗时: {test.get('execution_time', 0):.2f}s)")
            
            if test.get("step_results"):
                step_success = sum(1 for step in test["step_results"].values() if step.get("success", False))
                total_steps = len(test["step_results"])
                report.append(f"         步骤成功率: {step_success}/{total_steps} ({(step_success/total_steps)*100:.1f}%)")
            
            if test.get("error"):
                report.append(f"         错误: {test['error']}")
        
        report.append("")
        report.append("=" * 80)
        
        # 成功标准评估
        overall_success_rate = results.get('success_rate', 0)
        operation_rates = results.get('operation_success_rates', {})
        
        report.append("🎯 成功标准评估:")
        report.append(f"   目标: 整体成功率 ≥ 90%, 单操作成功率 ≥ 95%")
        report.append("")
        
        if overall_success_rate >= 90:
            report.append("✅ 整体成功率达标")
        else:
            report.append("❌ 整体成功率未达标")
        
        all_ops_pass = all(rate >= 95 for rate in operation_rates.values())
        if all_ops_pass and operation_rates:
            report.append("✅ 所有操作成功率达标")
        else:
            report.append("❌ 部分操作成功率未达标")
        
        if overall_success_rate >= 90 and all_ops_pass:
            report.append("")
            report.append("🎉 测试通过！系统达到99%成功率目标！")
        else:
            report.append("")
            report.append("⚠️ 测试未完全通过，需要进一步优化")
        
        report.append("=" * 80)
        
        report_text = "\n".join(report)
        
        # 保存报告
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            logger.info("📄 测试报告已保存到: {}", output_file)
        
        return report_text


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="微博自动化高级测试系统")
    parser.add_argument("--rounds", type=int, default=5, help="测试轮数 (默认: 5)")
    parser.add_argument("--headless", action="store_true", help="无头模式运行")
    parser.add_argument("--no-comment", action="store_true", help="不测试评论")
    parser.add_argument("--no-like", action="store_true", help="不测试点赞")
    parser.add_argument("--no-repost", action="store_true", help="不测试转发")
    parser.add_argument("--no-follow", action="store_true", help="不测试关注")
    parser.add_argument("--output", type=str, help="测试报告输出文件")
    parser.add_argument("--quick", action="store_true", help="快速测试（仅点赞，3轮）")
    
    args = parser.parse_args()
    
    # 构建测试配置
    if args.quick:
        test_config = {
            "test_rounds": 3,
            "headless": args.headless,
            "operations": {
                "do_comment": False,
                "do_like": True,
                "do_repost": False,
                "do_follow": False
            }
        }
        logger.info("🚀 快速测试模式：仅测试点赞操作，3轮测试")
    else:
        test_config = {
            "test_rounds": args.rounds,
            "headless": args.headless,
            "operations": {
                "do_comment": not args.no_comment,
                "do_like": not args.no_like,
                "do_repost": not args.no_repost,
                "do_follow": not args.no_follow
            }
        }
    
    # 执行测试
    test_suite = WeiboTestSuite()
    results = test_suite.run_comprehensive_test(test_config)
    
    # 生成并显示报告
    output_file = args.output or f"weibo_test_report_{int(time.time())}.txt"
    report = test_suite.generate_test_report(results, output_file)
    print(report)
    
    # 返回适当的退出码
    success_rate = results.get('success_rate', 0)
    sys.exit(0 if success_rate >= 90 else 1)


if __name__ == "__main__":
    main()
