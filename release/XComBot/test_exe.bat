@echo off
chcp 65001 >nul
echo ========================================
echo XComBot exe 测试脚本
echo ========================================
echo.

echo 🔍 检查exe文件...
if not exist "XComBot.exe" (
    echo ❌ 未找到 XComBot.exe 文件
    pause
    exit /b 1
)

echo ✅ 找到 XComBot.exe 文件
for %%A in (XComBot.exe) do echo 📏 文件大小: %%~zA 字节

echo.
echo 🧪 测试exe文件启动...
echo 注意：程序将启动GUI界面，请手动关闭测试
echo.
echo 按任意键开始测试...
pause >nul

echo 正在启动 XComBot.exe...
start "" "XComBot.exe"

echo.
echo 📋 测试说明:
echo 1. 如果程序正常启动并显示GUI界面，说明打包成功
echo 2. 如果出现错误，请检查日志文件
echo 3. 测试完成后请手动关闭程序窗口
echo.
echo ✅ 测试启动完成
pause
