#!/usr/bin/env python3
"""
小红书自动化脚本 - 完整功能版本
包含：登录、获取文章内容、评论、点赞、收藏、分享
支持 N 次执行和结果统计
"""

from __future__ import annotations
import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.browser import BrowserManager
from src.login_xhs import login_flow_xhs, ensure_login_xhs
from src.xhs import (
    open_home_xhs, pick_random_card, extract_card_content, 
    xhs_interact_with_post, act_once_on_first_card
)
from src.logger import logger


class XHSAutomation:
    def __init__(self, headless: bool = False, slow_mo: int = 100):
        self.headless = headless
        self.slow_mo = slow_mo
        self.bm = None
        self.results = []
        
    def setup_browser(self):
        """初始化浏览器"""
        self.bm = BrowserManager()
        # 临时设置配置
        from src.config import CONFIG
        CONFIG.headless = self.headless
        CONFIG.slow_mo_ms = self.slow_mo
        
        self.bm.launch()
        self.bm.new_context(use_storage=True)
        logger.info("XHS自动化: 浏览器已启动")
        
    def ensure_login(self, timeout: int = 300) -> bool:
        """确保已登录"""
        try:
            return ensure_login_xhs(self.bm.page, timeout_sec=timeout)
        except Exception as e:
            logger.error("XHS自动化: 登录失败: {}", str(e))
            return False
    
    def run_single_interaction(self, interaction_config: Dict[str, Any]) -> Dict[str, Any]:
        """执行单次交互"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": None,
            "content": {},
            "actions": {}
        }
        
        try:
            page = self.bm.page
            
            # 打开首页
            open_home_xhs(page)
            time.sleep(2.0)
            
            # 选择卡片
            card = pick_random_card(page, limit=20)
            if not card:
                result["error"] = "未找到可用卡片"
                return result
            
            # 提取卡片内容
            content = extract_card_content(card)
            result["content"] = content
            logger.info("XHS自动化: 选中卡片 - {}", content.get("title", "无标题")[:50])
            
            # 进入详情页
            opened = False
            for click_sel in ["a", "img", "picture"]:
                try:
                    elem = card.locator(click_sel).first
                    if elem and elem.count() > 0:
                        elem.click(timeout=30000)
                        opened = True
                        break
                except Exception:
                    continue
            
            if not opened:
                try:
                    card.click(timeout=30000)
                    opened = True
                except Exception:
                    pass
            
            if not opened:
                result["error"] = "无法进入详情页"
                return result
            
            # 等待详情页加载
            time.sleep(2.0)
            logger.info("XHS自动化: 已进入详情页: {}", page.url)
            
            # 执行交互
            interaction_result = xhs_interact_with_post(
                page,
                do_comment=interaction_config.get("comment", True),
                do_like=interaction_config.get("like", True),
                do_collect=interaction_config.get("collect", True),
                do_share=interaction_config.get("share", False),
                comment_text=interaction_config.get("comment_text")
            )
            
            result["actions"] = {
                "comment": interaction_result["comment"],
                "like": interaction_result["like"],
                "collect": interaction_result["collect"],
                "share": interaction_result["share"]
            }
            result["success"] = interaction_result["success"]
            
        except Exception as e:
            result["error"] = str(e)
            logger.error("XHS自动化: 单次交互失败: {}", str(e))
        
        return result
    
    def run_multiple_interactions(self, count: int, interval: int = 10, 
                                 interaction_config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """执行多次交互"""
        if interaction_config is None:
            interaction_config = {
                "comment": True,
                "like": True,
                "collect": True,
                "share": False
            }
        
        results = []
        
        for i in range(count):
            logger.info("XHS自动化: 开始第 {}/{} 次交互", i + 1, count)
            
            result = self.run_single_interaction(interaction_config)
            result["iteration"] = i + 1
            results.append(result)
            
            if result["success"]:
                logger.info("XHS自动化: 第 {} 次交互成功", i + 1)
            else:
                logger.warning("XHS自动化: 第 {} 次交互失败: {}", i + 1, result.get("error", "未知错误"))
            
            # 间隔等待（除了最后一次）
            if i < count - 1:
                logger.info("XHS自动化: 等待 {} 秒后继续...", interval)
                time.sleep(interval)
        
        return results
    
    def generate_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成执行报告"""
        total = len(results)
        successful = sum(1 for r in results if r["success"])
        failed = total - successful
        
        action_stats = {
            "comment": sum(1 for r in results if r.get("actions", {}).get("comment", False)),
            "like": sum(1 for r in results if r.get("actions", {}).get("like", False)),
            "collect": sum(1 for r in results if r.get("actions", {}).get("collect", False)),
            "share": sum(1 for r in results if r.get("actions", {}).get("share", False))
        }
        
        errors = {}
        for r in results:
            if not r["success"] and r.get("error"):
                error = r["error"]
                errors[error] = errors.get(error, 0) + 1
        
        report = {
            "summary": {
                "total_runs": total,
                "successful": successful,
                "failed": failed,
                "success_rate": f"{(successful/total*100):.1f}%" if total > 0 else "0%"
            },
            "action_stats": action_stats,
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }
        
        return report
    
    def save_results(self, results: List[Dict[str, Any]], report: Dict[str, Any], 
                    filename: str = None):
        """保存结果到文件"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"xhs_automation_results_{timestamp}.json"
        
        output_dir = Path("results")
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / filename
        
        data = {
            "report": report,
            "results": results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info("XHS自动化: 结果已保存到 {}", output_file)
        return output_file
    
    def cleanup(self):
        """清理资源"""
        if self.bm:
            try:
                self.bm.save_storage()
                self.bm.close()
            except Exception as e:
                logger.warning("XHS自动化: 清理资源时出错: {}", str(e))


def main():
    parser = argparse.ArgumentParser(description="小红书自动化脚本")
    parser.add_argument("-n", "--count", type=int, default=5, help="执行次数 (默认: 5)")
    parser.add_argument("-i", "--interval", type=int, default=10, help="间隔秒数 (默认: 10)")
    parser.add_argument("--headless", action="store_true", help="无头模式")
    parser.add_argument("--slow-mo", type=int, default=100, help="慢动作延迟毫秒 (默认: 100)")
    parser.add_argument("--no-comment", action="store_true", help="禁用评论")
    parser.add_argument("--no-like", action="store_true", help="禁用点赞")
    parser.add_argument("--no-collect", action="store_true", help="禁用收藏")
    parser.add_argument("--enable-share", action="store_true", help="启用分享")
    parser.add_argument("--login-timeout", type=int, default=300, help="登录超时秒数 (默认: 300)")
    
    args = parser.parse_args()
    
    # 配置交互选项
    interaction_config = {
        "comment": not args.no_comment,
        "like": not args.no_like,
        "collect": not args.no_collect,
        "share": args.enable_share
    }
    
    automation = XHSAutomation(headless=args.headless, slow_mo=args.slow_mo)
    
    try:
        # 初始化
        automation.setup_browser()
        
        # 登录
        logger.info("XHS自动化: 开始登录流程...")
        if not automation.ensure_login(timeout=args.login_timeout):
            logger.error("XHS自动化: 登录失败，退出")
            return 1
        
        logger.info("XHS自动化: 登录成功，开始执行 {} 次交互", args.count)
        
        # 执行多次交互
        results = automation.run_multiple_interactions(
            count=args.count,
            interval=args.interval,
            interaction_config=interaction_config
        )
        
        # 生成报告
        report = automation.generate_report(results)
        
        # 保存结果
        output_file = automation.save_results(results, report)
        
        # 打印摘要
        print("\n" + "="*50)
        print("XHS自动化执行完成")
        print("="*50)
        print(f"总执行次数: {report['summary']['total_runs']}")
        print(f"成功次数: {report['summary']['successful']}")
        print(f"失败次数: {report['summary']['failed']}")
        print(f"成功率: {report['summary']['success_rate']}")
        print(f"评论成功: {report['action_stats']['comment']}")
        print(f"点赞成功: {report['action_stats']['like']}")
        print(f"收藏成功: {report['action_stats']['collect']}")
        print(f"分享成功: {report['action_stats']['share']}")
        print(f"结果文件: {output_file}")
        print("="*50)
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("XHS自动化: 用户中断执行")
        return 1
    except Exception as e:
        logger.error("XHS自动化: 执行失败: {}", str(e))
        return 1
    finally:
        automation.cleanup()


if __name__ == "__main__":
    sys.exit(main())
