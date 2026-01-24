# cc-launcher

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

**Claude Code 多平台启动器** - 专为Claude Code设计的智能启动管理工具，支持无缝切换多个AI平台，提供完整的会话管理和环境配置功能。

> **🎯 专用设计**: 从原gaccode.com项目分拆出来的独立启动器组件，专注于提供最佳的多平台启动和会话管理体验。

## ✨ 核心特性

### 🚀 智能多平台启动
- **统一入口** - 一个命令启动不同AI平台的Claude Code
- **平台检测** - 自动识别已配置的可用平台，智能选择最佳选项
- **环境配置** - 自动设置API密钥、端点和模型配置
- **别名支持** - 支持简短别名快速启动（gc、dp、sf等）

### 🔍 智能安装检测
- **多方式检测** - 支持 Native Installer、Homebrew、WinGet、npm 检测
- **优先级选择** - 自动优先选择 Native Installer（官方推荐）
- **安装类型识别** - 智能识别 Claude Code 的安装方式
- **更新建议** - 根据安装类型提供对应的更新指导

### 🆔 完整会话管理
- **会话创建** - 为每个平台创建专用会话ID，避免会话冲突
- **会话持久化** - 自动保存会话信息，支持会话恢复
- **会话映射** - 与cc-status共享会话信息，确保状态显示一致
- **智能清理** - 自动清理过期会话，管理存储空间

### 🔧 配置共享系统
- **统一配置** - 与cc-status共享`~/.claude/config/platforms.json`
- **独立配置** - 启动器专用配置`~/.claude/config/launcher.json`
- **自动初始化** - 首次运行时自动创建默认配置文件
- **配置验证** - 启动前自动验证配置完整性和有效性

### 🎨 用户体验优化
- **彩色输出** - 清晰的状态指示和错误信息显示
- **详细反馈** - 完整的启动过程信息和错误诊断
- **调试模式** - 支持详细日志输出，便于问题排查
- **Windows兼容** - 完全支持Windows操作系统

## 📦 安装与配置

### 前置要求
- Python 3.7+
- Claude Code CLI
- 至少一个支持平台的API密钥

### Claude Code CLI 安装（推荐方式）

**重要提示**：npm 安装方式已被官方标记为 deprecated，强烈推荐使用 Native Installer。

#### Windows 安装

**方式1：Native Installer（推荐，支持自动更新）**
```powershell
# PowerShell
irm https://claude.ai/install.ps1 | iex
```

```cmd
# CMD
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

**方式2：WinGet（需手动更新）**
```powershell
winget install Anthropic.ClaudeCode
```

#### macOS/Linux 安装

**方式1：Native Installer（推荐，支持自动更新）**
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**方式2：Homebrew（需手动更新）**
```bash
brew install --cask claude-code
```

#### 版本锁定选项

```bash
# 安装 stable 版本（约延迟一周，更稳定）
curl -fsSL https://claude.ai/install.sh | bash -s stable

# 安装指定版本
curl -fsSL https://claude.ai/install.sh | bash -s 1.0.58
```

#### npm 方式（已弃用，不推荐）

```bash
# 仅作为备选方案
npm install -g @anthropic-ai/claude-code
```

> **📌 注意**：Native Installer 会自动后台更新，无需手动干预。Homebrew 和 WinGet 安装需要定期手动更新。

### 快速安装

1. **克隆项目**
```bash
git clone https://github.com/DrayChou/cc-launcher.git
cd cc-launcher
```

2. **初始化配置**
```bash
python3 launcher.py --init-config
```

3. **Mac/Linux全局配置（推荐）**
```bash
# 一键设置全局命令
echo "" >> ~/.zshrc && echo "# Claude Code Tools" >> ~/.zshrc && echo "export PATH=\"\$PATH:\$PWD\"" >> ~/.zshrc && echo "alias ccl=\"\$PWD/launcher.py\"" >> ~/.zshrc && source ~/.zshrc

