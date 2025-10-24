#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Environment Manager - 环境管理器
负责设置和管理Claude Code的环境变量
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..utils.logger import get_logger


class EnvironmentManager:
    """环境管理器"""

    def __init__(self, config_manager):
        """初始化环境管理器"""
        self.config_manager = config_manager
        self.logger = get_logger("environment")

    def setup_environment(self, platform_config: Dict[str, Any]) -> Dict[str, str]:
        """
        为Claude Code设置环境变量

        Args:
            platform_config: 平台配置

        Returns:
            设置的环境变量字典
        """
        try:
            self.logger.info("Setting up Claude Code environment")

            # 清理现有环境变量
            self._clear_existing_env_vars()

            # 设置新的环境变量
            env_vars = self._setup_new_env_vars(platform_config)

            self.logger.info("Environment configured successfully")
            return env_vars

        except Exception as e:
            self.logger.error(f"Error setting up environment: {e}")
            return {}

    def _clear_existing_env_vars(self):
        """清理现有的Claude Code相关环境变量"""
        # 需要清理的环境变量列表
        vars_to_clear = [
            # Claude Code 核心环境变量
            "ANTHROPIC_API_KEY",
            "ANTHROPIC_AUTH_TOKEN",
            "ANTHROPIC_BASE_URL",
            "ANTHROPIC_API_URL",
            "ANTHROPIC_API_VERSION",
            "ANTHROPIC_CUSTOM_HEADERS",
            "ANTHROPIC_DEFAULT_HEADERS",
            "ANTHROPIC_MODEL",
            "ANTHROPIC_SMALL_FAST_MODEL",
            "ANTHROPIC_SMALL_FAST_MODEL_AWS_REGION",
            "ANTHROPIC_TIMEOUT_MS",
            "ANTHROPIC_REQUEST_TIMEOUT",
            "ANTHROPIC_MAX_RETRIES",
            # Claude Code 默认模型环境变量
            "ANTHROPIC_DEFAULT_HAIKU_MODEL",
            "ANTHROPIC_DEFAULT_OPUS_MODEL",
            "ANTHROPIC_DEFAULT_SONNET_MODEL",
            # Claude Code 配置变量
            "CLAUDE_CODE_MAX_OUTPUT_TOKENS",
            # 其他AI平台环境变量
            "MOONSHOT_API_KEY",
            "DEEPSEEK_API_KEY",
            "SILICONFLOW_API_KEY",
            # 可能的其他相关变量
            "CLAUDE_API_KEY",
            "CLAUDE_AUTH_TOKEN",
            "CLAUDE_BASE_URL",
            "CLAUDE_MODEL",
        ]

        cleared_vars = []
        for var_name in vars_to_clear:
            if var_name in os.environ:
                del os.environ[var_name]
                cleared_vars.append(var_name)

        if cleared_vars:
            self.logger.debug(f"Cleared {len(cleared_vars)} environment variables")

    def _setup_new_env_vars(self, platform_config: Dict[str, Any]) -> Dict[str, str]:
        """设置新的环境变量"""
        env_vars = {}

        # 设置认证信息 - 确保只有一个认证变量
        if platform_config.get("api_key"):
            env_vars["ANTHROPIC_API_KEY"] = platform_config["api_key"]
            env_vars["ANTHROPIC_AUTH_TOKEN"] = ""  # 清空另一个
            self.logger.debug("Using API key authentication")
        elif platform_config.get("auth_token"):
            env_vars["ANTHROPIC_AUTH_TOKEN"] = platform_config["auth_token"]
            env_vars["ANTHROPIC_API_KEY"] = ""  # 清空另一个
            self.logger.debug("Using auth token authentication")
        elif platform_config.get("login_token"):
            env_vars["ANTHROPIC_API_KEY"] = platform_config["login_token"]
            env_vars["ANTHROPIC_AUTH_TOKEN"] = ""  # 清空另一个
            self.logger.debug("Using login token authentication")

        # 设置API基础URL
        api_base_url = platform_config.get("api_base_url")
        if api_base_url:
            env_vars["ANTHROPIC_BASE_URL"] = api_base_url
            self.logger.debug(f"Set API base URL: {api_base_url}")

        # 设置模型配置
        model = platform_config.get("model")
        if model:
            env_vars["ANTHROPIC_MODEL"] = model
            env_vars["ANTHROPIC_DEFAULT_HAIKU_MODEL"] = model
            env_vars["ANTHROPIC_DEFAULT_SONNET_MODEL"] = model
            env_vars["ANTHROPIC_DEFAULT_OPUS_MODEL"] = model
            self.logger.debug(f"Set model: {model}")

        small_model = platform_config.get("small_model", model)
        if small_model:
            env_vars["ANTHROPIC_SMALL_FAST_MODEL"] = small_model
            self.logger.debug(f"Set small model: {small_model}")

        # 设置Claude Code特定配置
        claude_code_config = platform_config.get("claude_code_config", {})
        if claude_code_config.get("max_output_tokens"):
            env_vars["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = str(
                claude_code_config["max_output_tokens"]
            )
            self.logger.debug("Set max output tokens")

        # 检测并设置Git Bash路径（Windows）
        if os.name == 'nt':
            git_bash_path = self._detect_git_bash_path()
            if git_bash_path:
                env_vars["CLAUDE_CODE_GIT_BASH_PATH"] = str(git_bash_path)
                self.logger.debug(f"Set Git Bash path: {git_bash_path.name}")

        self.logger.info(f"Set {len(env_vars)} environment variables")
        return env_vars

    def _detect_git_bash_path(self) -> Optional[Path]:
        """检测Git Bash可执行文件路径"""
        possible_paths = []

        # 1. 检查环境变量指向的Git安装
        git_env_vars = [
            ("GIT_INSTALL_PATH", "Git/bin/bash.exe"),
            ("PROGRAMFILES", "Git/bin/bash.exe"),
            ("PROGRAMFILES(X86)", "Git/bin/bash.exe"),
            ("LOCALAPPDATA", "Programs/Git/bin/bash.exe"),
        ]

        for env_var, relative_path in git_env_vars:
            if env_var in os.environ:
                git_path = Path(os.environ[env_var]) / relative_path
                if git_path.exists():
                    possible_paths.append(git_path)

        # 2. 基于Git环境变量的路径检测
        self._detect_git_from_env_vars(possible_paths)

        # 3. 常见安装位置
        common_paths = [
            Path("C:/Program Files/Git/bin/bash.exe"),
            Path("C:/Program Files (x86)/Git/bin/bash.exe"),
            Path(r"C:\Program Files\Git\usr\bin\bash.exe"),
        ]
        possible_paths.extend([p for p in common_paths if p.exists()])

        # 4. 用户安装路径
        user_install = Path.home() / "AppData" / "Local" / "Programs" / "Git" / "bin" / "bash.exe"
        if user_install.exists():
            possible_paths.append(user_install)

        # 5. 使用which命令查找 - 优先级更高，移到前面
        git_bash = shutil.which("bash.exe")
        if git_bash:
            possible_paths.insert(0, Path(git_bash))  # 插入到最前面，优先使用PATH中的bash

        # 选择第一个可用的路径
        for git_path in possible_paths:
            try:
                # 验证是否可以执行
                if git_path.is_file():
                    self.logger.debug(f"Found Git Bash at: {git_path}")
                    return git_path
            except Exception:
                continue

        self.logger.debug("No Git Bash found")
        return None

    def _detect_git_from_env_vars(self, possible_paths: list):
        """基于Git环境变量检测Git安装路径"""
        # Git相关的环境变量检测
        git_env_detections = [
            # 1. GIT_EXEC_PATH - Git核心程序路径（最可靠）
            ("GIT_EXEC_PATH", "bin/bash.exe"),
            # 2. GIT_INSTALL_ROOT - Git for Windows安装根目录
            ("GIT_INSTALL_ROOT", "bin/bash.exe"),
            # 3. Program Files中的Git（通过环境变量动态获取）
            ("PROGRAMFILES", "Git/bin/bash.exe"),
            ("PROGRAMFILES(X86)", "Git/bin/bash.exe"),
            # 4. LOCALAPPDATA中的Git
            ("LOCALAPPDATA", "Programs/Git/bin/bash.exe"),
            # 5. 用户自定义Git路径
            ("GIT_PATH", "bin/bash.exe"),
            ("GIT_HOME", "bin/bash.exe"),
            ("GIT_DIR", "../bin/bash.exe"),  # GIT_DIR通常指向.git目录，需要向上查找
        ]

        for env_var, relative_path in git_env_detections:
            if env_var in os.environ:
                git_base_path = Path(os.environ[env_var])
                git_bash_path = git_base_path / relative_path

                if git_bash_path.exists() and git_bash_path.is_file():
                    possible_paths.append(git_bash_path)
                    self.logger.debug(f"Found Git via {env_var}: {git_bash_path}")
                    return  # 找到就停止

        # 如果环境变量检测失败，尝试使用git命令查询
        try:
            # 使用git --exec-path查询Git安装路径
            result = subprocess.run(
                ["git", "--exec-path"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            if result.returncode == 0 and result.stdout.strip():
                git_exec_path = Path(result.stdout.strip())
                git_bash_path = git_exec_path.parent / "bash.exe"

                if git_bash_path.exists():
                    possible_paths.append(git_bash_path)
                    self.logger.debug(f"Found Git via git --exec-path: {git_bash_path}")
                    return

        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            self.logger.debug("Git command not available for path detection")

        # 检查PATH中是否有git.exe，然后推导bash路径
        git_exe_path = shutil.which("git.exe")
        if git_exe_path:
            git_dir = Path(git_exe_path).parent
            git_bash_path = git_dir / "bash.exe"

            if git_bash_path.exists():
                possible_paths.append(git_bash_path)
                self.logger.debug(f"Found Git bash via git.exe in PATH: {git_bash_path}")
                return

    def create_subprocess_env(self, platform_config: Dict[str, Any]) -> Dict[str, str]:
        """
        为子进程创建环境变量字典

        Args:
            platform_config: 平台配置

        Returns:
            完整的环境变量字典
        """
        # 复制当前环境变量
        process_env = os.environ.copy()

        # 添加平台特定的环境变量
        platform_env = self._setup_new_env_vars(platform_config)
        process_env.update(platform_env)

        self.logger.debug(f"Created subprocess environment with {len(platform_env)} variables")
        return process_env

    def validate_environment(self, platform_config: Dict[str, Any]) -> bool:
        """
        验证环境配置是否有效

        Args:
            platform_config: 平台配置

        Returns:
            配置是否有效
        """
        try:
            # 检查认证信息
            has_auth = any([
                platform_config.get("api_key"),
                platform_config.get("auth_token"),
                platform_config.get("login_token")
            ])

            if not has_auth:
                self.logger.warning("No authentication information found")
                return False

            # 检查API基础URL
            api_base_url = platform_config.get("api_base_url")
            if not api_base_url:
                self.logger.warning("No API base URL found")
                return False

            # 检查模型配置
            model = platform_config.get("model")
            if not model:
                self.logger.warning("No model specified")
                return False

            self.logger.debug("Environment configuration is valid")
            return True

        except Exception as e:
            self.logger.error(f"Error validating environment: {e}")
            return False