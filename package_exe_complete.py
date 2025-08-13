#!/usr/bin/env python3
"""
XComBot 完整打包脚本 - 优化版
解决常见打包问题，生成高质量的可执行文件
"""

import os
import sys
import shutil
import subprocess
import json
from pathlib import Path
import time


def print_step(step_name, description=""):
    """打印步骤信息"""
    print(f"\n{'='*60}")
    print(f"🔧 {step_name}")
    if description:
        print(f"   {description}")
    print('='*60)


def check_environment():
    """检查打包环境"""
    print_step("环境检查", "检查Python版本和必要工具")
    
    # 检查Python版本
    python_version = sys.version_info
    print(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print("❌ Python版本过低，需要Python 3.8+")
        return False
    
    # 检查虚拟环境
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ 检测到虚拟环境")
    else:
        print("⚠️  未检测到虚拟环境，建议在虚拟环境中打包")
    
    # 检查必要文件
    required_files = [
        "app.py",
        "start_ui.py", 
        "src/",
        "config/config.example.json",
        "data/comments.txt",
        "requirements.txt"
    ]
    
    missing_files = []
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ 缺少: {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ 缺少必要文件: {missing_files}")
        return False
    
    return True


def install_build_dependencies():
    """安装打包依赖"""
    print_step("安装打包依赖", "安装PyInstaller和相关工具")
    
    dependencies = [
        "pyinstaller>=5.0",
        "setuptools",
        "wheel"
    ]
    
    for dep in dependencies:
        print(f"📦 安装 {dep}...")
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", dep
            ], capture_output=True, text=True, check=True)
            print(f"✅ {dep} 安装成功")
        except subprocess.CalledProcessError as e:
            print(f"❌ {dep} 安装失败: {e}")
            return False
    
    return True


def create_optimized_spec():
    """创建优化的spec文件"""
    print_step("创建配置文件", "生成优化的PyInstaller配置")
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# 项目根目录
project_root = Path.cwd()

# 数据文件配置
datas = [
    (str(project_root / 'config' / 'config.example.json'), 'config'),
    (str(project_root / 'data' / 'comments.txt'), 'data'),
    (str(project_root / 'src'), 'src'),
]

# 隐藏导入模块
hiddenimports = [
    # UI相关
    'tkinter',
    'tkinter.ttk',
    'ttkbootstrap',
    'ttkbootstrap.constants',
    'ttkbootstrap.style',
    
    # 浏览器自动化
    'playwright',
    'playwright.sync_api',
    'playwright._impl',
    
    # 日志和配置
    'loguru',
    'pydantic',
    'pydantic_settings',
    
    # 网络请求
    'requests',
    'aiohttp',
    'urllib3',
    
    # 系统和工具
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
    
    # 项目模块
    'src.ui_bootstrap',
    'src.browser',
    'src.config',
    'src.logger',
    'src.login',
    'src.run_tasks',
    'src.weibo',
    'src.xhs',
    'src.zhihu',
    'src.toutiao',
    'src.anti_detection',
]

# 排除的模块（减小文件大小）
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
]

# 分析配置
a = Analysis(
    ['start_ui.py'],  # 使用UI启动文件作为入口
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

# 创建PYZ
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# 创建可执行文件
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
    console=False,  # 隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if Path('icon.ico').exists() else None,
)
'''
    
    with open('XComBot_optimized.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ 优化配置文件创建完成: XComBot_optimized.spec")
    return True


def clean_build_dirs():
    """清理构建目录"""
    print_step("清理构建目录", "删除之前的构建文件")
    
    dirs_to_clean = ['dist', 'build', '__pycache__']
    files_to_clean = ['*.spec']
    
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            print(f"🧹 删除目录: {dir_name}")
            shutil.rmtree(dir_name)
    
    # 清理spec文件（除了我们刚创建的）
    for spec_file in Path('.').glob('*.spec'):
        if spec_file.name != 'XComBot_optimized.spec':
            print(f"🧹 删除文件: {spec_file}")
            spec_file.unlink()
    
    print("✅ 清理完成")


def build_executable():
    """构建可执行文件"""
    print_step("构建可执行文件", "使用PyInstaller生成exe")
    
    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        "--log-level=INFO",
        "XComBot_optimized.spec"
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    print("⏳ 构建中，请耐心等待...")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        build_time = time.time() - start_time
        print(f"✅ 构建成功！耗时: {build_time:.1f}秒")
        
        # 检查输出文件
        exe_path = Path("dist/XComBot.exe")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"📁 输出文件: {exe_path}")
            print(f"📏 文件大小: {size_mb:.1f} MB")
            return True
        else:
            print("❌ 未找到输出的exe文件")
            return False
            
    except subprocess.CalledProcessError as e:
        print("❌ 构建失败！")
        print("错误输出:")
        print(e.stderr)
        return False


def create_distribution_package():
    """创建发布包"""
    print_step("创建发布包", "生成完整的发布文件")
    
    dist_dir = Path("dist")
    
    # 复制必要的配置文件
    config_dir = dist_dir / "config"
    config_dir.mkdir(exist_ok=True)
    
    data_dir = dist_dir / "data" 
    data_dir.mkdir(exist_ok=True)
    
    # 复制配置文件
    if Path("config/config.example.json").exists():
        shutil.copy2("config/config.example.json", config_dir / "config.example.json")
        print("✅ 复制配置示例文件")
    
    # 复制数据文件
    if Path("data/comments.txt").exists():
        shutil.copy2("data/comments.txt", data_dir / "comments.txt")
        print("✅ 复制评论数据文件")
    
    return True


def create_installer():
    """创建安装脚本"""
    print_step("创建安装脚本", "生成用户友好的安装程序")
    
    installer_content = '''@echo off
