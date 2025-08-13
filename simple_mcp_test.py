#!/usr/bin/env python3
"""
简化的MCP测试

用于诊断和验证基本功能
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.logger import logger
    logger.info("🚀 开始简化MCP测试")
    
    from src.browser import BrowserManager
    from src.config import CONFIG
    from src.weibo import WEIBO_HOME
    from src.login_weibo import is_logged_in_weibo
    
    logger.info("✅ 所有模块导入成功")
    
    # 测试浏览器启动
    logger.info("🔧 测试浏览器启动...")
    CONFIG.headless = False
    CONFIG.slow_mo_ms = 100
    
    bm = BrowserManager()
    
    try:
        bm.launch()
        bm.new_context(use_storage=True)
        page = bm.page
        
        logger.info("✅ 浏览器启动成功")
        
        # 测试页面导航
        logger.info("🌐 测试页面导航...")
        page.goto(WEIBO_HOME)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(3)
        
        logger.info("✅ 页面导航成功")
        
        # 测试登录检查
        logger.info("🔐 测试登录检查...")
        is_logged = is_logged_in_weibo(page)
        
        if is_logged:
            logger.info("✅ 检测到登录状态")
            
            # 测试基本的自动化功能
            logger.info("🎯 测试基本自动化功能...")
            
            try:
                from src.weibo import automate_on_post_alternative
                
                # 运行最简单的测试（仅点赞）
                result = automate_on_post_alternative(
                    page,
                    do_comment=False,
                    do_like=True,
                    do_repost=False,
                    do_follow=False
                )
                
                logger.info("📊 自动化测试结果: {}", result)
                
                if result.get("like_executed", False):
                    logger.info("🎉 简化MCP测试完全成功！")
                    print("\n" + "="*50)
                    print("🎉 简化MCP测试成功！")
                    print("✅ 基本自动化功能正常工作")
                    print("🚀 系统已准备好进行完整测试")
                    print("="*50)
                    success = True
                else:
                    logger.warning("⚠️ 自动化功能部分失败")
                    print("\n" + "="*50)
                    print("⚠️ 简化MCP测试部分成功")
                    print("🔧 自动化功能需要进一步调试")
                    print("="*50)
                    success = False
                    
            except Exception as e:
                logger.error("❌ 自动化测试异常: {}", str(e))
                success = False
        else:
            logger.warning("⚠️ 未检测到登录状态")
            print("\n" + "="*50)
            print("⚠️ 需要先登录微博")
            print("🔑 请在浏览器中完成登录后重新运行测试")
            print("="*50)
            success = False
        
        # 保持浏览器打开一段时间
        logger.info("🔍 保持浏览器打开5秒...")
        time.sleep(5)
        
    except Exception as e:
        logger.error("❌ 浏览器测试异常: {}", str(e))
        success = False
    
    finally:
        bm.close()
        logger.info("🔧 浏览器已关闭")
    
    if success:
        logger.info("🎉 简化MCP测试完全成功")
        sys.exit(0)
    else:
        logger.warning("⚠️ 简化MCP测试未完全成功")
        sys.exit(1)

except ImportError as e:
    print(f"❌ 导入错误: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 测试异常: {e}")
    sys.exit(1)
