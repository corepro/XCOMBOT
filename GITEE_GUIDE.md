# Gitee 仓库创建和上传指南

## 🌟 第一步：注册Gitee账号

1. 访问 [https://gitee.com](https://gitee.com)
2. 点击右上角"注册"
3. 填写用户名、邮箱、密码
4. 验证邮箱完成注册

## 📁 第二步：创建新仓库

### 在Gitee网站上创建：

1. **登录Gitee后，点击右上角"+"号**
2. **选择"新建仓库"**
3. **填写仓库信息**：
   - **仓库名称**: `XComBot` 或 `social-media-automation`
   - **仓库介绍**: `多平台社交媒体自动化工具 - 支持微博、知乎、小红书、今日头条、Twitter`
   - **是否开源**: 选择"私有"（推荐）或"公开"
   - **编程语言**: Python
   - **添加.gitignore**: 选择Python
   - **添加开源许可证**: 可选择MIT License
   - **添加README**: 勾选

4. **点击"创建"**

## 💻 第三步：本地Git配置

### 安装Git（如果未安装）：

**Windows**:
```bash
# 下载并安装 Git for Windows
# https://git-scm.com/download/win
```

**配置Git用户信息**:
```bash
git config --global user.name "你的用户名"
git config --global user.email "你的邮箱@example.com"
```

## 📤 第四步：上传代码到Gitee

### 方法一：从现有项目上传

在项目根目录打开命令行：

```bash
# 1. 初始化Git仓库
git init

# 2. 添加远程仓库（替换为你的仓库地址）
git remote add origin https://gitee.com/你的用户名/XComBot.git

# 3. 添加所有文件到暂存区
git add .

# 4. 查看将要提交的文件（确认没有敏感文件）
git status

# 5. 提交代码
git commit -m "初始提交：多平台社交媒体自动化工具"

# 6. 推送到远程仓库
git push -u origin master
```

### 方法二：克隆空仓库后添加文件

```bash
# 1. 克隆空仓库
git clone https://gitee.com/你的用户名/XComBot.git
cd XComBot

# 2. 复制项目文件到此目录（排除.gitignore中的文件）

# 3. 添加文件
git add .

# 4. 提交
git commit -m "初始提交：多平台社交媒体自动化工具"

# 5. 推送
git push origin master
```

## 🔐 第五步：设置SSH密钥（推荐）

### 生成SSH密钥：

```bash
# 生成SSH密钥
ssh-keygen -t rsa -C "你的邮箱@example.com"

# 查看公钥
cat ~/.ssh/id_rsa.pub
# Windows: type %USERPROFILE%\.ssh\id_rsa.pub
```

### 在Gitee中添加SSH密钥：

1. 复制公钥内容
2. 登录Gitee，进入"设置" → "SSH公钥"
3. 点击"添加公钥"
4. 粘贴公钥内容，添加标题
5. 点击"确定"

### 使用SSH地址：

```bash
# 更改远程仓库地址为SSH
git remote set-url origin git@gitee.com:你的用户名/XComBot.git
```

## 📋 第六步：仓库管理

### 常用Git命令：

```bash
# 查看状态
git status

# 添加文件
git add 文件名
git add .  # 添加所有文件

# 提交更改
git commit -m "提交说明"

# 推送到远程
git push

# 拉取远程更新
git pull

# 查看提交历史
git log --oneline

# 创建分支
git checkout -b 新分支名

# 切换分支
git checkout 分支名

# 合并分支
git merge 分支名
```

### 更新代码：

```bash
# 1. 添加修改的文件
git add .

# 2. 提交更改
git commit -m "更新：添加新功能"

# 3. 推送到远程
git push
```

## ⚠️ 重要注意事项

### 🚫 绝对不要上传的文件：
- `config/config.json` - 包含API密钥
- `storage/` 目录 - 包含登录Cookie
- `logs/` 目录 - 包含操作日志
- `venv_new/` 目录 - 虚拟环境
- 任何包含真实账号信息的文件

### ✅ 安全检查清单：
- [ ] 检查.gitignore文件是否正确
- [ ] 确认config.json未被添加
- [ ] 确认storage目录未被添加
- [ ] 确认logs目录未被添加
- [ ] 检查是否有硬编码的密钥或密码

### 🔍 提交前检查：

```bash
# 查看将要提交的文件
git status

# 查看文件内容差异
git diff

# 查看暂存区的文件
git diff --cached
```

## 🌐 第七步：仓库设置

### 设置仓库为私有（推荐）：
1. 进入仓库页面
2. 点击"设置"
3. 在"基本信息"中设置"仓库公开性"为"私有"

### 添加协作者：
1. 进入仓库页面
2. 点击"管理" → "仓库成员管理"
3. 添加协作者邮箱或用户名

### 设置分支保护：
1. 进入"管理" → "分支管理"
2. 设置主分支保护规则

## 🎯 完成！

现在您的代码已经安全地上传到Gitee了！

**下一步**：
- 定期提交代码更新
- 使用分支进行功能开发
- 编写详细的提交说明
- 保持仓库整洁
