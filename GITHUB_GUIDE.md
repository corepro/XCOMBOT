# GitHub 仓库创建和上传指南

## 🌟 第一步：注册GitHub账号

1. 访问 [https://github.com](https://github.com)
2. 点击右上角"Sign up"
3. 填写用户名、邮箱、密码
4. 验证邮箱完成注册

## 📁 第二步：创建新仓库

### 在GitHub网站上创建：

1. **登录GitHub后，点击右上角"+"号**
2. **选择"New repository"**
3. **填写仓库信息**：
   - **Repository name**: `XComBot` 或 `social-media-automation`
   - **Description**: `Multi-platform social media automation tool - Supports Weibo, Zhihu, XHS, Toutiao, Twitter`
   - **Visibility**: 选择"Private"（推荐）或"Public"
   - **Initialize repository**:
     - ✅ Add a README file
     - ✅ Add .gitignore (选择Python)
     - ✅ Choose a license (推荐MIT License)

4. **点击"Create repository"**

## 💻 第三步：本地Git配置

### 安装Git（如果未安装）：

**Windows**:
```bash
# 下载并安装 Git for Windows
# https://git-scm.com/download/win
```

**配置Git用户信息**:
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## 📤 第四步：上传代码到GitHub

### 方法一：从现有项目上传

在项目根目录打开命令行：

```bash
# 1. 初始化Git仓库
git init

# 2. 添加远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/你的用户名/XComBot.git

# 3. 添加所有文件到暂存区
git add .

# 4. 查看将要提交的文件（确认没有敏感文件）
git status

# 5. 提交代码
git commit -m "Initial commit: Multi-platform social media automation tool"

# 6. 设置主分支名称（GitHub默认为main）
git branch -M main

# 7. 推送到远程仓库
git push -u origin main
```

### 方法二：克隆空仓库后添加文件

```bash
# 1. 克隆空仓库
git clone https://github.com/你的用户名/XComBot.git
cd XComBot

# 2. 复制项目文件到此目录（排除.gitignore中的文件）

# 3. 添加文件
git add .

# 4. 提交
git commit -m "Initial commit: Multi-platform social media automation tool"

# 5. 推送
git push origin main
```

## 🔐 第五步：设置SSH密钥（推荐）

### 生成SSH密钥：

```bash
# 生成SSH密钥
ssh-keygen -t ed25519 -C "your.email@example.com"

# 启动ssh-agent
eval "$(ssh-agent -s)"

# 添加SSH密钥到ssh-agent
ssh-add ~/.ssh/id_ed25519

# 查看公钥
cat ~/.ssh/id_ed25519.pub
# Windows: type %USERPROFILE%\.ssh\id_ed25519.pub
```

### 在GitHub中添加SSH密钥：

1. 复制公钥内容
2. 登录GitHub，进入"Settings" → "SSH and GPG keys"
3. 点击"New SSH key"
4. 粘贴公钥内容，添加标题
5. 点击"Add SSH key"

### 使用SSH地址：

```bash
# 更改远程仓库地址为SSH
git remote set-url origin git@github.com:你的用户名/XComBot.git
```

## 📋 第六步：GitHub特色功能

### 创建Release（发布版本）：

1. 进入仓库页面
2. 点击"Releases" → "Create a new release"
3. 填写版本号（如v1.0.0）和发布说明
4. 可以上传打包好的exe文件

### 设置GitHub Actions（CI/CD）：

创建 `.github/workflows/python-app.yml`：

```yaml
name: Python application

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python 3.9
      uses: actions/setup-python@v3
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install flake8 pytest
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
    - name: Lint with flake8
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
    - name: Test with pytest
      run: |
        pytest
```

### 创建Issues模板：

创建 `.github/ISSUE_TEMPLATE/bug_report.md`：

```markdown
---
name: Bug report
about: Create a report to help us improve
title: ''
labels: bug
assignees: ''
---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
 - OS: [e.g. Windows 10]
 - Python Version: [e.g. 3.9]
 - Browser: [e.g. Chrome]

**Additional context**
Add any other context about the problem here.
```

## 🔒 第七步：仓库安全设置

### 设置仓库为私有：
1. 进入仓库页面
2. 点击"Settings"
3. 滚动到"Danger Zone"
4. 点击"Change repository visibility"

### 添加协作者：
1. 进入"Settings" → "Manage access"
2. 点击"Invite a collaborator"
3. 输入用户名或邮箱

### 设置分支保护：
1. 进入"Settings" → "Branches"
2. 点击"Add rule"
3. 设置分支保护规则

### 设置Secrets（用于CI/CD）：
1. 进入"Settings" → "Secrets and variables" → "Actions"
2. 添加敏感信息（如API密钥）

## 📊 第八步：项目管理

### 使用GitHub Projects：
1. 进入仓库页面
2. 点击"Projects" → "New project"
3. 创建看板管理任务

### 使用GitHub Wiki：
1. 进入仓库页面
2. 点击"Wiki"
3. 创建项目文档

### 设置GitHub Pages（如果需要）：
1. 进入"Settings" → "Pages"
2. 选择源分支
3. 设置自定义域名（可选）

## ⚠️ 重要注意事项

### 🚫 绝对不要上传的文件：
- API密钥和密码
- 用户登录信息
- 个人隐私数据
- 大型二进制文件（>100MB）

### ✅ 最佳实践：
- 使用有意义的提交信息
- 定期创建分支进行功能开发
- 编写详细的README文档
- 添加适当的许可证
- 使用GitHub Issues跟踪问题

### 🔍 提交前检查：

```bash
# 检查文件大小
find . -size +50M -type f

# 检查敏感信息
grep -r "password\|api_key\|secret" . --exclude-dir=.git

# 查看将要提交的文件
git status
git diff --cached
```

## 🌐 第九步：开源项目优化

### 创建贡献指南 `CONTRIBUTING.md`：

```markdown
# Contributing to XComBot

## How to contribute

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Code style

- Follow PEP 8
- Add docstrings to functions
- Use meaningful variable names

## Reporting bugs

Please use GitHub Issues to report bugs.
```

### 创建行为准则 `CODE_OF_CONDUCT.md`：

```markdown
# Code of Conduct

## Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone.

## Our Standards

- Be respectful and inclusive
- Accept constructive criticism
- Focus on what is best for the community

## Enforcement

Instances of abusive behavior may be reported to the project maintainers.
```

## 🎯 完成！

现在您的代码已经成功上传到GitHub了！

**推荐下一步**：
- 设置自动化测试
- 创建详细的文档
- 定期发布新版本
- 与社区互动
