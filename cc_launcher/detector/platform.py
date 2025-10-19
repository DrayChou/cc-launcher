#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Platform Detector - 平台检测器
检测可用的AI平台
"""

from typing import Dict, Any, Optional, Tuple
from ..utils.logger import get_logger


class PlatformDetector:
    """平台检测器"""

    def __init__(self, config_manager):
        """初始化平台检测器"""
        self.config_manager = config_manager
        self.logger = get_logger("platform_detector")

    def detect_platform(self, requested_platform: Optional[str] = None) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        检测要使用的平台

        Args:
            requested_platform: 用户请求的平台名称或别名

        Returns:
            (平台名称, 平台配置) 元组，如果未找到则返回None
        """
        try:
            platforms_config = self.config_manager.get_platforms_config()

            # 解析平台别名
            resolved_platform = self._resolve_platform_alias(requested_platform, platforms_config)

            if resolved_platform:
                # 检查平台是否可用
                platform_config = platforms_config.get("platforms", {}).get(resolved_platform)
                if platform_config and self._is_platform_available(platform_config):
                    self.logger.info(f"Selected platform: {platform_config.get('name', resolved_platform)}")
                    return resolved_platform, platform_config
                else:
                    self.logger.warning(f"Platform {resolved_platform} is not available")
                    return None

            # 如果没有指定平台，选择默认平台
            return self._select_default_platform(platforms_config)

        except Exception as e:
            self.logger.error(f"Error detecting platform: {e}")
            return None

    def _resolve_platform_alias(self, platform: Optional[str], platforms_config: Dict[str, Any]) -> Optional[str]:
        """解析平台别名"""
        if not platform:
            return None

        aliases = platforms_config.get("aliases", {})
        resolved = aliases.get(platform.lower(), platform.lower())

        if resolved in platforms_config.get("platforms", {}):
            return resolved

        return None

    def _is_platform_available(self, platform_config: Dict[str, Any]) -> bool:
        """检查平台是否可用"""
        try:
            # 检查是否启用
            if not platform_config.get("enabled", False):
                return False

            # 检查是否有认证信息
            has_auth = any([
                platform_config.get("api_key"),
                platform_config.get("auth_token"),
                platform_config.get("login_token")
            ])

            if not has_auth:
                return False

            # 检查必要字段
            required_fields = ["name", "api_base_url", "model"]
            for field in required_fields:
                if not platform_config.get(field):
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Error checking platform availability: {e}")
            return False

    def _select_default_platform(self, platforms_config: Dict[str, Any]) -> Optional[Tuple[str, Dict[str, Any]]]:
        """选择默认平台"""
        try:
            # 1. 尝试使用配置的默认平台
            default_platform = platforms_config.get("default_platform")
            if default_platform:
                platform_config = platforms_config.get("platforms", {}).get(default_platform)
                if platform_config and self._is_platform_available(platform_config):
                    self.logger.info(f"Using configured default platform: {default_platform}")
                    return default_platform, platform_config

            # 2. 选择第一个可用的平台
            for platform_name, platform_config in platforms_config.get("platforms", {}).items():
                if self._is_platform_available(platform_config):
                    self.logger.info(f"Using first available platform: {platform_name}")
                    return platform_name, platform_config

            # 3. 没有可用的平台
            self.logger.warning("No available platforms found")
            return None

        except Exception as e:
            self.logger.error(f"Error selecting default platform: {e}")
            return None

    def list_available_platforms(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有可用平台

        Returns:
            可用平台字典
        """
        try:
            platforms_config = self.config_manager.get_platforms_config()
            available_platforms = {}

            for platform_id, platform_config in platforms_config.get("platforms", {}).items():
                if self._is_platform_available(platform_config):
                    available_platforms[platform_id] = platform_config

            self.logger.info(f"Found {len(available_platforms)} available platforms")
            return available_platforms

        except Exception as e:
            self.logger.error(f"Error listing available platforms: {e}")
            return {}

    def validate_platform_config(self, platform_name: str) -> bool:
        """
        验证平台配置

        Args:
            platform_name: 平台名称

        Returns:
            配置是否有效
        """
        try:
            platform_config = self.config_manager.get_platform_config(platform_name)
            if not platform_config:
                return False

            return self._is_platform_available(platform_config)

        except Exception as e:
            self.logger.error(f"Error validating platform config for {platform_name}: {e}")
            return False

    def get_platform_status(self, platform_name: str) -> Dict[str, Any]:
        """
        获取平台状态信息

        Args:
            platform_name: 平台名称

        Returns:
            平台状态信息
        """
        try:
            platform_config = self.config_manager.get_platform_config(platform_name)
            if not platform_config:
                return {
                    "name": platform_name,
                    "enabled": False,
                    "configured": False,
                    "has_auth": False,
                    "available": False
                }

            enabled = platform_config.get("enabled", False)
            has_auth = any([
                platform_config.get("api_key"),
                platform_config.get("auth_token"),
                platform_config.get("login_token")
            ])
            available = self._is_platform_available(platform_config)

            return {
                "name": platform_config.get("name", platform_name),
                "enabled": enabled,
                "configured": bool(platform_config.get("api_base_url") and platform_config.get("model")),
                "has_auth": has_auth,
                "available": available
            }

        except Exception as e:
            self.logger.error(f"Error getting platform status for {platform_name}: {e}")
            return {
                "name": platform_name,
                "enabled": False,
                "configured": False,
                "has_auth": False,
                "available": False,
                "error": str(e)
            }