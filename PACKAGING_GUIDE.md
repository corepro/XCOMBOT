# Windows exe打包指南

## 🎯 打包目标

将XComBot Python项目打包成Windows可执行文件（.exe），方便在没有Python环境的Windows系统上运行。

## 📋 准备工作

### 系统要求
- Windows 10/11
- Python 3.8+ 已安装
- 至少4GB可用磁盘空间
- 稳定的网络连接

### 环境检查
```bash
# 检查Python版本
python --version

# 检查pip
pip --version

# 检查虚拟环境（如果使用）
venv_new\Scripts\activate
```

## 🚀 方法一：使用简易脚本（推荐新手）

### 步骤：
1. **双击运行 `build_simple.bat`**
2. **等待自动完成**（约5-15分钟）
3. **检查 `dist/` 目录**

### 输出文件：
```
dist/
├── XComBot.exe          # 主程序（约50-100MB）
├── install.bat          # 安装脚本
└── 使用说明.txt         # 使用说明
```

## 🔧 方法二：使用Python脚本（推荐高级用户）

### 步骤：
```bash
# 1. 运行打包脚本
python build_exe.py

# 2. 等待完成
# 脚本会自动：
# - 检查环境
# - 安装依赖
# - 创建配置文件
# - 构建exe
# - 创建附加文件
```

### 输出文件：
```
dist/
├── XComBot.exe          # 主程序
├── install.bat          # 安装脚本
├── README.txt           # 详细说明
├── config/              # 配置文件目录
└── data/                # 数据文件目录
```

## ⚙️ 方法三：手动使用PyInstaller

### 安装PyInstaller：
```bash
pip install pyinstaller
```

### 基础打包命令：
```bash
pyinstaller --onefile --windowed --name="XComBot" app.py
```

### 完整打包命令：
```bash
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
```

### 参数说明：
- `--onefile`: 打包成单个exe文件
- `--windowed`: 隐藏控制台窗口
- `--name`: 指定输出文件名
- `--add-data`: 添加数据文件
- `--hidden-import`: 添加隐藏导入
- `--exclude-module`: 排除不需要的模块

## 🎨 高级配置

### 创建spec文件：
```bash
# 生成spec文件
pyi-makespec --onefile --windowed app.py

# 编辑XComBot.spec文件
# 然后使用spec文件打包
pyinstaller XComBot.spec
```

### 添加图标：
```bash
pyinstaller --onefile --windowed --icon=icon.ico app.py
```

### 优化文件大小：
```bash
pyinstaller --onefile --windowed --strip --upx-dir=upx app.py
```

## 📦 打包优化

### 减小文件大小：

1. **排除不需要的模块**：
```python
# 在spec文件中添加
excludes=[
    'matplotlib',
    'numpy', 
    'pandas',
    'scipy',
    'PIL',
    'cv2',
    'tensorflow',
    'torch',
]
```

2. **使用UPX压缩**：
```bash
# 下载UPX: https://upx.github.io/
# 解压到项目目录
pyinstaller --onefile --upx-dir=upx app.py
```

3. **分析依赖**：
```bash
# 分析导入的模块
pyi-archive_viewer dist/XComBot.exe
```

### 提高启动速度：

1. **使用目录模式**：
```bash
# 不使用--onefile，生成目录
pyinstaller --windowed app.py
```

2. **预编译模块**：
```bash
# 在spec文件中设置
noarchive=False
```

## 🧪 测试打包结果

### 基本测试：
```bash
# 1. 进入dist目录
cd dist

# 2. 运行exe文件
XComBot.exe

# 3. 检查功能
# - GUI是否正常显示
# - 配置文件是否正确加载
# - 日志是否正常输出
```

### 兼容性测试：
- 在不同Windows版本上测试
- 在没有Python环境的机器上测试
- 测试所有主要功能

### 性能测试：
- 启动时间
- 内存占用
- CPU使用率

## 🚀 分发准备

### 创建安装包：

1. **使用NSIS**：
```nsis
; XComBot.nsi
!define APPNAME "XComBot"
!define VERSION "1.0.0"

OutFile "XComBot_Setup.exe"
InstallDir "$PROGRAMFILES\${APPNAME}"

Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    File "XComBot.exe"
    File /r "config"
    File /r "data"
    
    CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\XComBot.exe"
    CreateShortCut "$SMPROGRAMS\${APPNAME}.lnk" "$INSTDIR\XComBot.exe"
SectionEnd
```

2. **使用Inno Setup**：
```pascal
[Setup]
AppName=XComBot
AppVersion=1.0.0
DefaultDirName={pf}\XComBot
DefaultGroupName=XComBot
OutputBaseFilename=XComBot_Setup

[Files]
Source: "dist\XComBot.exe"; DestDir: "{app}"
Source: "dist\config\*"; DestDir: "{app}\config"; Flags: recursesubdirs
Source: "dist\data\*"; DestDir: "{app}\data"; Flags: recursesubdirs

[Icons]
Name: "{group}\XComBot"; Filename: "{app}\XComBot.exe"
Name: "{commondesktop}\XComBot"; Filename: "{app}\XComBot.exe"
```

### 数字签名：
```bash
# 使用signtool签名（需要代码签名证书）
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com XComBot.exe
```

## ⚠️ 常见问题

### 打包失败：

1. **模块导入错误**：
   - 检查hidden-import设置
   - 使用--collect-all参数

2. **文件路径错误**：
   - 检查--add-data路径
   - 使用绝对路径

3. **内存不足**：
   - 关闭其他程序
   - 增加虚拟内存

### 运行时错误：

1. **缺少DLL**：
   - 安装Visual C++ Redistributable
   - 复制缺少的DLL到exe目录

2. **权限问题**：
   - 以管理员身份运行
   - 检查杀毒软件设置

3. **路径问题**：
   - 使用相对路径
   - 检查工作目录设置

## 📊 文件大小对比

| 打包方式 | 文件大小 | 启动速度 | 兼容性 |
|---------|---------|---------|--------|
| --onefile | 50-100MB | 慢 | 高 |
| 目录模式 | 100-200MB | 快 | 高 |
| UPX压缩 | 30-60MB | 中等 | 中等 |

## 🎯 最佳实践

1. **开发阶段**：使用目录模式，便于调试
2. **测试阶段**：使用--onefile模式，便于分发
3. **发布阶段**：添加图标、签名、创建安装包
4. **维护阶段**：定期更新依赖，重新打包

## 📋 检查清单

打包前检查：
- [ ] 所有依赖已安装
- [ ] 配置文件已准备
- [ ] 测试脚本运行正常
- [ ] 清理临时文件

打包后检查：
- [ ] exe文件可以正常启动
- [ ] 所有功能正常工作
- [ ] 文件大小合理
- [ ] 在目标系统上测试

发布前检查：
- [ ] 添加使用说明
- [ ] 创建安装脚本
- [ ] 测试安装过程
- [ ] 准备技术支持文档
