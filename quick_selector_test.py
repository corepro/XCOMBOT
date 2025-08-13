#!/usr/bin/env python3
"""
快速选择器验证脚本

快速验证新添加的精确XPath选择器是否能正确定位元素
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.browser import BrowserManager
from src.logger import logger
from src.config import CONFIG
from src.weibo import WEIBO_HOME
from src.login_weibo import is_logged_in_weibo


def quick_test_selectors():
    """快速测试新的选择器"""
    logger.info("⚡ 快速验证新的微博元素选择器")
    
    # 新的精确选择器
    selectors_to_test = {
        "关注按钮": "/html/body/div[1]/div[2]/div[2]/div[2]/main/div[1]/div/div[2]/article/div[2]/header/div[2]/button",
        "点赞按钮": "//*[@id=\"app\"]/div[2]/div[2]/div[2]/main/div[1]/div/div[2]/article/footer/div/div[1]/div/div[3]/div/button",
        "转发选项": "//*[@id=\"composerEle\"]/div[2]/div/div[3]/div/div[2]/label",
        "微博内容": "//*[@id=\"app\"]/div[2]/div[2]/div[2]/main/div[1]/div/div[2]/article/div[2]/div/div[1]/div"
    }
    
    # 设置配置
    CONFIG.headless = False
    CONFIG.slow_mo_ms = 300
    
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
        
        logger.info("✅ 登录状态正常")
        
        # 等待页面加载
        time.sleep(3)
        
        # 测试结果
        results = {}
        total_tests = len(selectors_to_test)
        successful_tests = 0
        
        # 逐个测试选择器
        for element_name, xpath in selectors_to_test.items():
            logger.info("🔍 测试 {}: {}", element_name, xpath)
            
            try:
                # 尝试定位元素
                element = page.query_selector(f"xpath={xpath}")
                
                if element:
                    # 检查元素状态
                    is_visible = element.is_visible()
                    is_attached = element.is_attached()
                    
                    # 获取元素信息
                    element_info = {
                        "found": True,
                        "visible": is_visible,
                        "attached": is_attached,
                        "text": "",
                        "position": None
                    }
                    
                    try:
                        text = element.inner_text() or element.text_content() or ""
                        element_info["text"] = text[:50] + "..." if len(text) > 50 else text
                    except:
                        pass
                    
                    try:
                        box = element.bounding_box()
                        if box:
                            element_info["position"] = f"({box['x']:.0f}, {box['y']:.0f})"
                    except:
                        pass
                    
                    results[element_name] = element_info
                    
                    if is_visible and is_attached:
                        successful_tests += 1
                        logger.info("   ✅ 成功定位 - 可见: {}, 位置: {}", 
                                  is_visible, element_info["position"])
                        if element_info["text"]:
                            logger.info("   📝 元素文本: {}", element_info["text"])
                    else:
                        logger.warning("   ⚠️ 元素找到但状态异常 - 可见: {}, 附着: {}", 
                                     is_visible, is_attached)
                else:
                    results[element_name] = {
                        "found": False,
                        "error": "元素未找到"
                    }
                    logger.error("   ❌ 元素未找到")
                    
            except Exception as e:
                results[element_name] = {
                    "found": False,
                    "error": str(e)
                }
                logger.error("   ❌ 测试异常: {}", str(e))
            
            # 短暂等待
            time.sleep(1)
        
        # 生成快速报告
        success_rate = (successful_tests / total_tests) * 100
        
        print("\n" + "="*60)
        print("⚡ 快速选择器验证结果")
        print("="*60)
        print(f"📊 总体统计: {successful_tests}/{total_tests} 成功 ({success_rate:.1f}%)")
        print("")
        
        for element_name, result in results.items():
            if result["found"]:
                if result.get("visible", False):
                    status = "✅ 完美"
                else:
                    status = "⚠️ 找到但不可见"
                print(f"   {element_name}: {status}")
                if result.get("text"):
                    print(f"      文本: {result['text']}")
                if result.get("position"):
                    print(f"      位置: {result['position']}")
            else:
                print(f"   {element_name}: ❌ 失败 - {result.get('error', '未知错误')}")
        
        print("")
        
        if success_rate >= 75:
            print("🎉 选择器更新成功！大部分元素都能正确定位")
            print("💡 建议：可以开始使用更新后的自动化功能")
        elif success_rate >= 50:
            print("⚠️ 选择器部分有效，需要进一步调整")
            print("💡 建议：检查失败的选择器，可能需要更新XPath")
        else:
            print("❌ 选择器更新效果不佳")
            print("💡 建议：重新检查页面结构，获取最新的XPath")
        
        print("="*60)
        
        return success_rate >= 75
        
    except Exception as e:
        logger.error("❌ 快速测试异常: {}", str(e))
        return False
        
    finally:
        # 保持浏览器打开5秒观察
        logger.info("🔍 保持浏览器打开5秒...")
        time.sleep(5)
        bm.close()


def main():
    """主函数"""
    logger.info("🚀 启动快速选择器验证")
    
    success = quick_test_selectors()
    
    if success:
        print("\n✅ 快速验证通过！新选择器工作正常")
        print("🎯 下一步：运行完整的自动化测试")
        print("   python advanced_weibo_test.py --quick")
    else:
        print("\n❌ 快速验证未通过，需要调整选择器")
        print("🔧 建议：检查XPath路径或页面结构变化")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
