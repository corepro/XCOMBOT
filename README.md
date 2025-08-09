# XComBot

一个使用 Playwright 自动化多个社交媒体平台（微博、知乎、小红书、今日头条、Twitter）进行点赞、转发、评论、收藏、关注等操作的桌面工具（含现代化 GUI）。

支持平台：
- 🐦 **微博** (weibo.com) - 点赞、转发、评论、收藏
- 🤔 **知乎** (zhihu.com) - 点赞、转发、评论、收藏、关注
- 📱 **小红书** (xiaohongshu.com) - 点赞、转发、评论、收藏、关注
- 📰 **今日头条** (toutiao.com) - 点赞、转发、评论、收藏、关注
- 🐦 **Twitter/X** (x.com) - 点赞、转发、评论

注意：仅用于学习与自动化演示，请遵守平台条款与法律法规，合理控制频率，勿用于垃圾信息。

## 核心功能

### 🔐 登录管理
- 支持所有平台的自动登录检测和Cookie保存
- 手动扫码/密码登录，自动保存登录状态
- 重启后自动恢复登录状态，无需重复登录

### 🎯 操作功能
- **点赞**: 自动为指定内容点赞
- **转发**: 自动转发内容（支持添加转发评论）
- **评论**: 智能评论生成（本地库/AI API）
- **收藏**: 自动收藏感兴趣的内容
- **关注**: 自动关注指定用户

### 🤖 智能特性
- **反爬虫系统**: 4级反爬虫模式（关闭/基础/增强/极限）
- **人类行为模拟**: 随机延时、鼠标轨迹、滚动行为
- **浏览器指纹伪装**: Canvas随机化、WebRTC防护、硬件信息伪装
- **代理支持**: 支持代理IP轮换（极限模式）

### 🎨 现代化界面
- 基于 ttkbootstrap 的现代化 GUI
- 实时日志显示和操作统计
- 直观的平台选择和操作配置
- 反爬虫模式可视化选择

## 环境要求
- Python 3.10+
- Windows/Mac/Linux 均可（本项目示例在 Windows 测试）

## 安装
1) 创建与激活虚拟环境（可选，推荐）

2) 安装依赖
```
pip install -r requirements.txt
playwright install
```

> 首次安装 Playwright 后需要安装浏览器内核：`playwright install`

## 快速开始

### 🖥️ GUI 模式（推荐）
启动现代化图形界面：
```bash
python app.py
```

### 📱 平台登录
首次使用需要登录各个平台：
```bash
# 微博登录
python app.py --login weibo

# 知乎登录
python app.py --login zhihu

# 小红书登录
python app.py --login xhs

# 今日头条登录
python app.py --login toutiao

# Twitter登录
python app.py --login twitter
```

### 🎯 精准模式（批量处理链接）
```bash
# 处理微博链接列表
python app.py --precise-mode weibo --links-file links.txt --like --retweet --comment

# 处理知乎链接列表
python app.py --precise-mode zhihu --links-file links.txt --like --collect --follow
```

## 配置说明

### 📁 配置文件
配置文件位于 `config/config.json`，主要配置项：

```json
{
  "headless": false,
  "slow_mo_ms": 100,
  "storage_state_path": "storage/storage_state.json",
  "anti_detection_enabled": true,
  "anti_detection_mode": "enhanced",
  "comment": {
    "mode": "local",
    "local_library_path": "data/comments.txt"
  }
}
```

### ⚙️ 主要配置项
- **headless**: 是否无头模式运行（建议 false 用于调试）
- **slow_mo_ms**: 操作延时毫秒（人类化操作）
- **storage_state_path**: Cookie 存储路径
- **anti_detection_enabled**: 是否启用反爬虫功能
- **anti_detection_mode**: 反爬虫模式（off/basic/enhanced/extreme）
- **comment.mode**: 评论模式（local 本地库 / ai AI生成）
- **comment.local_library_path**: 本地评论库文件路径

### 🛡️ 反爬虫模式说明
- **关闭**: 不使用反爬虫措施
- **基础**: 随机延时、用户代理轮换、基础行为模拟
- **增强**: 浏览器指纹伪装、Canvas随机化、WebRTC防护
- **极限**: 代理轮换、会话隔离、高级行为随机化

## 使用技巧

### 💡 最佳实践
1. **首次使用**: 建议先在GUI中完成各平台登录
2. **反爬虫设置**: 根据需要选择合适的反爬虫模式
3. **操作频率**: 合理控制操作间隔，避免被平台限制
4. **日志监控**: 实时查看日志了解运行状态

### 🔧 故障排除
- **登录失败**: 检查网络连接，尝试手动登录
- **操作失败**: 页面结构可能变化，等待更新
- **反爬虫检测**: 提升反爬虫模式等级
- **性能问题**: 降低操作频率，启用延时

### 📊 功能测试
```bash
# 测试反爬虫功能
python test_anti_detection.py --test-all

# 测试Cookie保存功能
python test_cookie_saving.py --test-all

# 测试知乎Cookie修复
python test_zhihu_cookie_fix.py
```

## ⚠️ 注意事项
- 各平台页面结构可能变化，选择器需要及时更新
- 操作需控制间隔与频率，建议启用反爬虫功能
- 登录方式推荐手动/扫码完成，程序负责保存状态
- 请遵守各平台的使用条款和相关法律法规

## 📄 免责声明
本项目仅用于学习和技术研究目的，不对因使用导致的任何风险负责。使用者需自行确保合规合法使用，并承担相应责任。

