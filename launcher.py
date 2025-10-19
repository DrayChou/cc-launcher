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
        printer.print("  Please install: npm install -g @anthropic-ai/claude-code", Colors.YELLOW)

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
            printer.print("  npm install -g @anthropic-ai/claude-code", Colors.YELLOW)
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

        # 关键修复：临时修改settings.json文件（模仿原始gaccode.com）
        settings_backup_path = None
        try:
            settings_backup_path = _modify_settings_json_temporarily(platform_config, printer)
        except Exception as e:
            printer.print(f"Warning: Failed to modify settings.json: {e}", Colors.YELLOW)

        try:
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
        finally:
            # 恢复原始settings.json
            if settings_backup_path and settings_backup_path.exists():
                try:
                    user_settings_path = Path.home() / ".claude" / "settings.json"
                    shutil.move(settings_backup_path, user_settings_path)
                    printer.print("Settings.json restored", Colors.GREEN)
                except Exception as e:
                    printer.print(f"Warning: Failed to restore settings.json: {e}", Colors.YELLOW)

    except KeyboardInterrupt:
        printer.print("\nInterrupted by user", Colors.YELLOW)
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        printer.print(f"Unexpected error: {e}", Colors.RED)
        return 1


def _modify_settings_json_temporarily(platform_config: dict, printer) -> Optional[Path]:
    """临时修改settings.json文件，确保Claude Code读取正确的配置

    Args:
        platform_config: 平台配置
        printer: 颜色打印机

    Returns:
        备份文件路径，如果settings.json不存在则返回None
    """
    import shutil
    import json

    user_settings_path = Path.home() / ".claude" / "settings.json"
    backup_settings_path = Path.home() / ".claude" / "settings.json.backup"

    if not user_settings_path.exists():
        return None

    try:
        # 备份原始settings.json
        shutil.copy2(user_settings_path, backup_settings_path)
        printer.print("Backed up settings.json to settings.json.backup", Colors.GRAY)

        # 读取并修改settings.json
        with open(user_settings_path, "r", encoding="utf-8") as f:
            settings_data = json.load(f)

        # 保存原始env配置用于调试
        original_env = settings_data.get("env", {})
        printer.print(f"Original env in settings.json: {list(original_env.keys())}", Colors.CYAN)

        # 创建新的环境变量配置
        env_config = _create_settings_env_config(platform_config)

        # 设置正确的环境变量配置
        settings_data["env"] = env_config

        # 写入修改后的settings.json
        with open(user_settings_path, "w", encoding="utf-8") as f:
            json.dump(settings_data, f, indent=2, ensure_ascii=False)

        printer.print("Updated env configuration in settings.json", Colors.GREEN)
        return backup_settings_path
    except Exception as e:
        printer.print(f"Warning: Failed to modify settings.json: {e}", Colors.RED)
        return None


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


if __name__ == "__main__":
    sys.exit(main())