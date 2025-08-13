#!/usr/bin/env python3
"""
简化的关注和转发功能测试
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import CONFIG
from src.browser import BrowserManager
from src.logger import logger
from src.weibo import automate_on_post_alternative
from src.login_weibo import ensure_login_weibo

def simple_follow_test():
    """简化的关注和转发测试"""
    print("开始测试优化后的关注和转发功能...")
    
    # 设置配置
    CONFIG.platform = "weibo"
    CONFIG.weibo_flow_mode = "alternative"
    CONFIG.headless = False
    CONFIG.anti_detection_mode = "off"
    CONFIG.anti_detection_enabled = False
    
    bm = BrowserManager()
    try:
        bm.launch()
        bm.new_context(use_storage=True)
        page = bm.page
        assert page is not None
        
        # 确保登录
        ensure_login_weibo(page)
        
        # 测试关注功能
        print("测试关注功能...")
        result = automate_on_post_alternative(
            page, 
            do_comment=True,   # 启用评论
            do_like=True,      # 启用点赞
            do_repost=False,   # 不转发
            do_follow=True     # 启用关注测试
        )
        
        print("测试结果：")
        print(f"- 关注执行: {result.get('follow_executed', False)}")
        print(f"- 点赞执行: {result.get('like_executed', False)}")
        print(f"- 评论执行: {result.get('comment_executed', False)}")
        print(f"- 转发执行: {result.get('repost_executed', False)}")
        
        # 计算成功率
        operations = ["follow_executed", "like_executed", "comment_executed"]
        successful = sum(1 for op in operations if result.get(op, False))
        total = len(operations)
        success_rate = (successful / total * 100) if total > 0 else 0
        
        print(f"- 成功率: {success_rate:.1f}% ({successful}/{total})")
        
        if success_rate > 66.7:
            print("🎉 关注功能优化效果显著！")
        elif success_rate >= 66.7:
            print("✅ 关注功能优化保持了稳定性")
        else:
            print("⚠️ 关注功能需要进一步优化")
        
        print("测试完成！")
        
    except Exception as e:
        print(f"测试失败: {e}")
        logger.exception("关注功能测试失败: {}", e)
    finally:
        bm.close()

if __name__ == "__main__":
    simple_follow_test()
