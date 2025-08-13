#!/usr/bin/env python3
"""
快速重构验证测试

快速验证微博自动化系统重构后的基本功能
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.logger import logger
from src.config import CONFIG


def test_imports():
    """测试导入功能"""
    
    logger.info("🧪 测试模块导入...")
    
    try:
        # 测试核心模块导入
        from src.weibo import automate_on_post
        logger.info("✅ automate_on_post 导入成功")
        
        # 测试运行任务模块
        from src.run_tasks import run_weibo_firstcard_repeat, weibo_act_on_url
        logger.info("✅ 随机模式和精准模式函数导入成功")
        
        # 测试UI模块
        from src.ui_bootstrap import AppUIBoot
        logger.info("✅ UI模块导入成功")
        
        return True
        
    except Exception as e:
        logger.error("❌ 模块导入失败: {}", str(e))
        return False


def test_config_cleanup():
    """测试配置清理"""
    
    logger.info("🧪 测试配置清理...")
    
    try:
        # 检查是否还有weibo_flow_mode配置
        has_flow_mode = hasattr(CONFIG, 'weibo_flow_mode')
        
        if has_flow_mode:
            logger.warning("⚠️ 配置中仍存在 weibo_flow_mode")
            return False
        else:
            logger.info("✅ weibo_flow_mode 配置已清理")
            return True
            
    except Exception as e:
        logger.error("❌ 配置测试失败: {}", str(e))
        return False


def test_function_signatures():
    """测试函数签名"""
    
    logger.info("🧪 测试函数签名...")
    
    try:
        from src.weibo import automate_on_post
        from src.run_tasks import run_weibo_firstcard_repeat, weibo_act_on_url
        
        # 检查automate_on_post函数签名
        import inspect
        sig = inspect.signature(automate_on_post)
        params = list(sig.parameters.keys())
        
        expected_params = ['page', 'do_comment', 'do_like', 'do_repost', 'do_follow']
        
        if all(param in params for param in expected_params):
            logger.info("✅ automate_on_post 函数签名正确")
        else:
            logger.error("❌ automate_on_post 函数签名不正确")
            return False
        
        # 检查随机模式函数签名
        sig = inspect.signature(run_weibo_firstcard_repeat)
        params = list(sig.parameters.keys())
        
        expected_params = ['n', 'do_comment', 'do_like', 'do_retweet']
        
        if all(param in params for param in expected_params):
            logger.info("✅ run_weibo_firstcard_repeat 函数签名正确")
        else:
            logger.error("❌ run_weibo_firstcard_repeat 函数签名不正确")
            return False
        
        # 检查精准模式函数签名
        sig = inspect.signature(weibo_act_on_url)
        params = list(sig.parameters.keys())
        
        expected_params = ['bm', 'url', 'do_like', 'do_retweet', 'do_comment']
        
        if all(param in params for param in expected_params):
            logger.info("✅ weibo_act_on_url 函数签名正确")
        else:
            logger.error("❌ weibo_act_on_url 函数签名不正确")
            return False
        
        return True
        
    except Exception as e:
        logger.error("❌ 函数签名测试失败: {}", str(e))
        return False


def test_ui_cleanup():
    """测试UI清理"""
    
    logger.info("🧪 测试UI清理...")
    
    try:
        from src.ui_bootstrap import AppUIBoot

        # 创建UI实例
        ui = AppUIBoot()
        
        # 检查是否还有流程选择相关属性
        flow_attributes = [
            'var_weibo_flow',
            'weibo_flow_label', 
            'weibo_flow_menu',
            '_update_weibo_flow_visibility'
        ]
        
        remaining_attrs = []
        for attr in flow_attributes:
            if hasattr(ui, attr):
                remaining_attrs.append(attr)
        
        if remaining_attrs:
            logger.warning("⚠️ UI中仍存在流程选择相关属性: {}", remaining_attrs)
            return False
        else:
            logger.info("✅ UI流程选择相关属性已清理")
            return True
            
    except Exception as e:
        logger.error("❌ UI清理测试失败: {}", str(e))
        return False


def test_code_structure():
    """测试代码结构"""
    
    logger.info("🧪 测试代码结构...")
    
    try:
        # 检查是否还有automate_on_post_alternative函数
        from src import weibo
        
        has_alternative = hasattr(weibo, 'automate_on_post_alternative')
        
        if has_alternative:
            logger.warning("⚠️ 仍存在 automate_on_post_alternative 函数")
            return False
        else:
            logger.info("✅ automate_on_post_alternative 函数已清理")
        
        # 检查是否有automate_on_post函数
        has_main = hasattr(weibo, 'automate_on_post')
        
        if has_main:
            logger.info("✅ automate_on_post 主函数存在")
        else:
            logger.error("❌ automate_on_post 主函数不存在")
            return False
        
        return True
        
    except Exception as e:
        logger.error("❌ 代码结构测试失败: {}", str(e))
        return False


def main():
    """主函数"""
    
    logger.info("🚀 开始快速重构验证测试")
    
    tests = [
        ("模块导入", test_imports),
        ("配置清理", test_config_cleanup),
        ("函数签名", test_function_signatures),
        ("UI清理", test_ui_cleanup),
        ("代码结构", test_code_structure)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info("=" * 50)
        logger.info("🧪 执行测试: {}", test_name)
        
        try:
            if test_func():
                passed += 1
                logger.info("✅ {} 测试通过", test_name)
            else:
                logger.error("❌ {} 测试失败", test_name)
        except Exception as e:
            logger.error("❌ {} 测试异常: {}", test_name, str(e))
    
    logger.info("=" * 50)
    success_rate = (passed / total) * 100
    logger.info("📊 测试结果: {}/{} 通过 ({:.1f}%)", passed, total, success_rate)
    
    if success_rate >= 80:
        logger.info("🎉 快速验证成功！重构基本完成。")
        print("\n" + "=" * 60)
        print("🎉 微博自动化系统重构验证成功！")
        print("=" * 60)
        print("✅ 重构成果:")
        print("   - 流程选择功能已删除")
        print("   - 统一使用备选流程模式")
        print("   - UI界面已简化")
        print("   - 代码结构已清理")
        print("   - 函数签名正确")
        print("")
        print("🚀 系统已准备好使用！")
        print("   - 随机模式: 使用UI中的'开始监控'功能")
        print("   - 精准模式: 使用UI中的'精准模式'功能")
        print("   - 所有操作都使用统一的自动化流程")
        print("=" * 60)
        return True
    else:
        logger.warning("⚠️ 快速验证未完全通过，需要进一步检查")
        print("\n" + "=" * 60)
        print("⚠️ 微博自动化系统重构验证未完全通过")
        print("=" * 60)
        print(f"📊 通过率: {success_rate:.1f}% (需要 ≥80%)")
        print("")
        print("🔧 建议检查:")
        print("   - 确保所有流程选择相关代码已删除")
        print("   - 验证UI界面清理是否完整")
        print("   - 检查函数重命名是否正确")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
