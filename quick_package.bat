@echo off
chcp 65001 >nul
title XComBot 快速打包工具

echo.
echo ╔══════════════════════════════════════╗
echo ║        XComBot 快速打包工具          ║
echo ║     一键生成Windows可执行文件        ║
echo ╚══════════════════════════════════════╝
echo.

echo 🔍 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或未添加到PATH
    echo 💡 请先安装Python 3.8+并添加到系统PATH
    echo.
    pause
    exit /b 1
)

echo ✅ Python环境检查通过
echo.

echo 🔧 激活虚拟环境...
if exist "venv_new\Scripts\activate.bat" (
    call "venv_new\Scripts\activate.bat"
    echo ✅ 虚拟环境已激活
) else (
    echo ⚠️  未找到虚拟环境，使用系统Python
)
echo.

echo 📦 安装/更新PyInstaller...
pip install --upgrade pyinstaller setuptools wheel
if errorlevel 1 (
    echo ❌ PyInstaller安装失败
    echo 💡 请检查网络连接或尝试使用国内镜像源
    echo    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pyinstaller
    pause
    exit /b 1
)
echo ✅ PyInstaller安装完成
echo.

echo 🧹 清理之前的构建文件...
if exist "dist" rmdir /s /q "dist" 2>nul
if exist "build" rmdir /s /q "build" 2>nul
echo ✅ 清理完成
echo.

echo 🔨 开始打包...
echo ⏳ 这可能需要几分钟时间，请耐心等待...
echo.

pyinstaller --clean --noconfirm ^
    --onefile ^
    --windowed ^
    --name="XComBot" ^
    --add-data="config/config.example.json;config" ^
    --add-data="data/comments.txt;data" ^
    --add-data="src;src" ^
    --hidden-import="tkinter" ^
    --hidden-import="tkinter.ttk" ^
    --hidden-import="ttkbootstrap" ^
    --hidden-import="ttkbootstrap.constants" ^
    --hidden-import="playwright" ^
    --hidden-import="playwright.sync_api" ^
    --hidden-import="loguru" ^
    --hidden-import="pydantic" ^
    --hidden-import="requests" ^
    --hidden-import="aiohttp" ^
    --exclude-module="matplotlib" ^
    --exclude-module="numpy" ^
    --exclude-module="pandas" ^
    --exclude-module="scipy" ^
    --exclude-module="PIL" ^
    --exclude-module="cv2" ^
    --exclude-module="tensorflow" ^
    --exclude-module="torch" ^
    start_ui.py

if errorlevel 1 (
    echo.
    echo ❌ 打包失败！
    echo 💡 可能的解决方案:
    echo    1. 检查是否缺少依赖模块
    echo    2. 尝试在虚拟环境中打包
    echo    3. 使用完整打包脚本: python package_exe_complete.py
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
echo   - 确保网络连接正常
echo.
echo 🔒 隐私保护:
echo   - 所有数据仅保存在本地
echo   - 不会上传任何个人信息
echo.
echo 版本: 1.0.0
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
echo ║            打包完成！                ║
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
echo 🎉 打包成功完成！
echo.
pause
