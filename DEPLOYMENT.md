# 部署指南

## 📋 文件说明

### ✅ 可以上传的文件
- **源代码**: `src/` 目录下的所有 `.py` 文件
- **主程序**: `app.py`, `start_ui.py`
- **依赖文件**: `requirements.txt`
- **文档**: `README.md`, `DEPLOYMENT.md`
- **示例配置**: `config/config.example.json`
- **示例数据**: `data/comments.txt`
- **脚本**: `scripts/` 目录下的文件
- **Git配置**: `.gitignore`

### ❌ 不能上传的文件
- **虚拟环境**: `venv_new/` 目录
- **日志文件**: `logs/` 目录和所有 `.log` 文件
- **存储状态**: `storage/` 目录（包含登录信息）
- **配置文件**: `config/config.json`（可能包含API密钥）
- **测试文件**: 所有 `test_*.py` 文件
- **调试文件**: 所有 `debug_*.py` 文件
- **临时文件**: `traces/`, `*.tmp`, `*.backup` 等
- **系统文件**: `__pycache__/`, `.DS_Store` 等

## 🚀 部署步骤

### 1. 克隆仓库后的设置

```bash
# 1. 克隆仓库
git clone <your-repo-url>
cd XComBot

# 2. 创建虚拟环境
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt
playwright install

# 4. 创建配置文件
cp config/config.example.json config/config.json

# 5. 编辑配置文件
# 修改 config/config.json 中的设置，特别是 API 密钥

# 6. 创建必要目录
mkdir logs storage traces

# 7. 运行程序
python app.py
```

### 2. 配置说明

编辑 `config/config.json` 文件：

```json
{
  "headless": false,
  "slow_mo_ms": 100,
  "anti_detection_enabled": true,
  "anti_detection_mode": "enhanced",
  "comment": {
    "mode": "local",
    "hf_api_key": "YOUR_ACTUAL_API_KEY"
  }
}
```

### 3. 安全注意事项

⚠️ **重要**: 以下文件包含敏感信息，绝对不要上传到公开仓库：

- `config/config.json` - 包含API密钥
- `storage/storage_state.json` - 包含登录Cookie
- `logs/` - 可能包含敏感操作记录

## 🔒 隐私保护

1. **API密钥**: 使用环境变量或单独的配置文件
2. **登录状态**: 每次部署后需要重新登录
3. **日志文件**: 定期清理，不要上传到仓库
4. **测试文件**: 可能包含真实数据，建议不上传

## 📦 打包说明

如果需要打包成exe文件，请参考项目根目录的打包脚本。