chcp 65001 >nul
title XComBot 安装程序

echo.
echo ╔══════════════════════════════════════╗
echo ║          XComBot 安装程序            ║
echo ║     多平台社交媒体自动化工具         ║
echo ╚══════════════════════════════════════╝
echo.

echo 📁 正在创建程序目录...
set "INSTALL_DIR=%USERPROFILE%\\XComBot"
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo 📋 正在复制程序文件...
copy "XComBot.exe" "%INSTALL_DIR%\\" >nul
if exist "config" xcopy "config" "%INSTALL_DIR%\\config\\" /E /I /Y >nul
if exist "data" xcopy "data" "%INSTALL_DIR%\\data\\" /E /I /Y >nul

echo 🔗 正在创建桌面快捷方式...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\\Desktop\\XComBot.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\XComBot.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'XComBot - 多平台社交媒体自动化工具'; $Shortcut.Save()"

echo.
echo ✅ 安装完成！
echo.
echo 📍 程序位置: %INSTALL_DIR%\\XComBot.exe
echo 🖥️  桌面快捷方式已创建
echo.
echo 💡 使用提示:
echo    - 首次运行需要配置各平台登录
echo    - 建议选择"增强"反爬虫模式
echo    - 程序会自动下载所需的浏览器驱动
echo.
echo 按任意键退出...
pause >nul
'''
    
    with open('dist/安装.bat', 'w', encoding='gbk') as f:
        f.write(installer_content)
    
    print("✅ 安装脚本创建完成")
    return True


def main():
    """主函数"""
    print("🚀 XComBot 完整打包工具")
    print("=" * 60)
    print("📝 功能: 将Python项目打包成Windows可执行文件")
    print("🎯 目标: 生成独立运行的exe文件")
    print("=" * 60)
    
    try:
        # 1. 环境检查
        if not check_environment():
            print("❌ 环境检查失败")
            return False
        
        # 2. 安装依赖
        if not install_build_dependencies():
            print("❌ 依赖安装失败")
            return False
        
        # 3. 清理构建目录
        clean_build_dirs()
        
        # 4. 创建配置文件
        if not create_optimized_spec():
            print("❌ 配置文件创建失败")
            return False
        
        # 5. 构建可执行文件
        if not build_executable():
            print("❌ 构建失败")
            return False
        
        # 6. 创建发布包
        if not create_distribution_package():
            print("❌ 发布包创建失败")
            return False
        
        # 7. 创建安装脚本
        if not create_installer():
            print("❌ 安装脚本创建失败")
            return False
        
        # 成功完成
        print_step("打包完成", "所有步骤执行成功")
        
        print("🎉 打包成功完成！")
        print("\n📁 输出目录: dist/")
        print("📋 主要文件:")
        print("   ├── XComBot.exe        (主程序)")
        print("   ├── 安装.bat           (安装脚本)")
        print("   ├── config/            (配置文件)")
        print("   └── data/              (数据文件)")
        
        print("\n💡 使用方法:")
        print("   1. 进入 dist 目录")
        print("   2. 双击 '安装.bat' 进行安装")
        print("   3. 或直接双击 'XComBot.exe' 运行")
        
        print("\n⚠️  注意事项:")
        print("   - 首次运行需要下载浏览器驱动")
        print("   - 可能需要添加到杀毒软件白名单")
        print("   - 建议在Windows 10/11上运行")
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断操作")
        return False
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    
    print("\n" + "="*60)
    if success:
        print("🎊 打包流程全部完成！")
        print("📦 可执行文件已生成在 dist/ 目录中")
    else:
        print("💥 打包过程中出现错误")
        print("🔍 请检查上述错误信息并重试")
    print("="*60)
    
    input("\n按回车键退出...")
    sys.exit(0 if success else 1)
