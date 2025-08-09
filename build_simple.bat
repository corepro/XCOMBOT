@echo off
chcp 65001 >nul
echo ========================================
echo XComBot 简易打包脚本
echo ========================================
echo.

echo 🔍 检查Python环境...
python --version
if errorlevel 1 (
    echo ❌ Python未安装或未添加到PATH
    echo 请先安装Python 3.8+
    pause
    exit /b 1
)

echo.
echo 📦 安装PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo ❌ PyInstaller安装失败
    pause
    exit /b 1
)

echo.
echo 🧹 清理之前的构建文件...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del "*.spec"

echo.
echo 🔨 开始打包...
pyinstaller --onefile --windowed --name="XComBot" ^
    --add-data="config/config.example.json;config" ^
    --add-data="data/comments.txt;data" ^
    --add-data="src;src" ^
    --hidden-import="tkinter" ^
    --hidden-import="ttkbootstrap" ^
    --hidden-import="playwright" ^
    --hidden-import="loguru" ^
    --exclude-module="matplotlib" ^
    --exclude-module="numpy" ^
    --exclude-module="pandas" ^
    app.py

if errorlevel 1 (
    echo ❌ 打包失败
    pause
    exit /b 1
)

echo.
echo 📋 创建安装脚本...
echo @echo off > "dist\install.bat"
echo echo 正在安装XComBot... >> "dist\install.bat"
echo if not exist "%%USERPROFILE%%\XComBot" mkdir "%%USERPROFILE%%\XComBot" >> "dist\install.bat"
echo copy "XComBot.exe" "%%USERPROFILE%%\XComBot\\" >> "dist\install.bat"
echo echo 安装完成！程序位置: %%USERPROFILE%%\XComBot\XComBot.exe >> "dist\install.bat"
echo pause >> "dist\install.bat"

echo.
echo 📖 创建使用说明...
echo XComBot - 多平台社交媒体自动化工具 > "dist\使用说明.txt"
echo. >> "dist\使用说明.txt"
echo 1. 双击 XComBot.exe 启动程序 >> "dist\使用说明.txt"
echo 2. 首次使用需要登录各个平台 >> "dist\使用说明.txt"
echo 3. 选择反爬虫模式（建议选择"增强"） >> "dist\使用说明.txt"
echo 4. 配置操作参数后开始使用 >> "dist\使用说明.txt"
echo. >> "dist\使用说明.txt"
echo 注意：首次运行可能需要下载浏览器驱动 >> "dist\使用说明.txt"

echo.
echo ✅ 打包完成！
echo ========================================
echo 📁 输出目录: dist\
echo 📋 文件列表:
dir /b "dist\"
echo.
echo 💡 使用方法:
echo    1. 进入 dist 目录
echo    2. 双击 XComBot.exe 运行
echo    3. 或运行 install.bat 安装到用户目录
echo ========================================
echo.
pause
