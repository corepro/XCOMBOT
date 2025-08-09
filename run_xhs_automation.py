#!/usr/bin/env python3
"""
小红书自动化启动脚本
简化版本，用于快速测试和执行
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from src.browser import BrowserManager
from src.login_xhs import ensure_login_xhs
from src.xhs import open_home_xhs, pick_random_card, xhs_interact_with_post
from src.logger import logger


def run_xhs_automation(count: int = 5, interval: int = 10, 
                      do_comment: bool = True, do_like: bool = True, 
                      do_collect: bool = True, do_share: bool = False):
    """运行小红书自动化"""
    
    # 初始化浏览器
    bm = BrowserManager()
    bm.launch()
    bm.new_context(use_storage=True)
    
    try:
        # 登录
        logger.info("开始登录小红书...")
        if not ensure_login_xhs(bm.page, timeout_sec=300):
            logger.error("登录失败")
            return False
        
        logger.info("登录成功，开始执行 {} 次自动化操作", count)
        
        success_count = 0
        
        for i in range(count):
            logger.info("=== 第 {}/{} 次执行 ===", i + 1, count)
            
            try:
                # 打开首页
                open_home_xhs(bm.page)
                time.sleep(2.0)
                
                # 选择随机卡片
                card = pick_random_card(bm.page, limit=20)
                if not card:
                    logger.warning("第 {} 次: 未找到可用卡片", i + 1)
                    continue
                
                # 进入详情页
                opened = False
                for click_sel in ["a", "img"]:
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
                    logger.warning("第 {} 次: 无法进入详情页", i + 1)
                    continue
                
                # 等待页面加载
                time.sleep(2.0)
                logger.info("第 {} 次: 已进入详情页: {}", i + 1, bm.page.url)
                
                # 执行交互
                result = xhs_interact_with_post(
                    bm.page,
                    do_comment=do_comment,
                    do_like=do_like,
                    do_collect=do_collect,
                    do_share=do_share
                )
                
                if result["success"]:
                    success_count += 1
                    logger.info("第 {} 次: 执行成功 - 评论:{} 点赞:{} 收藏:{} 分享:{}", 
                              i + 1, result["comment"], result["like"], 
                              result["collect"], result["share"])
                else:
                    logger.warning("第 {} 次: 执行失败", i + 1)
                
            except Exception as e:
                logger.error("第 {} 次: 执行出错: {}", i + 1, str(e))
            
            # 间隔等待
            if i < count - 1:
                logger.info("等待 {} 秒后继续...", interval)
                time.sleep(interval)
        
        # 输出总结
        logger.info("=== 执行完成 ===")
        logger.info("总执行次数: {}", count)
        logger.info("成功次数: {}", success_count)
        logger.info("成功率: {:.1f}%", (success_count / count * 100) if count > 0 else 0)
        
        return success_count > 0
        
    except KeyboardInterrupt:
        logger.info("用户中断执行")
        return False
    except Exception as e:
        logger.error("执行失败: {}", str(e))
        return False
    finally:
        try:
            bm.save_storage()
            bm.close()
        except Exception:
            pass


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="小红书自动化脚本")
    parser.add_argument("-n", "--count", type=int, default=5, help="执行次数")
    parser.add_argument("-i", "--interval", type=int, default=10, help="间隔秒数")
    parser.add_argument("--no-comment", action="store_true", help="禁用评论")
    parser.add_argument("--no-like", action="store_true", help="禁用点赞")
    parser.add_argument("--no-collect", action="store_true", help="禁用收藏")
    parser.add_argument("--enable-share", action="store_true", help="启用分享")
    
    args = parser.parse_args()
    
    success = run_xhs_automation(
        count=args.count,
        interval=args.interval,
        do_comment=not args.no_comment,
        do_like=not args.no_like,
        do_collect=not args.no_collect,
        do_share=args.enable_share
    )
    
    sys.exit(0 if success else 1)
