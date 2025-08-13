#!/usr/bin/env python3
"""
XComBot 打包问题诊断和修复工具
解决常见的打包问题和运行时错误
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import json


def print_section(title):
    """打印章节标题"""
    print(f"\n{'='*60}")
    print(f"🔧 {title}")
    print('='*60)


def check_python_environment():
    """检查Python环境"""
    print_section("Python环境检查")
    
    # Python版本
    version = sys.version_info
    print(f"Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version < (3, 8):
        print("❌ Python版本过低，需要3.8+")
        return False
    else:
        print("✅ Python版本符合要求")
    
    # 虚拟环境检查
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ 当前在虚拟环境中")
        print(f"   虚拟环境路径: {sys.prefix}")
    else:
        print("⚠️  当前不在虚拟环境中")
        print("   建议: 在虚拟环境中进行打包")
    
    # 检查pip
    try:
        import pip
        print(f"✅ pip版本: {pip.__version__}")
    except ImportError:
        print("❌ pip未安装")
        return False
    
    return True


def check_dependencies():
    """检查依赖包"""
    print_section("依赖包检查")
    
    required_packages = [
        'playwright',
        'pydantic', 
        'loguru',
        'ttkbootstrap',
        'requests',
        'aiohttp'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  缺少依赖包: {missing_packages}")
        print("修复命令:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True


def check_pyinstaller():
    """检查PyInstaller"""
    print_section("PyInstaller检查")
    
    try:
        import PyInstaller
        print(f"✅ PyInstaller版本: {PyInstaller.__version__}")
        
        # 检查PyInstaller命令
        result = subprocess.run(['pyinstaller', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ PyInstaller命令可用: {result.stdout.strip()}")
        else:
            print("❌ PyInstaller命令不可用")
            return False
            
    except ImportError:
        print("❌ PyInstaller未安装")
        print("修复命令: pip install pyinstaller")
        return False
    
    return True


def check_project_structure():
    """检查项目结构"""
    print_section("项目结构检查")
    
    required_files = {
        'app.py': '主程序入口',
        'start_ui.py': 'UI启动文件',
        'src/': '源代码目录',
        'src/ui_bootstrap.py': 'UI模块',
        'src/browser.py': '浏览器模块',
        'src/config.py': '配置模块',
        'config/config.example.json': '配置示例',
        'data/comments.txt': '评论数据',
        'requirements.txt': '依赖列表'
    }
    
    missing_files = []
    
    for file_path, description in required_files.items():
        if Path(file_path).exists():
            print(f"✅ {file_path} - {description}")
        else:
            print(f"❌ {file_path} - {description} (缺失)")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️  缺少必要文件: {missing_files}")
        return False
    
    return True


def fix_import_issues():
    """修复导入问题"""
    print_section("修复导入问题")
    
    # 检查__init__.py文件
    src_init = Path('src/__init__.py')
    if not src_init.exists():
        print("📝 创建 src/__init__.py")
        src_init.touch()
        print("✅ src/__init__.py 已创建")
    
    # 检查反检测模块
    anti_detection_init = Path('src/anti_detection/__init__.py')
    if not anti_detection_init.exists() and Path('src/anti_detection').exists():
        print("📝 创建 src/anti_detection/__init__.py")
        anti_detection_init.touch()
        print("✅ src/anti_detection/__init__.py 已创建")
    
    return True


def create_fixed_spec():
    """创建修复的spec文件"""
    print_section("创建修复的spec文件")
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# 项目根目录
project_root = Path.cwd()

# 数据文件
datas = [
    (str(project_root / 'config' / 'config.example.json'), 'config'),
    (str(project_root / 'data' / 'comments.txt'), 'data'),
    (str(project_root / 'src'), 'src'),
]

# 隐藏导入 - 包含所有可能需要的模块
hiddenimports = [
    # 基础模块
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.filedialog',
    
    # UI框架
    'ttkbootstrap',
    'ttkbootstrap.constants',
    'ttkbootstrap.style',
    'ttkbootstrap.themes',
    
    # 浏览器自动化
    'playwright',
    'playwright.sync_api',
    'playwright._impl',
    'playwright._impl._api_structures',
    'playwright._impl._browser',
    'playwright._impl._page',
    
    # 配置和日志
    'pydantic',
    'pydantic.fields',
    'pydantic.main',
    'pydantic_settings',
    'loguru',
    
    # 网络请求
    'requests',
    'requests.adapters',
    'requests.auth',
    'aiohttp',
    'aiohttp.client',
    'urllib3',
    
    # 系统模块
    'pathlib',
    'threading',
    'queue',
    'json',
    'time',
    'random',
    'typing',
    'dataclasses',
    'enum',
    'functools',
    'itertools',
    'collections',
    'os',
    'sys',
    'subprocess',
    'shutil',
    
    # 项目模块
    'src',
    'src.ui_bootstrap',
    'src.browser',
    'src.config',
    'src.logger',
    'src.login',
    'src.login_weibo',
    'src.login_xhs',
    'src.login_zhihu',
    'src.login_toutiao',
    'src.run_tasks',
    'src.weibo',
    'src.xhs',
    'src.zhihu',
    'src.toutiao',
    'src.comments',
    'src.humanize',
    'src.monitor',
    'src.anti_detection',
    'src.anti_detection.basic',
    'src.anti_detection.enhanced',
    'src.anti_detection.extreme',
]

# 排除模块
excludes = [
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'PIL',
    'cv2',
    'tensorflow',
    'torch',
    'jupyter',
    'notebook',
    'IPython',
    'pytest',
    'sphinx',
    'setuptools',
    'distutils',
]

# 分析
a = Analysis(
    ['start_ui.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='XComBot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    
    with open('XComBot_fixed.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ 修复的spec文件已创建: XComBot_fixed.spec")
    return True


def run_diagnostics():
    """运行完整诊断"""
    print("🔍 XComBot 打包问题诊断工具")
    print("=" * 60)
    
    issues_found = []
    
    # 检查Python环境
    if not check_python_environment():
        issues_found.append("Python环境")
    
    # 检查依赖
    if not check_dependencies():
        issues_found.append("依赖包")
    
    # 检查PyInstaller
    if not check_pyinstaller():
        issues_found.append("PyInstaller")
    
    # 检查项目结构
    if not check_project_structure():
        issues_found.append("项目结构")
    
    # 修复导入问题
    fix_import_issues()
    
    # 创建修复的spec文件
    create_fixed_spec()
    
    # 总结
    print_section("诊断总结")
    
    if issues_found:
        print("❌ 发现以下问题:")
        for issue in issues_found:
            print(f"   - {issue}")
        print("\n💡 建议:")
        print("   1. 解决上述问题后重新打包")
        print("   2. 使用修复的spec文件: pyinstaller XComBot_fixed.spec")
        print("   3. 或使用快速打包脚本: quick_package.bat")
        return False
    else:
        print("✅ 所有检查通过！")
        print("\n💡 可以开始打包:")
        print("   1. 使用快速脚本: quick_package.bat")
        print("   2. 使用完整脚本: python package_exe_complete.py")
        print("   3. 使用修复的spec: pyinstaller XComBot_fixed.spec")
        return True


def main():
    """主函数"""
    try:
        success = run_diagnostics()
        
        print("\n" + "="*60)
        if success:
            print("🎉 诊断完成，环境正常！")
        else:
            print("⚠️  发现问题，请按建议修复")
        print("="*60)
        
        return success
        
    except Exception as e:
        print(f"\n❌ 诊断过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    input("\n按回车键退出...")
    sys.exit(0 if success else 1)
