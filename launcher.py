#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cc-launcher - Claude Code Multi-Platform Launcher
Claude Code 多平台启动器主入口

功能：
- 多平台Claude Code启动
- 智能环境变量配置
- 会话ID生成和管理
- 平台检测和验证
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

# 添加项目路径到 Python 路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from cc_launcher.core.config import ConfigManager
    from cc_launcher.core.session import SessionManager
    from cc_launcher.core.environment import EnvironmentManager
    from cc_launcher.detector.claude import ClaudeDetector
    from cc_launcher.detector.platform import PlatformDetector
    from cc_launcher.utils.colors import Colors, ColorPrinter
    from cc_launcher.utils.logger import get_logger
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure all dependencies are installed.")
    sys.exit(1)


def print_header():
    """打印启动器头部信息"""
    printer = ColorPrinter()
    printer.print("Claude Code Multi-Platform Launcher v1.0", Colors.MAGENTA, bold=True)
    printer.print("=" * 50, Colors.GRAY)

    # 显示 launcher.py 的实际安装路径（仅在非标准位置时显示）
    launcher_path = Path(__file__).parent
    standard_path = Path.home() / ".claude" / "scripts" / "cc-launcher"

    if launcher_path != standard_path:
        printer.print(f"Launcher location: {launcher_path}", Colors.GRAY)

    print()


def list_available_platforms(config_manager: ConfigManager):
    """列出所有可用平台"""
    printer = ColorPrinter()
    platforms_config = config_manager.get_platforms_config()

    printer.print("Available platforms:", Colors.CYAN, bold=True)

    for platform_id, platform_config in platforms_config.get("platforms", {}).items():
        if platform_config.get("enabled", False):
            # 检查是否有有效的认证信息
            has_auth = any([
                platform_config.get("api_key"),
                platform_config.get("auth_token"),
                platform_config.get("login_token")
            ])

            status = "[OK]" if has_auth else "[FAIL]"
            status_color = Colors.GREEN if has_auth else Colors.RED

            printer.print(f"  {status} {platform_id:<12} - {platform_config.get('name', 'Unknown')}",
                         status_color)

            if has_auth:
                printer.print(f"    Model: {platform_config.get('model', 'N/A')}", Colors.GRAY)

    print()


def check_config(config_manager: ConfigManager):
    """检查配置状态"""
    printer = ColorPrinter()

    printer.print("Configuration Check:", Colors.CYAN, bold=True)

    # 检查平台配置
    platforms_config = config_manager.get_platforms_config()
    enabled_platforms = []

    for platform_id, platform_config in platforms_config.get("platforms", {}).items():
        if platform_config.get("enabled", False):
            has_auth = any([
                platform_config.get("api_key"),
                platform_config.get("auth_token"),
                platform_config.get("login_token")
            ])
            if has_auth:
                enabled_platforms.append(platform_id)

    if enabled_platforms:
        printer.print(f"[OK] Found {len(enabled_platforms)} configured platform(s)", Colors.GREEN)
        for platform in enabled_platforms:
            printer.print(f"  - {platform}", Colors.GRAY)
    else:
        printer.print("[FAIL] No configured platforms found", Colors.RED)
        printer.print("  Please configure API keys in ~/.claude/config/platforms.json", Colors.YELLOW)

    # 检查Claude安装
    claude_detector = ClaudeDetector()
    claude_cmd = claude_detector.detect_claude_command()

    if claude_cmd:
        printer.print(f"[OK] Claude Code detected: {' '.join(claude_cmd)}", Colors.GREEN)
    else:
        printer.print("[FAIL] Claude Code not found", Colors.RED)
        printer.print("  Please install Claude Code:", Colors.YELLOW)
        if os.name == 'nt':
            printer.print("    PowerShell: irm https://claude.ai/install.ps1 | iex", Colors.GRAY)
            printer.print("    WinGet: winget install Anthropic.ClaudeCode", Colors.GRAY)
        else:
            printer.print("    Native: curl -fsSL https://claude.ai/install.sh | bash", Colors.GRAY)
            printer.print("    Homebrew: brew install --cask claude-code", Colors.GRAY)

    print()


