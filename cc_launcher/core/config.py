#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Manager - 共享配置管理器
与 cc-status 共享相同的配置文件和目录结构
"""

import sys
from pathlib import Path

# 添加 cc-status 到路径以共享配置模块
scripts_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(scripts_dir / "cc-status"))

try:
    from cc_status.core.config import ConfigManager as BaseConfigManager
except ImportError:
    # 如果 cc-status 不可用，提供备用实现
    import json
    from typing import Dict, Any, Optional
    from ..utils.logger import get_logger

    class BaseConfigManager:
        def __init__(self):
            self.home_dir = Path.home()
            self.claude_dir = self.home_dir / ".claude"
            self.config_dir = self.claude_dir / "config"
            self.cache_dir = self.claude_dir / "cache"
            self.logs_dir = self.claude_dir / "logs"

            # 确保目录存在
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.logs_dir.mkdir(parents=True, exist_ok=True)

            self.logger = get_logger("config")

            # 配置文件路径
            self.platforms_file = self.config_dir / "platforms.json"
            self.status_file = self.config_dir / "status.json"
            self.launcher_file = self.config_dir / "launcher.json"

        def _load_json_file(self, file_path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
            """安全加载JSON文件"""
            try:
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                else:
                    # 创建默认配置文件
                    self._save_json_file(file_path, default)
                    return default.copy()
            except (json.JSONDecodeError, IOError) as e:
                self.logger.warning(f"Failed to load {file_path}: {e}")
                return default.copy()

        def _save_json_file(self, file_path: Path, data: Dict[str, Any]) -> bool:
            """安全保存JSON文件"""
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                self.logger.debug(f"Saved configuration to {file_path}")
                return True
            except IOError as e:
                self.logger.error(f"Failed to save {file_path}: {e}")
                return False

        def get_platforms_config(self) -> Dict[str, Any]:
            """获取平台配置"""
            default_config = {
                "platforms": {
                    "gaccode": {
                        "name": "GAC Code",
                        "api_base_url": "https://relay05.gaccode.com/claudecode",
                        "login_token": "",
                        "model": "claude-3-5-sonnet-20241022",
                        "enabled": True
                    },
                    "deepseek": {
                        "name": "DeepSeek",
                        "api_base_url": "https://api.deepseek.com/anthropic",
                        "api_key": "",
                        "model": "deepseek-chat",
                        "enabled": True
                    }
                },
                "default_platform": "gaccode",
                "aliases": {
                    "gc": "gaccode",
                    "dp": "deepseek",
                    "ds": "deepseek"
                }
            }
            return self._load_json_file(self.platforms_file, default_config)

        def get_status_config(self) -> Dict[str, Any]:
            """获取状态栏配置"""
            default_config = {
                "show_balance": True,
                "show_model": True,
                "show_git_branch": True,
                "show_time": True,
                "layout": "single_line"
            }
            return self._load_json_file(self.status_file, default_config)

        def get_launcher_config(self) -> Dict[str, Any]:
            """获取启动器配置"""
            default_config = {
                "default_platform": "gaccode",
                "claude_executable": "claude",
                "auto_create_session": True,
                "continue_last_session": False
            }
            return self._load_json_file(self.launcher_file, default_config)

        def get_platform_config(self, platform_name: str) -> Optional[Dict[str, Any]]:
            """获取特定平台配置"""
            platforms_config = self.get_platforms_config()
            return platforms_config.get("platforms", {}).get(platform_name)

        def get_cache_dir(self) -> Path:
            """获取缓存目录"""
            return self.cache_dir

        def get_logs_dir(self) -> Path:
            """获取日志目录"""
            return self.logs_dir


class ConfigManager(BaseConfigManager):
    """启动器配置管理器 - 继承自基础配置管理器"""

    def __init__(self):
        super().__init__()
        self.logger.debug("Initialized cc-launcher ConfigManager")

    def get_enabled_platforms(self) -> Dict[str, Dict[str, Any]]:
        """获取所有启用的平台配置"""
        platforms_config = self.get_platforms_config()
        enabled_platforms = {}

        for platform_id, platform_config in platforms_config.get("platforms", {}).items():
            if platform_config.get("enabled", False):
                # 检查是否有认证信息
                has_auth = any([
                    platform_config.get("api_key"),
                    platform_config.get("auth_token"),
                    platform_config.get("login_token")
                ])
                if has_auth:
                    enabled_platforms[platform_id] = platform_config

        return enabled_platforms

    def resolve_platform_alias(self, platform: str) -> str:
        """解析平台别名"""
        platforms_config = self.get_platforms_config()
        aliases = platforms_config.get("aliases", {})
        return aliases.get(platform, platform)

    def validate_platform_config(self, platform_name: str) -> bool:
        """验证平台配置是否完整"""
        platform_config = self.get_platform_config(platform_name)
        if not platform_config:
            return False

        # 检查必要字段
        required_fields = ["name", "api_base_url", "model", "enabled"]
        for field in required_fields:
            if field not in platform_config:
                return False

        # 检查认证信息
        has_auth = any([
            platform_config.get("api_key"),
            platform_config.get("auth_token"),
            platform_config.get("login_token")
        ])

        return has_auth