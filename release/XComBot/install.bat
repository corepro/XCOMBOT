@echo off
chcp 65001 >nul
echo ========================================
echo XComBot 安装脚本
echo ========================================
echo.

echo 正在创建程序目录...
if not exist "%USERPROFILE%\XComBot" mkdir "%USERPROFILE%\XComBot"

echo 正在复制程序文件...
copy "XComBot.exe" "%USERPROFILE%\XComBot\"
if errorlevel 1 (
    echo ❌ 复制程序文件失败
    pause
    exit /b 1
)

echo 正在创建桌面快捷方式...
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%USERPROFILE%\Desktop\XComBot.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%USERPROFILE%\XComBot\XComBot.exe" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%USERPROFILE%\XComBot" >> CreateShortcut.vbs
echo oLink.Description = "多平台社交媒体自动化工具" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript CreateShortcut.vbs >nul 2>&1
del CreateShortcut.vbs

echo.
echo ========================================
echo ✅ 安装完成！
echo 程序位置: %USERPROFILE%\XComBot\XComBot.exe
echo 桌面快捷方式已创建
echo ========================================
echo.
echo 💡 使用提示:
echo 1. 双击桌面的"XComBot"快捷方式启动程序
echo 2. 首次运行需要配置各平台登录信息
echo 3. 建议选择"增强"反爬虫模式
echo 4. 程序会自动创建配置和日志文件
echo.
pause
