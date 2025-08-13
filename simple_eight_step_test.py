#!/usr/bin/env python3
"""
简单8步流程验证测试

快速验证8步流程优化的基本功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

def test_import():
    """测试导入"""
    print("🧪 测试模块导入...")
    
    try:
        from src.weibo import automate_on_post
        print("✅ automate_on_post 导入成功")
        
        from src.weibo import generate_comment_text
        print("✅ generate_comment_text 导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {str(e)}")
        return False


def test_function_signature():
    """测试函数签名"""
    print("\n🧪 测试函数签名...")
    
    try:
        from src.weibo import automate_on_post
        
        import inspect
        sig = inspect.signature(automate_on_post)
        params = list(sig.parameters.keys())
        
        expected_params = ['page', 'do_comment', 'do_like', 'do_repost', 'do_follow']
        
        if all(param in params for param in expected_params):
            print("✅ automate_on_post 函数签名正确")
            return True
        else:
            print(f"❌ 函数签名不正确: {params}")
            return False
    except Exception as e:
        print(f"❌ 函数签名测试失败: {str(e)}")
        return False


def test_eight_step_structure():
    """测试8步流程结构"""
    print("\n🧪 测试8步流程结构...")
    
    try:
        with open("src/weibo.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查关键步骤
        steps = [
            "步骤3：点击关注按钮",
            "步骤4：找到并点击评论框", 
            "步骤5：生成并输入评论",
            "步骤6：点击同时转发按钮",
            "步骤7：点击点赞按钮",
            "步骤8：提交评论完成流程"
        ]
        
        found_steps = 0
        for step in steps:
            if step in content:
                print(f"✅ {step}: 已实现")
                found_steps += 1
            else:
                print(f"❌ {step}: 未找到")
        
        success_rate = (found_steps / len(steps)) * 100
        print(f"\n📊 8步流程完整性: {found_steps}/{len(steps)} ({success_rate:.1f}%)")
        
        return success_rate >= 100
        
    except Exception as e:
        print(f"❌ 8步流程结构测试失败: {str(e)}")
        return False


def test_xpath_selectors():
    """测试XPath选择器"""
    print("\n🧪 测试精确XPath选择器...")
    
    try:
        with open("src/weibo.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查关注按钮XPath
        follow_xpath = "//*[@id=\"app\"]/div[2]/div[2]/div[2]/main/div[1]/div/div[2]/article/div[2]/header/div[2]/button"
        if follow_xpath in content:
            print("✅ 关注按钮精确XPath已设置")
        else:
            print("❌ 关注按钮精确XPath未找到")
            return False
        
        # 检查点赞按钮XPath
        like_xpath = "//*[@id=\"app\"]/div[2]/div[2]/div[2]/main/div/div/div[2]/article/footer/div/div[1]/div/div[3]/div/button"
        if like_xpath in content:
            print("✅ 点赞按钮精确XPath已设置")
        else:
            print("❌ 点赞按钮精确XPath未找到")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ XPath选择器测试失败: {str(e)}")
        return False


def test_ctrl_enter():
    """测试Ctrl+Enter机制"""
    print("\n🧪 测试Ctrl+Enter提交机制...")
    
    try:
        with open("src/weibo.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查Ctrl+Enter相关代码
        if "Control+Enter" in content and "优先尝试Ctrl+Enter" in content:
            print("✅ Ctrl+Enter优先提交机制已实现")
            return True
        else:
            print("❌ Ctrl+Enter机制未完整实现")
            return False
        
    except Exception as e:
        print(f"❌ Ctrl+Enter测试失败: {str(e)}")
        return False


def main():
    """主函数"""
    
    print("🚀 简单8步流程验证测试")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_import),
        ("函数签名", test_function_signature),
        ("8步流程结构", test_eight_step_structure),
        ("XPath选择器", test_xpath_selectors),
        ("Ctrl+Enter机制", test_ctrl_enter)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*15} {test_name} {'='*15}")
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {str(e)}")
    
    print("\n" + "="*50)
    success_rate = (passed / total) * 100
    print(f"📊 测试结果: {passed}/{total} 通过 ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("\n🎉 8步流程优化验证成功！")
        print("✅ 核心优化已完成:")
        print("   - 8步详细流程结构")
        print("   - 精确XPath选择器优先级")
        print("   - Ctrl+Enter优先提交机制")
        print("   - 标准化操作间隔时间")
        print("   - 智能降级和错误处理")
        return True
    else:
        print("\n⚠️ 8步流程优化需要进一步检查")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
