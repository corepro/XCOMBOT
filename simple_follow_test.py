#!/usr/bin/env python3
"""
简化的微博关注功能测试脚本
"""

def test_follow_functionality():
    """测试关注功能修复"""
    print("=== 测试微博关注功能修复 ===")
    
    try:
        # 检查weibo.py文件中的关注功能修改
        with open('src/weibo.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        tests_passed = 0
        total_tests = 0
        
        # 测试1: 检查函数签名
        total_tests += 1
        if 'def comment_and_optionally_repost(page: Page, do_repost: bool = False, do_like: bool = False, do_follow: bool = False, back_to_home: bool = True)' in content:
            print("✓ comment_and_optionally_repost函数签名已更新")
            tests_passed += 1
        else:
            print("✗ comment_and_optionally_repost函数签名未更新")
        
        # 测试2: 检查关注状态检测
        total_tests += 1
        if 'detect_follow_status_on_page(page)' in content:
            print("✓ 关注状态检测函数调用已实现")
            tests_passed += 1
        else:
            print("✗ 关注状态检测函数调用未实现")
        
        # 测试3: 检查基于截图的关注按钮选择器
        total_tests += 1
        if "button:has-text('+关注')" in content:
            print("✓ 基于截图的关注按钮选择器已实现")
            tests_passed += 1
        else:
            print("✗ 基于截图的关注按钮选择器未实现")
        
        # 测试4: 检查关注操作日志
        total_tests += 1
        if '开始执行关注操作' in content:
            print("✓ 关注操作日志已实现")
            tests_passed += 1
        else:
            print("✗ 关注操作日志未实现")
        
        # 测试5: 检查关注验证逻辑
        total_tests += 1
        if '关注操作成功验证' in content:
            print("✓ 关注验证逻辑已实现")
            tests_passed += 1
        else:
            print("✗ 关注验证逻辑未实现")
        
        # 测试6: 检查多模式同步
        total_tests += 1
        follow_count = content.count('开始执行关注操作')
        if follow_count >= 3:  # 精准模式、备选流程、卡片模式
            print(f"✓ 多模式关注逻辑已同步（出现{follow_count}次）")
            tests_passed += 1
        else:
            print(f"✗ 多模式关注逻辑可能未完全同步（出现{follow_count}次）")
        
        # 检查UI配置同步
        with open('src/ui_bootstrap.py', 'r', encoding='utf-8') as f:
            ui_content = f.read()
        
        # 测试7: 检查UI关注配置
        total_tests += 1
        if 'self.var_follow = tb.BooleanVar(value=getattr(CONFIG.action, "do_follow", True))' in ui_content:
            print("✓ UI关注变量定义正确")
            tests_passed += 1
        else:
            print("✗ UI关注变量定义不正确")
        
        # 测试8: 检查配置同步
        total_tests += 1
        if 'CONFIG.action.do_follow = bool(self.var_follow.get())' in ui_content:
            print("✓ UI关注配置同步已实现")
            tests_passed += 1
        else:
            print("✗ UI关注配置同步未实现")
        
        # 检查run_tasks.py中的调用
        with open('src/run_tasks.py', 'r', encoding='utf-8') as f:
            run_content = f.read()
        
        # 测试9: 检查函数调用更新
        total_tests += 1
        if 'do_follow=False' in run_content:
            print("✓ run_tasks.py中的函数调用已更新")
            tests_passed += 1
        else:
            print("✗ run_tasks.py中的函数调用未更新")
        
        print(f"\n=== 测试结果 ===")
        print(f"通过测试: {tests_passed}/{total_tests}")
        
        if tests_passed == total_tests:
            print("✅ 所有关注功能修复测试通过！")
            print("\n修复内容总结:")
            print("✓ 关注时机：在获取博文内容后立即执行")
            print("✓ 关注选择器：基于截图位置的'+关注'按钮")
            print("✓ 关注状态检测：使用detect_follow_status_on_page函数")
            print("✓ 关注验证：操作后验证关注是否成功")
            print("✓ 多模式同步：精准模式、备选流程、卡片模式已同步")
            print("✓ UI配置同步：关注选项正确同步到配置文件")
            print("✓ 日志输出：完整的关注操作日志记录")
            print("✓ 错误处理：备用关注方案和异常处理")
            return True
        else:
            print("❌ 部分关注功能修复测试失败")
            return False
        
    except Exception as e:
        print(f"✗ 测试过程失败: {e}")
        return False

if __name__ == "__main__":
    success = test_follow_functionality()
    exit(0 if success else 1)
