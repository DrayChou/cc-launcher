#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Detector - Claude Code命令检测器
智能检测系统中可用的Claude Code命令
"""

import os
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

        Returns:
            检测到的命令列表，如果未找到则返回None
        """
        # 尝试不同的Claude Code启动方式
        claude_commands = [
            # 1. 直接的claude命令 (全局安装)
            ["claude"],
            # 2. npx claude (局部安装或fallback)
            ["npx", "@anthropic-ai/claude-code"],
            # 3. node直接调用 (备用方案)
            ["node", "-e", "require('@anthropic-ai/claude-code/cli')"],
            # 4. pnpx claude (pnpm用户)
            ["pnpx", "claude"],
            # 5. yarn claude (yarn用户)
            ["yarn", "claude"],
            # 6. 使用完整路径的检测
            self._get_full_path_command("claude"),
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
                        self.logger.info(f"Detected Claude Code: {' '.join(cmd)}")
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
        """获取命令的完整路径"""
        try:
            # 检查是否是复合命令（如 "npx @anthropic-ai/claude-code"）
            if " " in command:
                base_cmd = command.split()[0]
                full_path = shutil.which(base_cmd)
                if full_path:
                    return [full_path] + command.split()[1:]
            else:
                full_path = shutil.which(command)
                if full_path:
                    return [full_path]

        except Exception as e:
            self.logger.debug(f"Error finding full path for {command}: {e}")

        return None

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
        建议Claude Code安装方法

        Returns:
            安装方法建议列表
        """
        suggestions = [
            "npm install -g @anthropic-ai/claude-code",
            "npx @anthropic-ai/claude-code",
            "Use package manager: scoop install claude-code",
            "Use package manager: npm install -g claude-code"
        ]

        # 根据操作系统调整建议
        if os.name == 'nt':
            suggestions.insert(0, "Download from: https://claude.ai/download")

        return suggestions