def check_claude_updates(claude_detector: ClaudeDetector, printer: ColorPrinter):
    """检查Claude Code更新"""
    import subprocess
    import os

    printer.print("Claude Code Update Check:", Colors.CYAN, bold=True)

    # 检测当前安装的Claude Code
    claude_cmd = claude_detector.detect_claude_command()
    if not claude_cmd:
        printer.print("[FAIL] Claude Code not found", Colors.RED)
        suggestions = claude_detector.suggest_installation_methods()
        printer.print("Installation suggestions:", Colors.YELLOW)
        for suggestion in suggestions:
            printer.print(f"  {suggestion}", Colors.GRAY)
        return

    # 获取当前版本
    current_version = claude_detector.get_claude_version(claude_cmd)
    if current_version:
        printer.print(f"[OK] Current version: {current_version}", Colors.GREEN)
    else:
        printer.print("[WARN] Could not determine current version", Colors.YELLOW)

    # 检测安装类型
    install_type = claude_detector.detect_installation_type(claude_cmd)
    printer.print(f"[INFO] Installation type: {install_type}", Colors.CYAN)

    # 根据安装类型提供更新建议
    printer.print("\nUpdate options:", Colors.CYAN)

    if install_type == "native":
        printer.print("  [Auto] Native Installer 支持自动更新", Colors.GREEN)
        printer.print("  手动更新: claude update", Colors.GRAY)
        printer.print("  重新安装: curl -fsSL https://claude.ai/install.sh | bash", Colors.GRAY)

    elif install_type == "homebrew":
        printer.print("  [Manual] Homebrew 需要手动更新", Colors.YELLOW)
        printer.print("  更新命令: brew upgrade claude-code", Colors.GREEN)

    elif install_type == "winget":
        printer.print("  [Manual] WinGet 需要手动更新", Colors.YELLOW)
        printer.print("  更新命令: winget upgrade Anthropic.ClaudeCode", Colors.GREEN)

    elif install_type == "npm":
        printer.print("  [Deprecated] npm 方式已弃用", Colors.YELLOW)
        printer.print("  建议迁移到 Native Installer", Colors.YELLOW)
        try:
            # 尝试检查 npm 更新
            result = subprocess.run(
                ["npm", "outdated", "-g", "@anthropic-ai/claude-code"],
                capture_output=True,
                text=True,
                timeout=15
            )
            if result.returncode == 0 and result.stdout.strip():
                printer.print("  npm 更新: npm update -g @anthropic-ai/claude-code", Colors.GRAY)
            else:
                printer.print("  [OK] npm 版本已是最新", Colors.GREEN)
        except Exception as e:
            printer.print(f"  [WARN] 无法检查 npm 更新: {e}", Colors.YELLOW)

    else:
        printer.print("  [Unknown] 未知的安装类型", Colors.YELLOW)
        printer.print(f"  当前命令: {' '.join(claude_cmd)}", Colors.GRAY)

    # 迁移建议
    if install_type == "npm":
        printer.print("\n[建议] 迁移到 Native Installer:", Colors.MAGENTA)
        if os.name == 'nt':
            printer.print("  PowerShell: irm https://claude.ai/install.ps1 | iex", Colors.GRAY)
        else:
            printer.print("  curl -fsSL https://claude.ai/install.sh | bash", Colors.GRAY)

    print()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Claude Code Multi-Platform Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Launch with default platform
  %(prog)s deepseek           # Launch with DeepSeek platform
  %(prog)s dp                 # Launch with DeepSeek (alias)
  %(prog)s --continue         # Continue last session
  %(prog)s --list             # List available platforms
  %(prog)s --check-config     # Check configuration
  %(prog)s glm --set-default  # Launch GLM and update base settings.json
        """
    )

    parser.add_argument(
        "platform",
        nargs="?",
        help="Platform name or alias (gc, dp, kimi, sf)"
    )
    parser.add_argument(
        "-c", "--continue",
        dest="continue_session",
        action="store_true",
        help="Continue existing session"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available platforms"
    )
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Check configuration status"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--init-config",
        action="store_true",
        help="Initialize configuration files"
    )
    parser.add_argument(
        "--check-updates",
        action="store_true",
        help="Check for Claude Code updates"
    )
    parser.add_argument(
        "--set-default",
        dest="set_default_env",
        action="store_true",
        help="Also update base settings.json env config to this platform"
    )

    args = parser.parse_args()

    # 初始化组件
    config_manager = ConfigManager()
    session_manager = SessionManager(config_manager)
    environment_manager = EnvironmentManager(config_manager)
    platform_detector = PlatformDetector(config_manager)
    claude_detector = ClaudeDetector()
    printer = ColorPrinter()

    # 设置日志级别
    if args.debug:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)

    logger = get_logger("launcher")

    try:
        # 处理特殊命令
        if args.init_config:
            print_header()
            try:
                # 触发配置文件创建（通过读取配置）
                config_manager.get_platforms_config()
                config_manager.get_status_config()
                config_manager.get_launcher_config()
                printer.print("Configuration files initialized successfully", Colors.GREEN)
                printer.print(f"Configuration location: {config_manager.config_dir}", Colors.CYAN)
            except Exception as e:
                printer.print(f"Failed to initialize configuration: {e}", Colors.RED)
                return 1
            return 0

        if args.list:
            print_header()
            list_available_platforms(config_manager)
            return 0

        if args.check_config:
            print_header()
            check_config(config_manager)
            return 0

        if args.check_updates:
            print_header()
            check_claude_updates(claude_detector, printer)
            return 0

        # 正常启动流程
        print_header()

        # 检测可用平台
        platform_info = platform_detector.detect_platform(args.platform)
        if not platform_info:
            printer.print("No suitable platform found or configured", Colors.RED)
            printer.print("Use --list to see available platforms", Colors.YELLOW)
            printer.print("Use --check-config to check configuration", Colors.YELLOW)
            return 1

        platform_name, platform_config = platform_info
        printer.print(f"Selected platform: {platform_config.get('name', platform_name)} ({platform_name})",
                     Colors.GREEN, bold=True)

        # 设置环境变量
        printer.print("Configuring environment...", Colors.CYAN)
        env_vars = environment_manager.setup_environment(platform_config)

        if not env_vars:
            printer.print("Failed to configure environment", Colors.RED)
            return 1

        # 如果指定了 --set-default，则同时更新基础 settings.json 的 env 配置
        if args.set_default_env:
            _update_base_settings_env(platform_name, platform_config, printer)

        # 创建或获取会话
        printer.print("Managing session...", Colors.CYAN)
        session_info = session_manager.create_or_get_session(
            platform_name,
            continue_session=args.continue_session
        )

        if not session_info:
            printer.print("Failed to create session", Colors.RED)
            return 1

        # 显示会话信息
        printer.print(f"Session ID: {session_info['session_id']}", Colors.GREEN)
        printer.print(f"Platform: {platform_name}", Colors.GREEN)
        if args.continue_session:
            printer.print("Mode: Continue existing session", Colors.YELLOW)
        else:
            printer.print("Mode: New session", Colors.CYAN)

        # 检测Claude命令
        claude_cmd = claude_detector.detect_claude_command()
        if not claude_cmd:
            printer.print("Claude Code not found. Please install:", Colors.RED)
            if os.name == 'nt':
                printer.print("  PowerShell: irm https://claude.ai/install.ps1 | iex", Colors.YELLOW)
                printer.print("  WinGet: winget install Anthropic.ClaudeCode", Colors.GRAY)
                printer.print("  CMD: curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd", Colors.GRAY)
            else:
                printer.print("  Native: curl -fsSL https://claude.ai/install.sh | bash", Colors.YELLOW)
                printer.print("  Homebrew: brew install --cask claude-code", Colors.GRAY)
            return 1

        # 准备启动命令
        launch_cmd = claude_cmd.copy()
        if args.continue_session:
            launch_cmd.append("--continue")
        else:
            launch_cmd.append(f"--session-id={session_info['session_id']}")

        # 启动Claude Code
        printer.print("Launching Claude Code...", Colors.MAGENTA, bold=True)
        printer.print(f"Command: {' '.join(launch_cmd)}", Colors.GRAY)
        print("=" * 50)

        # 启动Claude Code进程
        import os
        import subprocess
        import shutil
        import json

        # 使用配置好的环境变量
        launch_env = os.environ.copy()
        launch_env.update(env_vars)

        # 获取命令的完整路径（重要：避免PATH问题）
        cmd_path = shutil.which(launch_cmd[0])
        if cmd_path:
            launch_cmd[0] = cmd_path
            printer.print(f"Using full path: {cmd_path}", Colors.GREEN)

        # 创建平台专用的settings配置文件
        platform_settings_path = None
        try:
            platform_settings_path = _create_platform_settings_file(platform_name, platform_config, printer)
            if platform_settings_path:
                # 在启动命令中添加 --settings 参数
                launch_cmd.append(f"--settings={platform_settings_path}")
                printer.print(f"Using platform settings: {platform_settings_path}", Colors.CYAN)
        except Exception as e:
            printer.print(f"Warning: Failed to create platform settings file: {e}", Colors.YELLOW)

        try:
            process = subprocess.run(
                launch_cmd,
                env=launch_env,
                check=False,
                shell=(os.name == "nt")  # Windows需要shell=True
            )
            return process.returncode
        except KeyboardInterrupt:
            printer.print("\nInterrupted by user", Colors.YELLOW)
            return 130
        except FileNotFoundError:
            printer.print(f"Command not found: {launch_cmd[0]}", Colors.RED)
            return 1

    except KeyboardInterrupt:
        printer.print("\nInterrupted by user", Colors.YELLOW)
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        printer.print(f"Unexpected error: {e}", Colors.RED)
        return 1


def _create_platform_settings_file(platform_name: str, platform_config: dict, printer) -> Optional[Path]:
    """为指定平台创建专用的settings配置文件

    从当前工作目录的settings.json复制并修改env配置，
    生成settings.{platform}.json文件，避免污染全局配置

    Args:
        platform_name: 平台名称（如 "glm", "gaccode"）
        platform_config: 平台配置
        printer: 颜色打印机

    Returns:
        平台专用配置文件的绝对路径，如果失败则返回None
    """
    import json

    # 当前工作目录的settings.json
    cwd_settings_path = Path.cwd() / "settings.json"

    # 如果当前目录没有settings.json，尝试使用全局配置
    if not cwd_settings_path.exists():
        cwd_settings_path = Path.home() / ".claude" / "settings.json"

    if not cwd_settings_path.exists():
        printer.print(f"Warning: settings.json not found in {Path.cwd()} or {Path.home() / '.claude'}", Colors.YELLOW)
        return None

    try:
        # 生成平台专用配置文件名 - 与settings.json放在同一目录
        platform_settings_path = cwd_settings_path.parent / f"settings.{platform_name}.json"

        # 读取原始settings.json
        with open(cwd_settings_path, "r", encoding="utf-8") as f:
            settings_data = json.load(f)

        printer.print(f"Loaded settings from: {cwd_settings_path}", Colors.CYAN)

        # 创建新的环境变量配置
        env_config = _create_settings_env_config(platform_config)
        settings_data["env"] = env_config

        # 获取当前 Python 解释器的绝对路径（只计算一次）
        python_executable = Path(sys.executable).absolute().as_posix()
        printer.print(f"Using Python interpreter: {python_executable}", Colors.CYAN)

        # 配置 hooks 和 statusLine
        claude_dir = Path.home() / ".claude"

        # 配置 notify hook
        _configure_notify_hook(settings_data, claude_dir, python_executable, platform_name, printer)

        # 配置 statusLine
        _configure_status_line(settings_data, claude_dir, python_executable, platform_name, printer)

        # 写入平台专用配置文件
        with open(platform_settings_path, "w", encoding="utf-8") as f:
            json.dump(settings_data, f, indent=2, ensure_ascii=False)

        printer.print(f"Created platform settings: {platform_settings_path}", Colors.GREEN)
        return platform_settings_path.absolute()
    except Exception as e:
        printer.print(f"Warning: Failed to create platform settings file: {e}", Colors.RED)
        return None


def _configure_notify_hook(settings_data: dict, claude_dir: Path, python_executable: str, platform_name: str, printer):
    """配置 notify hook"""
    notify_dir = claude_dir / "scripts" / "notify"
    notify_script = notify_dir / "notify.py"

    # is_dir() 和 is_file() 已经隐含了存在性检查
    if notify_dir.is_dir() and notify_script.is_file():
        notify_script_path = notify_script.absolute().as_posix()
        notify_command = f"{python_executable} {notify_script_path} --platform={platform_name}"

        # 使用 setdefault 简化结构初始化
        settings_data.setdefault("hooks", {})
        settings_data["hooks"].setdefault("Stop", [{"hooks": []}])

        # 确保 Stop[0] 存在
        if not settings_data["hooks"]["Stop"]:
            settings_data["hooks"]["Stop"] = [{"hooks": []}]

        settings_data["hooks"]["Stop"][0].setdefault("hooks", [])

        # 设置或添加 notify hook
        hook_entry = {"type": "command", "command": notify_command}
        if settings_data["hooks"]["Stop"][0]["hooks"]:
            settings_data["hooks"]["Stop"][0]["hooks"][0] = hook_entry
        else:
            settings_data["hooks"]["Stop"][0]["hooks"].append(hook_entry)

        printer.print(f"Updated hooks.Stop with platform: {platform_name}", Colors.GREEN)
    else:
        _print_script_not_found_info(notify_dir, notify_script, "notify", "hooks", printer)


def _configure_status_line(settings_data: dict, claude_dir: Path, python_executable: str, platform_name: str, printer):
    """配置 statusLine"""
    statusline_dir = claude_dir / "scripts" / "cc-status"
    statusline_script = statusline_dir / "statusline.py"

    # is_dir() 和 is_file() 已经隐含了存在性检查
    if statusline_dir.is_dir() and statusline_script.is_file():
        statusline_script_path = statusline_script.absolute().as_posix()
        statusline_command = f"{python_executable} {statusline_script_path} --platform={platform_name}"

        # 使用 setdefault 简化初始化
        settings_data.setdefault("statusLine", {})
        settings_data["statusLine"]["type"] = "command"
        settings_data["statusLine"]["command"] = statusline_command
        settings_data["statusLine"].setdefault("padding", 1)

        printer.print(f"Updated statusLine with platform: {platform_name}", Colors.GREEN)
    else:
        _print_script_not_found_info(statusline_dir, statusline_script, "statusline", "statusLine", printer)


def _print_script_not_found_info(script_dir: Path, script_file: Path, script_name: str, config_name: str, printer):
    """打印脚本未找到的提示信息"""
    if not script_dir.is_dir():
        printer.print(f"Info: {script_name} directory not found at {script_dir}, skipping {config_name} configuration", Colors.GRAY)
    elif not script_file.is_file():
        printer.print(f"Info: {script_name}.py not found at {script_file}, skipping {config_name} configuration", Colors.GRAY)


def _create_settings_env_config(platform_config: dict) -> dict:
    """为settings.json创建环境变量配置

    Args:
        platform_config: 平台配置

    Returns:
        环境变量配置字典
    """
    env_config = {}

    # 设置认证信息
    if platform_config.get("api_key"):
        env_config.update({
            "ANTHROPIC_API_KEY": platform_config["api_key"],
            "ANTHROPIC_AUTH_TOKEN": ""
        })
    elif platform_config.get("auth_token"):
        env_config.update({
            "ANTHROPIC_AUTH_TOKEN": platform_config["auth_token"],
            "ANTHROPIC_API_KEY": ""
        })

    # 设置API基础URL
    if platform_config.get("api_base_url"):
        env_config["ANTHROPIC_BASE_URL"] = platform_config["api_base_url"]

    # 设置模型配置 - 重要！确保模型切换生效
    model = platform_config.get("model", "")
    if model:
        env_config["ANTHROPIC_MODEL"] = model
        env_config["ANTHROPIC_DEFAULT_HAIKU_MODEL"] = model
        env_config["ANTHROPIC_DEFAULT_SONNET_MODEL"] = model
        env_config["ANTHROPIC_DEFAULT_OPUS_MODEL"] = model
        env_config["ANTHROPIC_SMALL_FAST_MODEL"] = platform_config.get("small_model", model)

    return env_config


def _update_base_settings_env(platform_name: str, platform_config: dict, printer):
    """更新基础 settings.json 的 env 配置为指定平台

    Args:
        platform_name: 平台名称（如 "glm", "gaccode"）
        platform_config: 平台配置
        printer: 颜色打印机
    """
    import json

    # 查找基础 settings.json（优先当前目录，其次全局配置）
    cwd_settings_path = Path.cwd() / "settings.json"
    global_settings_path = Path.home() / ".claude" / "settings.json"

    # 确定要修改的文件路径
    base_settings_path = None
    if cwd_settings_path.exists():
        base_settings_path = cwd_settings_path
    elif global_settings_path.exists():
        base_settings_path = global_settings_path

    if not base_settings_path:
        printer.print("Warning: No base settings.json found to update", Colors.YELLOW)
        return

    try:
        # 读取基础配置
        with open(base_settings_path, "r", encoding="utf-8") as f:
            settings_data = json.load(f)

        # 更新 env 配置
        env_config = _create_settings_env_config(platform_config)
        settings_data["env"] = env_config

        # 写回基础配置
        with open(base_settings_path, "w", encoding="utf-8") as f:
            json.dump(settings_data, f, indent=2, ensure_ascii=False)

        printer.print(f"Updated base settings.json env: {base_settings_path}", Colors.GREEN)
    except Exception as e:
        printer.print(f"Warning: Failed to update base settings.json: {e}", Colors.YELLOW)


if __name__ == "__main__":
    sys.exit(main())