# 测试全局命令
ccl --check-config
```

### 配置API密钥
编辑 `~/.claude/config/platforms.json`，添加您的API密钥：
```json
{
  "platforms": {
    "gaccode": {
      "name": "GAC Code",
      "api_base_url": "https://relay05.gaccode.com/claudecode",
      "login_token": "your-gac-token-here",
      "model": "claude-3-5-sonnet-20241022",
      "enabled": true
    },
    "deepseek": {
      "name": "DeepSeek",
      "api_base_url": "https://api.deepseek.com/anthropic",
      "api_key": "sk-your-deepseek-key-here",
      "model": "deepseek-chat",
      "enabled": true
    },
    "kimi": {
      "name": "Kimi",
      "api_base_url": "https://api.moonshot.cn/anthropic",
      "auth_token": "your-kimi-token-here",
      "model": "moonshot-v1-8k",
      "enabled": true
    },
    "siliconflow": {
      "name": "SiliconFlow",
      "api_base_url": "https://api.siliconflow.cn/",
      "api_key": "sk-your-siliconflow-key-here",
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

### 启动器专用配置

编辑 `~/.claude/config/launcher.json` 自定义启动器行为：

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

### 配置选项说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `default_platform` | 默认启动平台 | `"gaccode"` |
| `claude_executable` | Claude可执行文件路径 | `"claude"` |
| `auto_create_session` | 自动创建会话 | `true` |
| `continue_last_session` | 继续上次会话 | `false` |
| `clear_existing` | 清理现有环境变量 | `true` |
| `timeout_seconds` | 环境设置超时时间 | `30` |

## 🚀 使用方法

### 基础使用

```bash
# 使用默认平台启动Claude Code
python3 launcher.py

# 使用指定平台启动
python3 launcher.py deepseek
python3 launcher.py kimi
python3 launcher.py siliconflow

# 使用别名启动（快速便捷）
python3 launcher.py dp    # DeepSeek
python3 launcher.py gc    # GAC Code
python3 launcher.py sf    # SiliconFlow
python3 launcher.py ds    # DeepSeek (另一个别名)

# 继续上次的会话
python3 launcher.py --continue
python3 launcher.py deepseek --continue

# 简短形式
python3 launcher.py -c
```

### 🌍 Mac/Linux全局配置（推荐）

配置全局命令，让你可以在任何地方启动Claude Code：

1. **自动配置（一键设置）**
   ```bash
   # 添加到shell配置
   echo "" >> ~/.zshrc
   echo "# Claude Code Tools" >> ~/.zshrc
   echo "export PATH=\"\$PATH:\$HOME/.claude\"" >> ~/.zshrc
   echo "alias ccl=\"~/.claude/ccl\"" >> ~/.zshrc

   # 重新加载配置
   source ~/.zshrc
   ```

2. **使用全局命令**
   ```bash
   # 在任何目录下使用
   ccl                    # 默认平台启动
   ccl deepseek          # DeepSeek平台
   ccl kimi              # Kimi平台
   ccl gc                # GAC Code
   ccl dp                # DeepSeek别名
   ccl --continue        # 继续上次会话
   ccl --list            # 查看所有平台
   ```

3. **平台别名速查**

   | 别名 | 平台 | 命令示例 |
   |------|------|----------|
   | `gc`, `ga` | GAC Code | `ccl gc` |
   | `dp`, `ds` | DeepSeek | `ccl dp` |
   | `km` | Kimi | `ccl km` |
   | `sc`, `sf` | SiliconFlow | `ccl sf` |
   | `glm` | GLM | `ccl glm` |
   | `kfc` | Kimi Coding | `ccl kfc` |

4. **手动配置选项**

   编辑 `~/.zshrc` 或 `~/.bashrc`，添加：
   ```bash
   # Claude Code Tools
   export PATH="$PATH:$HOME/.claude"
   alias ccl="$HOME/.claude/cc"
   alias claude-code="$HOME/.claude/cc"
   ```

### 管理命令

```bash
# 显示帮助信息
python3 launcher.py --help

# 列出所有可用平台及其配置状态
python3 launcher.py --list

# 检查配置完整性和Claude Code安装
python3 launcher.py --check-config

# 检查 Claude Code 更新（根据安装类型提供对应建议）
python3 launcher.py --check-updates

# 初始化配置文件（首次使用）
python3 launcher.py --init-config

# 调试模式（显示详细日志）
python3 launcher.py --debug deepseek

# 使用全局命令（如果已配置）
ccl --help
ccl --list
ccl --check-config
ccl --check-updates
```

### Claude Code 更新管理

cc-launcher 支持智能检测您的 Claude Code 安装类型，并提供对应的更新建议：

```bash
# 检查更新（自动识别安装类型）
python3 launcher.py --check-updates
```

**输出示例：**

```
Claude Code Update Check:
[OK] Current version: 2.1.19 (Claude Code)
[INFO] Installation type: native

Update options:
  [Auto] Native Installer 支持自动更新
  手动更新: claude update
  重新安装: curl -fsSL https://claude.ai/install.sh | bash
```

**不同安装类型的更新方式：**

| 安装类型 | 自动更新 | 手动更新命令 |
|----------|----------|--------------|
| **Native Installer** | ✅ 是 | `claude update` |
| **Homebrew** | ❌ 否 | `brew upgrade claude-code` |
| **WinGet** | ❌ 否 | `winget upgrade Anthropic.ClaudeCode` |
| **npm** | ❌ 否 | `npm update -g @anthropic-ai/claude-code` |

> **💡 提示**：如果您使用的是 npm 安装，建议迁移到 Native Installer 以获得自动更新支持。

## 🔄 启动流程详解

### 智能检测功能

cc-launcher 内置智能检测器，能够自动识别不同方式安装的 Claude Code：

**支持的安装类型检测：**

| 安装方式 | 检测特征 | 优先级 |
|----------|----------|--------|
| **Native Installer** | `~/.local/bin/claude` | ⭐ 最高 |
| **Homebrew** | `/usr/local/bin/claude`、`/opt/homebrew/bin/claude` | ⭐ 高 |
| **WinGet** | `%LOCALAPPDATA%\Microsoft\WindowsApps\` | ⭐ 高 |
| **npm (deprecated)** | `npx`、全局 npm 包 | ⭐ 低 |

**检测逻辑：**

1. **优先级1**：检查 Native Installer 路径
2. **优先级2**：检查包管理器路径（Homebrew/WinGet）
3. **优先级3**：检查 npm 相关命令（作为备选）

**验证检测结果：**

```bash
# 查看检测到的 Claude Code 命令
python3 launcher.py --check-config

# 输出示例：
# [OK] Claude Code detected: claude
```

### 启动流程

cc-launcher 采用智能化的启动流程，确保最佳用户体验：

1. **配置检测阶段**
   - 验证平台配置完整性
   - 检查API密钥有效性
   - 确认目标平台已启用

2. **环境准备阶段**
   - 清理现有的Claude相关环境变量
   - 设置目标平台的API配置
   - 配置模型参数和端点信息

3. **会话管理阶段**
   - 生成平台特定的会话ID
   - 创建会话映射供cc-status使用
   - 保存会话信息到缓存

4. **启动执行阶段**
   - 智能检测Claude Code安装位置
   - 构建启动命令参数
   - 启动Claude Code并传递会话信息

## 🔧 故障排除

### 常见问题解决

**Q: 找不到Claude Code？**
A: 解决步骤（按优先级）：

1. **推荐：使用 Native Installer**
   ```bash
   # Windows PowerShell
   irm https://claude.ai/install.ps1 | iex

   # Windows CMD
   curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd

   # macOS/Linux
   curl -fsSL https://claude.ai/install.sh | bash
   ```

2. **备选：使用包管理器**
   ```bash
   # Windows
   winget install Anthropic.ClaudeCode

   # macOS/Linux
   brew install --cask claude-code
   ```

3. **验证安装**
   ```bash
   # 检查版本
   claude --version

   # 测试启动
   claude --help
   ```

4. **检查检测状态**
   ```bash
   # 使用启动器的检测功能
   python3 launcher.py --check-config
   ```

> **⚠️ 注意**：npm 方式（`npm install -g @anthropic-ai/claude-code`）已被官方标记为 deprecated，建议迁移到 Native Installer。

**Q: 平台配置错误？**
A: 检查要点：
1. 验证 `~/.claude/config/platforms.json` JSON格式正确性
2. 确认API密钥格式符合平台要求
3. 检查网络连接和API服务可用性
4. 运行 `python launcher.py --check-config` 进行全面检查

**Q: 会话创建失败？**
A: 可能原因和解决方案：
1. 检查缓存目录权限：`~/.claude/cache/`
2. 确保有足够的磁盘空间
3. 查看详细日志：`~/.claude/logs/cc-launcher.log`
4. 尝试手动清理缓存：删除 `~/.claude/cache/session_*.json`

**Q: 与cc-status协同问题？**
A: 配置文件分工说明：
- `~/.claude/config/platforms.json` - 平台配置（两个项目共享）
- `~/.claude/config/status.json` - 状态栏配置（仅cc-status使用）
- `~/.claude/config/launcher.json` - 启动器配置（仅cc-launcher使用）

**Q: Mac全局命令不工作？**
A: 解决步骤：
1. 检查配置是否加载：`which ccl`
2. 验证PATH设置：`echo $PATH | grep claude`
3. 手动重新加载：`source ~/.zshrc`
4. 检查脚本权限：`ls -la ~/.claude/cc`
5. 验证Python版本：`python3 --version`

**Q: Linux/Mac权限问题？**
A: 权限设置：
```bash
# 设置执行权限
chmod +x ~/.claude/cc ~/.claude/claude-launcher

# 确保配置目录可写
chmod 755 ~/.claude
chmod 644 ~/.claude/config/*.json
```

**Q: Windows系统兼容性问题？**
A: Windows特别注意事项：
1. 确保Python已添加到PATH环境变量
2. 使用PowerShell或CMD运行启动器
3. 检查Windows Defender是否阻止脚本执行
4. 确认Git Bash路径配置正确（如需使用）

### 调试技巧

启用详细调试信息：
```bash
# 设置调试环境变量
export CC_LAUNCHER_DEBUG=1
python3 launcher.py deepseek

# 或使用内置调试模式
python3 launcher.py --debug --check-config

# 使用全局命令调试
export CC_LAUNCHER_DEBUG=1
ccl deepseek
```

### Mac/Linux特别提示

1. **Python版本要求**
   ```bash
   # 检查Python版本
   python3 --version

   # 安装Python3（Mac）
   brew install python3
   ```

2. **全局命令验证**
   ```bash
   # 完整诊断流程
   which ccl                    # 检查命令路径
   echo $PATH | grep claude      # 检查PATH设置
   ls -la ~/.claude/cc           # 检查文件权限
   python3 --version            # 检查Python版本
   ccl --check-config           # 测试配置
   ```

## 🗂️ 项目架构

```
cc-launcher/
├── launcher.py                     # 主入口文件，CLI接口
├── cc_launcher/                    # Python包
│   ├── __init__.py
│   ├── core/                       # 核心模块
│   │   ├── __init__.py
│   │   ├── config.py              # 配置管理器
│   │   ├── session.py             # 会话管理器
│   │   └── environment.py         # 环境配置管理
│   ├── detector/                   # 检测模块
│   │   ├── __init__.py
│   │   ├── claude.py              # Claude命令检测器
│   │   └── platform.py            # 平台检测器
│   ├── platforms/                  # 平台管理
│   │   ├── __init__.py
│   │   └── manager.py             # 平台管理器
│   └── utils/                      # 工具模块
│       ├── __init__.py
│       ├── logger.py              # 日志工具
│       ├── colors.py              # 颜色输出工具
│       └── file_lock.py           # 文件锁工具（Windows兼容）
├── tests/                          # 测试文件
├── docs/                           # 文档目录
└── README.md                       # 说明文档
```

## 🔒 安全特性

- **配置保护**: 敏感配置文件自动添加到 `.gitignore`
- **密钥掩码**: 日志输出中自动掩码API密钥
- **权限控制**: 配置目录设置为用户可读写
- **输入验证**: 所有配置项经过严格验证
- **环境隔离**: 每次启动前清理现有环境变量

## 🚀 性能优化

- **智能检测**: 按优先级检测 Claude Code 安装，优先选择 Native Installer
- **安装类型识别**: 自动识别安装方式（Native/Homebrew/WinGet/npm）
- **路径缓存**: 缓存 Claude Code 安装位置，避免重复检测
- **并发启动**: 优化启动流程，减少启动延迟
- **会话复用**: 支持会话恢复，避免重复创建
- **配置缓存**: 缓存配置文件，减少I/O操作

## 🤝 与 cc-status 协作机制

cc-launcher 与 cc-status 设计为完美配合的两个组件：

### 配置共享机制
- **平台配置**: `~/.claude/config/platforms.json` - 两个项目共享
- **专用配置**: 各自独立的配置文件，避免冲突
- **自动同步**: 配置变更后自动重新加载

### 会话协调机制
- **launcher职责**: 创建和管理平台特定会话ID
- **status职责**: 读取并显示会话相关信息
- **映射机制**: 通过session映射文件实现信息传递

### 目录结构统一
- **主目录**: 都使用 `~/.claude/` 作为根目录
- **子目录分工**: config/、cache/、logs/ 明确分工
- **权限一致**: 统一的文件权限管理

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🔗 相关项目

- **[cc-status](https://github.com/DrayChou/cc-status)** - Claude Code 多平台状态栏管理器
- **[gaccode.com](https://github.com/DrayChou/gaccode-statusline)** - 原始项目（已分拆）

---

> **💡 提示**: cc-launcher 专注于提供最佳的启动体验，配合使用 [cc-status](https://github.com/DrayChou/cc-status) 可获得完整的多平台Claude Code解决方案。