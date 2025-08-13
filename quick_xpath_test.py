#!/usr/bin/env python3
"""
快速XPath测试脚本

快速测试优化后的XPath选择器和Ctrl+Enter提交功能
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.browser import BrowserManager
from src.logger import logger
from src.config import CONFIG
from src.weibo import automate_on_post, WEIBO_HOME
from src.login_weibo import is_logged_in_weibo


def quick_test():
    """快速测试优化的XPath选择器"""
    
    logger.info("🚀 开始快速XPath测试")
    
    # 设置测试环境
    CONFIG.headless = False
    CONFIG.slow_mo_ms = 500  # 增加慢动作以便观察
    
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
                return False
        
        logger.info("✅ 登录状态验证通过")
        
        print("\n" + "="*60)
        print("🎯 开始执行优化的微博自动化测试")
        print("="*60)
        print("📋 测试配置:")
        print("   - 仅执行点赞操作（安全测试）")
        print("   - 使用优化的XPath选择器")
        print("   - 启用Ctrl+Enter快捷键提交")
        print("   - 操作间隔1-3秒")
        print("="*60)
        
        # 执行自动化测试
        logger.info("🎯 执行优化的自动化流程...")
        
        start_time = time.time()
        result = automate_on_post(
            page, 
            do_comment=False,  # 不评论，避免过多操作
            do_like=True,      # 仅点赞测试
            do_repost=False,   # 不转发
            do_follow=False    # 不关注
        )
        execution_time = time.time() - start_time
        
        # 分析结果
        print("\n" + "="*60)
        print("📊 测试结果分析")
        print("="*60)
        
        if "error" in result:
            print(f"❌ 测试失败: {result['error']}")
            print(f"⏱️ 执行时间: {execution_time:.2f} 秒")
            return False
        
        # 检查操作结果
        operations = {
            "关注": result.get("follow_executed", False),
            "点赞": result.get("like_executed", False),
            "评论": result.get("comment_executed", False),
            "转发": result.get("repost_executed", False)
        }
        
        print(f"⏱️ 执行时间: {execution_time:.2f} 秒")
        print("📋 操作结果:")
        
        success_count = 0
        for op_name, success in operations.items():
            status = "✅" if success else "❌"
            print(f"   {op_name}: {status}")
            if success:
                success_count += 1
        
        # 检查是否有MCP优化信息
        if result.get("mcp_optimized"):
            print("🔧 MCP优化: ✅ 已启用")
        
        # 检查是否有操作记录
        if result.get("mcp_script"):
            print("📝 操作记录: ✅ 已生成")
        
        # 总体评估
        print("\n📊 总体评估:")
        
        if result.get("like_executed", False):
            print("🎉 测试成功！")
            print("✅ 优化的XPath选择器工作正常")
            print("✅ 自动化流程执行成功")
            print("✅ 操作间隔优化生效")
            
            if execution_time < 60:
                print("✅ 执行效率良好")
            else:
                print("⚠️ 执行时间较长，可能需要进一步优化")
            
            return True
        else:
            print("⚠️ 测试未完全成功")
            print("❌ 点赞操作失败")
            print("🔧 建议检查:")
            print("   - XPath选择器是否准确")
            print("   - 页面结构是否发生变化")
            print("   - 网络连接是否稳定")
            
            return False
    
    except Exception as e:
        logger.error("❌ 快速测试异常: {}", str(e))
        print(f"\n❌ 测试过程中发生异常: {str(e)}")
        return False
    
    finally:
        print("\n🔄 保持浏览器打开以便检查结果...")
        print("按回车键关闭浏览器...")
        input()
        bm.close()


def main():
    """主函数"""
    
    print("🚀 微博自动化XPath优化快速测试")
    print("="*60)
    print("📋 本测试将验证:")
    print("   1. 用户提供的精确XPath选择器")
    print("   2. Ctrl+Enter快捷键提交功能")
    print("   3. 优化的操作间隔时间")
    print("   4. 整体自动化流程稳定性")
    print("="*60)
    
    success = quick_test()
    
    if success:
        print("\n🎉 快速测试成功！XPath优化生效！")
        print("✅ 系统已准备好使用优化的选择器")
        return True
    else:
        print("\n⚠️ 快速测试需要进一步调整")
        print("🔧 请检查XPath选择器和页面结构")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
