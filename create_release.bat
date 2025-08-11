@echo off
chcp 65001 >nul
echo ========================================
echo XComBot 发布包创建脚本
echo ========================================
echo.

echo 🔍 检查必要文件...
if not exist "dist\XComBot.exe" (
    echo ❌ 未找到 dist\XComBot.exe
    echo 请先运行打包脚本
    pause
    exit /b 1
)

echo ✅ 找到主程序文件

echo.
echo 📦 创建发布目录...
if exist "release" rmdir /s /q "release"
mkdir "release"
mkdir "release\XComBot"

echo.
echo 📋 复制文件...
copy "dist\XComBot.exe" "release\XComBot\"
copy "dist\install.bat" "release\XComBot\"
copy "dist\使用说明.txt" "release\XComBot\"
copy "dist\test_exe.bat" "release\XComBot\"

echo.
echo 📄 创建版本信息...
echo XComBot v1.0.0 > "release\XComBot\版本信息.txt"
echo 构建时间: %date% %time% >> "release\XComBot\版本信息.txt"
echo. >> "release\XComBot\版本信息.txt"
echo 文件列表: >> "release\XComBot\版本信息.txt"
dir /b "release\XComBot\" >> "release\XComBot\版本信息.txt"

echo.
echo 📁 发布包内容:
dir /b "release\XComBot\"

echo.
echo ✅ 发布包创建完成！
echo 📂 位置: release\XComBot\
echo.
echo 💡 使用方法:
echo 1. 将 release\XComBot 文件夹分发给用户
echo 2. 用户运行 install.bat 进行安装
echo 3. 或直接运行 XComBot.exe
echo.
pause
