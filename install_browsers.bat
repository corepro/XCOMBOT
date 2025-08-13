@echo off
chcp 65001 >nul
title XComBot 浏览器驱动安装工具

echo.
echo ╔══════════════════════════════════════╗
echo ║      XComBot 浏览器驱动安装工具      ║
echo ║        解决浏览器启动问题            ║
echo ╚══════════════════════════════════════╝
echo.

echo 🔍 检查系统环境...

:: 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或未添加到PATH
    echo.
    echo 💡 解决方案:
    echo    1. 安装Python 3.8+
    echo    2. 或者使用系统Chrome浏览器（推荐）
    echo.
    goto :check_chrome
) else (
    echo ✅ Python环境可用
)

echo.
echo 📦 安装Playwright浏览器驱动...
echo ⏳ 这可能需要几分钟时间，请耐心等待...

:: 尝试安装Playwright浏览器
python -m playwright install chromium
if errorlevel 1 (
    echo ❌ Playwright浏览器安装失败
    echo.
    goto :check_chrome
) else (
    echo ✅ Playwright浏览器安装成功
    echo.
    goto :success
)

:check_chrome
echo 🔍 检查系统Chrome浏览器...

:: 检查常见的Chrome安装路径
set "CHROME_FOUND=0"

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    echo ✅ 找到Chrome: C:\Program Files\Google\Chrome\Application\chrome.exe
    set "CHROME_FOUND=1"
)

if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    echo ✅ 找到Chrome: C:\Program Files (x86)\Google\Chrome\Application\chrome.exe
    set "CHROME_FOUND=1"
)

if exist "%USERPROFILE%\AppData\Local\Google\Chrome\Application\chrome.exe" (
    echo ✅ 找到Chrome: %USERPROFILE%\AppData\Local\Google\Chrome\Application\chrome.exe
    set "CHROME_FOUND=1"
)

if "%CHROME_FOUND%"=="1" (
    echo.
    echo ✅ 系统Chrome浏览器可用
    echo 💡 XComBot将自动使用系统Chrome浏览器
    goto :success
) else (
    echo ❌ 未找到系统Chrome浏览器
    echo.
    goto :install_chrome
)

:install_chrome
echo 💡 建议安装Chrome浏览器:
echo.
echo 📥 自动下载Chrome浏览器...
echo 1. 正在打开Chrome下载页面...

:: 打开Chrome下载页面
start https://www.google.com/chrome/

echo.
echo 📋 手动安装步骤:
echo    1. 在打开的页面中下载Chrome
echo    2. 安装Chrome到默认位置
echo    3. 重新运行XComBot程序
echo.
goto :end

:success
echo.
echo ╔══════════════════════════════════════╗
echo ║            安装完成！                ║
echo ╚══════════════════════════════════════╝
echo.
echo ✅ 浏览器环境已准备就绪
echo 🚀 现在可以正常使用XComBot了
echo.
echo 💡 使用提示:
echo    - 如果仍有问题，请重启XComBot
echo    - 确保网络连接正常
echo    - 建议关闭其他浏览器实例
echo.

:end
echo 按任意键退出...
pause >nul
