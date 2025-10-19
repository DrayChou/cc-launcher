# cc-launcher

Claude Code 多平台启动器 - 统一管理不同AI平台的Claude Code启动

## ✨ 特性

- 🚀 **多平台支持** - GAC Code、DeepSeek、Kimi、SiliconFlow等
- 🔧 **智能环境配置** - 自动设置API密钥和端点
- 🆔 **会话管理** - 创建和管理平台特定的会话ID
- 🎯 **平台检测** - 智能检测已配置的可用平台
- 📁 **共享配置** - 与 cc-status 共享平台配置
- 🎨 **友好界面** - 彩色输出和详细状态信息

## 📦 安装

```bash
cd scripts/cc-launcher
pip install -e .
```

## ⚙️ 配置

配置文件位置：`~/.claude/config/platforms.json`

```json
{
  "platforms": {
    "gaccode": {
      "name": "GAC Code",
      "api_base_url": "https://relay05.gaccode.com/claudecode",
      "login_token": "your-token-here",
      "model": "claude-3-5-sonnet-20241022",
      "enabled": true
    },
    "deepseek": {
      "name": "DeepSeek",
      "api_base_url": "https://api.deepseek.com/anthropic",
      "api_key": "sk-your-key-here",
      "model": "deepseek-chat",
      "enabled": true
    },
    "kimi": {
      "name": "Kimi",
      "api_base_url": "https://api.moonshot.cn/anthropic",
      "auth_token": "your-token-here",
      "model": "moonshot-v1-8k",
      "enabled": true
    },
    "siliconflow": {
      "name": "SiliconFlow",
      "api_base_url": "https://api.siliconflow.cn/",
      "api_key": "sk-your-key-here",
      "model": "deepseek-ai/DeepSeek-V3",
      "enabled": true
    }
  },
  "default_platform": "gaccode",
  "aliases": {
    "gc": "gaccode",
    "dp": "deepseek",
    "ds": "deepseek",
    "sc": "siliconflow",
    "sf": "siliconflow",
    "kimi": "kimi"
  }
}
```

启动器特定配置：`~/.claude/config/launcher.json`

```json
{
  "default_platform": "gaccode",
  "claude_executable": "claude",
  "git_bash_path": "",
  "auto_create_session": true,
  "continue_last_session": false,
  "environment": {
    "clear_existing": true,
    "timeout_seconds": 30
  }
}
```

## 🚀 使用

### 基础使用

```bash
# 使用默认平台启动
python launcher.py

# 使用指定平台启动
python launcher.py deepseek
python launcher.py kimi

# 使用别名启动
python launcher.py dp    # DeepSeek
python launcher.py gc    # GAC Code
python launcher.py sf    # SiliconFlow

# 继续上次的会话
python launcher.py --continue
python launcher.py deepseek --continue

# 简短形式
python launcher.py -c
```

### 高级用法

```bash
# 显示帮助信息
python launcher.py --help

# 列出所有可用平台
python launcher.py --list

# 检查配置
python launcher.py --check-config

# 调试模式
python launcher.py --debug deepseek
```

## 📋 启动流程

1. **配置检测** - 检查平台配置是否完整
2. **环境设置** - 清理现有环境变量，设置新的配置
3. **会话创建** - 生成平台特定的会话ID
4. **会话映射** - 创建session映射供statusline使用
5. **Claude启动** - 智能检测并启动Claude Code

## 🔧 故障排除

### 找不到Claude Code？
1. 确保已安装Claude Code CLI
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```
2. 检查PATH环境变量
3. 使用完整路径指定可执行文件

### 平台配置错误？
1. 检查 `~/.claude/config/platforms.json` 语法
2. 验证API密钥格式
3. 确认网络连接正常

### 会话创建失败？
1. 检查缓存目录权限：`~/.claude/cache/`
2. 确保有足够的磁盘空间
3. 查看日志文件：`~/.claude/logs/cc-launcher.log`

### 与 cc-status 配置冲突？
两个项目共享以下配置文件：
- `~/.claude/config/platforms.json` - 平台配置（共享）
- `~/.claude/config/status.json` - 状态栏配置（仅cc-status使用）
- `~/.claude/config/launcher.json` - 启动器配置（仅cc-launcher使用）

## 🗂️ 项目结构

```
cc-launcher/
├── launcher.py                 # 主入口文件
├── cc_launcher/                # Python包
│   ├── __init__.py
│   ├── core/                   # 核心模块
│   │   ├── __init__.py
│   │   ├── config.py          # 配置管理
│   │   ├── session.py         # 会话管理
│   │   └── environment.py     # 环境配置
│   ├── detector/               # 检测模块
│   │   ├── __init__.py
│   │   ├── claude.py          # Claude命令检测
│   │   └── platform.py        # 平台检测
│   ├── platforms/              # 平台管理
│   │   ├── __init__.py
│   │   └── manager.py         # 平台管理器
│   └── utils/                  # 工具模块
│       ├── __init__.py
│       ├── logger.py          # 日志工具
│       ├── colors.py          # 颜色工具
│       └── session_mapper.py  # 会话映射工具
├── setup.py                    # 安装脚本
└── README.md                   # 说明文档
```

## 🔗 与 cc-status 协作

1. **共享平台配置** - 两个项目读取相同的 `platforms.json`
2. **会话映射** - launcher创建session，statusline读取显示
3. **统一目录结构** - 都使用 `~/.claude/` 作为主目录
4. **独立功能** - launcher负责启动，statusline负责显示

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License