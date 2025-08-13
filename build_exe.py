#!/usr/bin/env python3
"""
XComBot exe打包脚本
使用PyInstaller将Python项目打包成Windows可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def check_requirements():
    """检查打包环境"""
    print("检查打包环境...")
    
    # 检查Python版本
    python_version = sys.version_info
    print(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print("❌ Python版本过低，建议使用Python 3.8+")
        return False
    
    # 检查PyInstaller
    try:
        import PyInstaller
        print(f"PyInstaller版本: {PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller安装完成")
    
    # 检查必要文件
    required_files = [
        "app.py",
        "src/",
        "config/config.example.json",
        "data/comments.txt",
        "requirements.txt"
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"❌ 缺少必要文件: {file_path}")
            return False
        else:
            print(f"找到文件: {file_path}")
    
    return True


def create_spec_file():
    """创建PyInstaller spec文件"""
    print("📝 创建PyInstaller配置文件...")
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 分析主程序
a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config/config.example.json', 'config'),
        ('data/comments.txt', 'data'),
        ('src', 'src'),
    ],
    hiddenimports=[
        'tkinter',
        'ttkbootstrap',
        'playwright',
        'playwright.sync_api',
        'loguru',
        'requests',
        'json',
        'pathlib',
        'threading',
        'queue',
        'time',
        'random',
        'typing',
        'dataclasses',
        'enum',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
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
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 创建PYZ文件
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    console=False,  # 设置为False隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
'''
    
    with open('XComBot.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ 配置文件创建完成: XComBot.spec")


def install_dependencies():
    """安装打包依赖"""
    print("安装打包依赖...")
    
    # 安装PyInstaller和其他必要依赖
    dependencies = [
        "pyinstaller>=5.0",
        "auto-py-to-exe",  # 可选的GUI工具
    ]
    
    for dep in dependencies:
        print(f"安装 {dep}...")
        subprocess.run([sys.executable, "-m", "pip", "install", dep])
    
    print("✅ 依赖安装完成")


def build_exe():
    """构建exe文件"""
    print("🔨 开始构建exe文件...")
    
    # 清理之前的构建
    if Path("dist").exists():
        print("🧹 清理之前的构建文件...")
        shutil.rmtree("dist")
    
    if Path("build").exists():
        shutil.rmtree("build")
    
    # 使用PyInstaller构建
    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        "XComBot.spec"
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ exe文件构建成功！")
        
        # 检查输出文件
        exe_path = Path("dist/XComBot.exe")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"📁 输出文件: {exe_path}")
            print(f"📏 文件大小: {size_mb:.1f} MB")
        else:
            print("❌ 未找到输出的exe文件")
            return False
    else:
        print("❌ 构建失败！")
        print("错误输出:")
        print(result.stderr)
        return False
    
    return True


def create_installer_script():
    """创建安装脚本"""
    print("📋 创建安装脚本...")
    
    installer_script = '''@echo off
echo ========================================
echo XComBot 安装脚本
echo ========================================
echo.

echo 正在创建程序目录...
if not exist "%USERPROFILE%\\XComBot" mkdir "%USERPROFILE%\\XComBot"

echo 正在复制程序文件...
copy "XComBot.exe" "%USERPROFILE%\\XComBot\\"
copy "config" "%USERPROFILE%\\XComBot\\" /E /Y
copy "data" "%USERPROFILE%\\XComBot\\" /E /Y

echo 正在创建桌面快捷方式...
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%USERPROFILE%\\Desktop\\XComBot.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%USERPROFILE%\\XComBot\\XComBot.exe" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%USERPROFILE%\\XComBot" >> CreateShortcut.vbs
echo oLink.Description = "多平台社交媒体自动化工具" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript CreateShortcut.vbs
del CreateShortcut.vbs

echo.
echo ========================================
echo 安装完成！
echo 程序位置: %USERPROFILE%\\XComBot\\XComBot.exe
echo 桌面快捷方式已创建
echo ========================================
echo.
pause
'''
    
    with open('dist/install.bat', 'w', encoding='gbk') as f:
        f.write(installer_script)
    
    print("✅ 安装脚本创建完成: dist/install.bat")


def create_readme():
    """创建exe版本的README"""
    print("📖 创建exe版本说明文档...")
    
    readme_content = '''# XComBot - Windows可执行版本

## 🚀 快速开始

### 方法一：使用安装脚本（推荐）
1. 双击运行 `install.bat`
2. 安装脚本会自动：
   - 创建程序目录
   - 复制程序文件
   - 创建桌面快捷方式
3. 双击桌面的"XComBot"快捷方式启动程序

### 方法二：直接运行
1. 双击 `XComBot.exe` 直接运行
2. 首次运行会在同目录创建配置文件

## ⚙️ 配置说明

### 首次使用
1. 启动程序后，程序会自动创建配置文件
2. 根据需要修改 `config/config.json` 中的设置
3. 重启程序使配置生效

### 主要配置项
- **反爬虫模式**: 建议选择"增强"或"极限"
- **操作延时**: 建议保持默认值
- **评论模式**: 可选择"本地库"或"AI生成"

## 🔧 功能说明

### 支持平台
- 微博 (weibo.com)
- 知乎 (zhihu.com)
- 小红书 (xiaohongshu.com)
- 今日头条 (toutiao.com)
- Twitter/X (x.com)

### 主要功能
- 自动点赞
- 自动转发
- 自动评论
- 自动收藏
- 自动关注

## 📁 文件结构

```
XComBot/
├── XComBot.exe          # 主程序
├── config/              # 配置文件目录
│   └── config.json      # 主配置文件
├── data/                # 数据文件目录
│   └── comments.txt     # 评论库
├── logs/                # 日志文件目录（自动创建）
├── storage/             # 存储目录（自动创建）
└── traces/              # 调试文件目录（自动创建）
```

## ⚠️ 注意事项

1. **首次运行**: 需要安装浏览器驱动，程序会自动处理
2. **网络连接**: 确保网络连接正常
3. **杀毒软件**: 可能需要将程序添加到杀毒软件白名单
4. **系统要求**: Windows 10/11，建议4GB以上内存

## 🔒 隐私保护

- 所有登录信息仅保存在本地
- 不会上传任何个人数据
- 建议定期清理日志文件

## 🆘 故障排除

### 程序无法启动
1. 检查是否被杀毒软件拦截
2. 尝试以管理员身份运行
3. 检查系统是否缺少运行库

### 登录失败
1. 检查网络连接
2. 尝试手动登录网站
3. 清理浏览器缓存

### 操作失败
1. 检查反爬虫设置
2. 降低操作频率
3. 查看日志文件了解详情

## 📞 技术支持

如遇问题，请查看 `logs/` 目录下的日志文件，
或访问项目主页获取帮助。

---
版本: 2.0.0
构建时间: ''' + str(Path().cwd()) + '''
'''
    
    with open('dist/README.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("✅ 说明文档创建完成: dist/README.txt")


def main():
    """主函数"""
    print("XComBot exe打包工具")
    print("=" * 50)
    
    # 检查环境
    if not check_requirements():
        print("❌ 环境检查失败，请解决上述问题后重试")
        return False
    
    # 安装依赖
    install_dependencies()
    
    # 创建配置文件
    create_spec_file()
    
    # 构建exe
    if not build_exe():
        print("❌ 构建失败")
        return False
    
    # 创建附加文件
    create_installer_script()
    create_readme()
    
    print("\n打包完成！")
    print("=" * 50)
    print("📁 输出目录: dist/")
    print("📋 主要文件:")
    print("   - XComBot.exe      (主程序)")
    print("   - install.bat      (安装脚本)")
    print("   - README.txt       (使用说明)")
    print("\n💡 使用建议:")
    print("   1. 运行 install.bat 进行安装")
    print("   2. 或直接双击 XComBot.exe 运行")
    print("   3. 首次运行需要配置各平台登录")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
