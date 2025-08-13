@echo off
chcp 65001 >nul
title XComBot 修复并重新打包

echo.
echo ╔══════════════════════════════════════╗
echo ║       XComBot 修复并重新打包         ║
echo ║      解决 PIL/Pillow 依赖问题       ║
echo ╚══════════════════════════════════════╝
echo.

echo 🔧 激活虚拟环境...
if exist "venv_new\Scripts\activate.bat" (
    call "venv_new\Scripts\activate.bat"
    echo ✅ 虚拟环境已激活
) else (
    echo ⚠️  未找到虚拟环境，使用系统Python
)
echo.

echo 📦 确保 Pillow 已安装...
pip install Pillow
if errorlevel 1 (
    echo ❌ Pillow 安装失败
    pause
    exit /b 1
)
echo ✅ Pillow 安装完成
echo.

echo 🧹 清理之前的构建文件...
if exist "dist" rmdir /s /q "dist" 2>nul
if exist "build" rmdir /s /q "build" 2>nul
echo ✅ 清理完成
echo.

echo 🔨 使用修复的配置重新打包...
echo ⏳ 这可能需要几分钟时间，请耐心等待...
echo.

pyinstaller --clean --noconfirm XComBot_fixed.spec

if errorlevel 1 (
    echo.
    echo ❌ 打包失败！
    echo 💡 可能的解决方案:
    echo    1. 检查是否所有依赖都已安装
    echo    2. 尝试重新安装 ttkbootstrap: pip install --upgrade ttkbootstrap
    echo    3. 检查虚拟环境是否正确激活
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ 打包成功！
echo.

echo 📁 创建发布目录结构...
if not exist "dist\config" mkdir "dist\config"
if not exist "dist\data" mkdir "dist\data"

if exist "config\config.example.json" copy "config\config.example.json" "dist\config\" >nul
if exist "data\comments.txt" copy "data\comments.txt" "dist\data\" >nul

echo ✅ 文件复制完成
echo.

echo 📋 创建安装脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo title XComBot 安装程序
echo.
echo echo 📁 正在安装XComBot...
echo set "INSTALL_DIR=%%USERPROFILE%%\XComBot"
echo if not exist "%%INSTALL_DIR%%" mkdir "%%INSTALL_DIR%%"
echo copy "XComBot.exe" "%%INSTALL_DIR%%\" ^>nul
echo if exist "config" xcopy "config" "%%INSTALL_DIR%%\config\" /E /I /Y ^>nul
echo if exist "data" xcopy "data" "%%INSTALL_DIR%%\data\" /E /I /Y ^>nul
echo.
echo echo 🔗 创建桌面快捷方式...
echo powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%%USERPROFILE%%\Desktop\XComBot.lnk'^); $Shortcut.TargetPath = '%%INSTALL_DIR%%\XComBot.exe'; $Shortcut.WorkingDirectory = '%%INSTALL_DIR%%'; $Shortcut.Description = 'XComBot - 多平台社交媒体自动化工具'; $Shortcut.Save(^)"
echo.
echo echo ✅ 安装完成！
echo echo 📍 程序位置: %%INSTALL_DIR%%\XComBot.exe
echo echo 🖥️  桌面快捷方式已创建
echo echo.
echo pause
) > "dist\安装.bat"

echo ✅ 安装脚本创建完成
echo.

echo 📖 创建使用说明...
(
echo XComBot - 多平台社交媒体自动化工具
echo ========================================
echo.
echo 🚀 快速开始:
echo   1. 双击 "安装.bat" 进行安装
echo   2. 或直接双击 "XComBot.exe" 运行
echo.
echo ⚙️ 首次使用:
echo   1. 启动程序后选择平台
echo   2. 登录相应的社交媒体账号
echo   3. 配置反爬虫模式（建议选择"增强"）
echo   4. 设置操作参数后开始使用
echo.
echo 📋 支持平台:
echo   - 微博 (weibo.com^)
echo   - 知乎 (zhihu.com^)
echo   - 小红书 (xiaohongshu.com^)
echo   - 今日头条 (toutiao.com^)
echo   - Twitter/X (x.com^)
echo.
echo ⚠️ 注意事项:
echo   - 首次运行需要下载浏览器驱动
echo   - 可能需要添加到杀毒软件白名单
echo   - 建议在Windows 10/11上运行
echo.
echo 🔧 修复版本说明:
echo   - 修复了 PIL/Pillow 依赖问题
echo   - 确保 ttkbootstrap UI 框架正常工作
echo.
echo 版本: 1.0.1 (修复版^)
echo 构建时间: %date% %time%
) > "dist\使用说明.txt"

echo ✅ 使用说明创建完成
echo.

echo 📊 检查输出文件...
if exist "dist\XComBot.exe" (
    for %%F in ("dist\XComBot.exe") do (
        set /a "size=%%~zF/1024/1024"
        echo ✅ XComBot.exe - !size! MB
    )
) else (
    echo ❌ 未找到 XComBot.exe
)

echo.
echo ╔══════════════════════════════════════╗
echo ║            修复完成！                ║
echo ╚══════════════════════════════════════╝
echo.
echo 📁 输出目录: dist\
echo 📋 文件列表:
dir /b "dist\"
echo.
echo 💡 使用方法:
echo   1. 进入 dist 目录
echo   2. 双击 "安装.bat" 进行安装
echo   3. 或直接双击 "XComBot.exe" 运行
echo.
echo 🎉 PIL/Pillow 依赖问题已修复！
echo.
pause
