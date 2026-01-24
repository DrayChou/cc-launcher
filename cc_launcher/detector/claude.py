#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Detector - Claude Code命令检测器
智能检测系统中可用的Claude Code命令
"""

import os
import glob
import shutil
import subprocess
from typing import List, Optional
from ..utils.logger import get_logger


class ClaudeDetector:
    """Claude Code命令检测器"""

    def __init__(self):
        """初始化检测器"""
        self.logger = get_logger("claude_detector")

    def detect_claude_command(self) -> Optional[List[str]]:
        """
        检测可用的Claude Code命令

        优先级顺序（按官方推荐）：
        1. Native Installer (推荐) - 自动更新
        2. Homebrew / WinGet - 需手动更新
        3. npm (deprecated) - 需手动更新

        Returns:
            检测到的命令列表，如果未找到则返回None
        """
        # 按官方推荐优先级尝试不同的Claude Code启动方式
        claude_commands = [
            # === 优先级1: Native Installer (官方推荐，支持自动更新) ===
            # 1.1 直接的 claude 命令 (Native Installer 全局安装)
            ["claude"],
            # 1.2 Native Installer 完整路径
            self._get_full_path_command("claude"),

            # === 优先级2: 包管理器 ===
            # 2.1 Homebrew (macOS/Linux)
            self._get_homebrew_command(),
            # 2.2 WinGet (Windows)
            self._get_winget_command(),

            # === 优先级3: npm 方式 (已 deprecated) ===
            # 3.1 npx claude (局部安装或fallback)
            ["npx", "@anthropic-ai/claude-code"],
            # 3.2 node直接调用 (备用方案)
            ["node", "-e", "require('@anthropic-ai/claude-code/cli')"],
            # 3.3 其他 npm 包管理器
            ["pnpx", "claude"],
            ["yarn", "claude"],
            # 3.4 npx 完整路径
            self._get_full_path_command("npx @anthropic-ai/claude-code"),
        ]

        # 过滤掉None的命令
        claude_commands = [cmd for cmd in claude_commands if cmd]

        for cmd in claude_commands:
            try:
                # 测试命令是否可用 - 运行 --version 检查
                test_cmd = cmd + ["--version"]
                result = subprocess.run(
                    test_cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=10,
                    shell=(len(cmd) == 1 and os.name == "nt")  # Windows需要shell=True
                )

                if result.returncode == 0:
                    # 验证输出包含Claude Code相关信息
                    output = result.stdout.strip() or result.stderr.strip()
                    if "claude" in output.lower() or "anthropic" in output.lower():
                        install_type = self.detect_installation_type(cmd)
                        self.logger.info(f"Detected Claude Code: {' '.join(cmd)} ({install_type})")
                        self.logger.debug(f"Version: {output}")
                        return cmd

            except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
                # 这个命令不可用，尝试下一个
                continue
            except Exception as e:
                self.logger.debug(f"Unexpected error testing command {cmd}: {e}")
                continue

        self.logger.warning("Claude Code not found")
        return None

    def _get_full_path_command(self, command: str) -> Optional[List[str]]:
        """获取命令的完整路径（优先选择 Native Installer）"""
        try:
            if " " in command:
                # 复合命令
                base_cmd = command.split()[0]
                full_path = shutil.which(base_cmd)
                if full_path:
                    return [full_path] + command.split()[1:]
            else:
                # 对于 claude 命令，优先选择 Native Installer 路径
                if command in ["claude", "claude.exe"]:
                    # 定义优先级路径（Native Installer 优先）
                    priority_paths = []

                    # Windows Native Installer 路径
                    if os.name == "nt":
                        priority_paths.append(os.path.expanduser("~\\.local\\bin\\claude.exe"))

                    # Unix-like Native Installer 路径
                    priority_paths.append(os.path.expanduser("~/.local/bin/claude"))

                    # 检查优先级路径是否存在
                    for path in priority_paths:
                        if os.path.exists(path):
                            self.logger.debug(f"Found priority path: {path}")
                            return [path]

                    # 如果优先路径都不存在，使用系统 PATH
                    full_path = shutil.which(command)
                    if full_path:
                        return [full_path]
                else:
                    # 其他命令直接使用 which
                    full_path = shutil.which(command)
                    if full_path:
                        return [full_path]

        except Exception as e:
            self.logger.debug(f"Error finding full path for {command}: {e}")

        return None

    def _get_homebrew_command(self) -> Optional[List[str]]:
        """检测 Homebrew 安装的 Claude Code"""
        homebrew_paths = [
            "/usr/local/bin/claude",  # macOS Intel
            "/opt/homebrew/bin/claude",  # macOS Apple Silicon
            os.path.expanduser("~/.linuxbrew/bin/claude"),  # Linux Homebrew
        ]
        for path in homebrew_paths:
            if os.path.exists(path):
                self.logger.debug(f"Found Homebrew installation: {path}")
                return [path]
        return None

    def _get_winget_command(self) -> Optional[List[str]]:
        """检测 WinGet 安装的 Claude Code"""
        if os.name == "nt":
            # WinGet 通常安装到用户目录
            local_app = os.path.expandvars("%LOCALAPPDATA%")
            possible_paths = [
                os.path.join(local_app, "Microsoft", "WindowsApps", "claude.exe"),
                os.path.join(local_app, "Microsoft", "WindowsApps", "Anthropic.ClaudeCode_*", "claude.exe"),
            ]
            for path in possible_paths:
                # 处理通配符
                if "*" in path:
                    matching = glob.glob(path)
                    if matching:
                        self.logger.debug(f"Found WinGet installation: {matching[0]}")
                        return [matching[0]]
                elif os.path.exists(path):
                    self.logger.debug(f"Found WinGet installation: {path}")
                    return [path]
        return None

    def detect_installation_type(self, command: List[str]) -> str:
        """
        检测 Claude Code 安装类型

        Args:
            command: Claude 命令列表

        Returns:
            安装类型字符串: native, homebrew, winget, npm, unknown
        """
        if not command:
            return "unknown"

        # npm 特征（最优先检查，因为命令包含 npx/npm/node）
        if "npx" in command or "npm" in str(command).lower() or "node" in command:
            return "npm"

        cmd_name = command[0]
        cmd_path = cmd_name

        # 对于 claude 命令，优先检查 Native Installer 路径
        if cmd_name in ["claude", "claude.exe"]:
            # 定义 Native Installer 路径特征
            native_paths = [
                os.path.expanduser("~\\.local\\bin\\claude.exe"),  # Windows
                os.path.expanduser("~/.local/bin/claude"),  # Unix
                "/usr/local/bin/claude",
                "/usr/bin/claude",
            ]

            # Homebrew 路径特征
            homebrew_paths = [
                "/usr/local/bin/claude",  # 可能是 Homebrew
                "/opt/homebrew/bin/claude",  # macOS ARM
                os.path.expanduser("~/.linuxbrew/bin/claude"),
            ]

            # WinGet 路径特征
            if os.name == "nt":
                local_app = os.path.expandvars("%LOCALAPPDATA%")
                winget_pattern = os.path.join(local_app, "Microsoft", "WindowsApps")

            # 优先检查 Native Installer 路径
            for path in native_paths:
                if os.path.exists(path):
                    return "native"

            # 检查 Homebrew 路径
            for path in homebrew_paths:
                if os.path.exists(path):
                    return "homebrew"

            # 检查 WinGet 路径
            if os.name == "nt" and "WindowsApps" in winget_pattern:
                # 使用 which 获取实际路径
                actual_path = shutil.which(cmd_name)
                if actual_path and "windowsapps" in actual_path.lower():
                    return "winget"

            # 最后使用 which 获取完整路径进行判断
            cmd_path = shutil.which(cmd_name)
            if not cmd_path:
                return "unknown"

        cmd_path_lower = cmd_path.lower()

        # 根据路径特征判断
        if "windowsapps" in cmd_path_lower:
            return "winget"
        if "homebrew" in cmd_path_lower or "/cellar/" in cmd_path_lower:
            return "homebrew"
        if ".local" in cmd_path_lower or "/usr/local/bin" in cmd_path_lower or "/usr/bin" in cmd_path_lower:
            return "native"
        if "nodejs" in cmd_path_lower or "npm" in cmd_path_lower:
            return "npm"

        return "unknown"

    def validate_claude_installation(self, command: List[str]) -> bool:
        """
        验证Claude Code安装是否正常

        Args:
            command: Claude命令

        Returns:
            安装是否正常
        """
        try:
            # 测试基本功能
            result = subprocess.run(
                command + ["--help"],
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode == 0:
                self.logger.info("Claude Code installation is valid")
                return True
            else:
                self.logger.warning(f"Claude Code help command failed: {result.returncode}")
                return False

        except Exception as e:
            self.logger.error(f"Error validating Claude Code installation: {e}")
            return False

    def get_claude_version(self, command: List[str]) -> Optional[str]:
        """
        获取Claude Code版本信息

        Args:
            command: Claude命令

        Returns:
            版本信息字符串
        """
        try:
            result = subprocess.run(
                command + ["--version"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                version = result.stdout.strip() or result.stderr.strip()
                return version
            else:
                return None

        except Exception as e:
            self.logger.error(f"Error getting Claude Code version: {e}")
            return None

    def suggest_installation_methods(self) -> List[str]:
        """
        建议Claude Code安装方法（按官方推荐优先级）

        Returns:
            安装方法建议列表（格式化的字符串）
        """
        suggestions = []

        # 根据操作系统提供对应的安装建议
        if os.name == 'nt':  # Windows
            suggestions.extend([
                "【推荐】Native Installer (自动更新):",
                "  PowerShell: irm https://claude.ai/install.ps1 | iex",
                "  CMD: curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd",
                "",
                "【包管理器】(需手动更新):",
                "  WinGet: winget install Anthropic.ClaudeCode",
                "",
                "【已弃用】npm 方式 (不推荐):",
                "  npm install -g @anthropic-ai/claude-code",
            ])
        else:  # macOS/Linux
            suggestions.extend([
                "【推荐】Native Installer (自动更新):",
                "  curl -fsSL https://claude.ai/install.sh | bash",
                "",
                "【包管理器】(需手动更新):",
                "  Homebrew: brew install --cask claude-code",
                "",
                "【已弃用】npm 方式 (不推荐):",
                "  npm install -g @anthropic-ai/claude-code",
            ])

        # 添加版本锁定选项说明
        suggestions.extend([
            "",
            "【版本锁定选项】",
            "  安装 stable 版本: bash -s stable",
            "  安装指定版本: bash -s 1.0.58",
        ])

        return suggestions