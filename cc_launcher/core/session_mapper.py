#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Session Mapper v2 - 增强版UUID会话映射系统
支持双UUID映射（标准UUID + 前缀UUID）和会话-平台关联
"""

import json
import uuid
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from ..utils.logger import get_logger


class SessionMapper:
    """增强版会话映射器"""

    def __init__(self):
        self.logger = get_logger("session_mapper")
        self.claude_dir = Path.home() / ".claude"
        self.cache_dir = self.claude_dir / "cache" / "sessions"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 会话映射文件
        self.session_mappings_file = self.cache_dir / "session-mappings.json"

        # 动态生成平台前缀配置
        self.platform_prefixes = self._generate_platform_prefixes()

        # 加载现有映射
        self.mappings = self._load_mappings()

    def _generate_platform_prefixes(self) -> Dict[str, str]:
        """动态生成平台前缀映射"""
        # 读取平台配置文件
        from ..core.config import ConfigManager
        config_manager = ConfigManager()
        platforms_config = config_manager.get_platforms_config()
        platforms = platforms_config.get("platforms", {})

        # 按照平台名称排序并生成数字前缀
        sorted_platforms = sorted(platforms.keys())
        platform_prefixes = {}

        for index, platform_name in enumerate(sorted_platforms, 1):
            prefix = f"{index:02d}"  # 格式化为两位数字，如 "01", "02", etc.
            platform_prefixes[platform_name] = prefix

        self.logger.debug(f"Generated platform prefixes: {platform_prefixes}")
        return platform_prefixes

    def _load_mappings(self) -> Dict[str, Any]:
        """加载会话映射"""
        try:
            if self.session_mappings_file.exists():
                with open(self.session_mappings_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                return {
                    "mappings": {},
                    "reverse_mappings": {},
                    "platform_sessions": {},
                    "created_at": datetime.now().isoformat(),
                    "version": "2.0"
                }
        except Exception as e:
            self.logger.error(f"Error loading session mappings: {e}")
            return {
                "mappings": {},
                "reverse_mappings": {},
                "platform_sessions": {},
                "created_at": datetime.now().isoformat(),
                "version": "2.0"
            }

    def _save_mappings(self) -> bool:
        """保存会话映射"""
        try:
            # 更新修改时间
            self.mappings["last_updated"] = datetime.now().isoformat()

            # 备份现有文件
            if self.session_mappings_file.exists():
                backup_file = self.session_mappings_file.with_suffix(".json.backup")
                backup_file.write_text(self.session_mappings_file.read_text(encoding="utf-8"), encoding="utf-8")

            # 保存新映射
            with open(self.session_mappings_file, "w", encoding="utf-8") as f:
                json.dump(self.mappings, f, indent=2, ensure_ascii=False)

            self.logger.debug("Session mappings saved successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error saving session mappings: {e}")
            return False

    def generate_dual_uuids(self, platform: str) -> Dict[str, str]:
        """生成双UUID映射

        Args:
            platform: 平台名称

        Returns:
            包含标准UUID和前缀UUID的字典
        """
        try:
            # 生成标准UUID
            standard_uuid = str(uuid.uuid4())

            # 获取平台前缀
            prefix = self.platform_prefixes.get(platform.lower(), "xx")

            # 生成前缀UUID (按照原始gaccode.com规则：直接替换标准UUID的前2个字符为平台数字序号)
            prefix_uuid = f"{prefix}{standard_uuid[2:]}"

            # 创建映射关系
            self.mappings["mappings"][prefix_uuid] = {
                "standard_uuid": standard_uuid,
                "platform": platform,
                "created_at": datetime.now().isoformat(),
                "prefix": prefix
            }

            self.mappings["reverse_mappings"][standard_uuid] = {
                "prefix_uuid": prefix_uuid,
                "platform": platform,
                "created_at": datetime.now().isoformat(),
                "prefix": prefix
            }

            # 更新平台会话列表
            if platform not in self.mappings["platform_sessions"]:
                self.mappings["platform_sessions"][platform] = []

            session_info = {
                "standard_uuid": standard_uuid,
                "prefix_uuid": prefix_uuid,
                "created_at": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat()
            }

            self.mappings["platform_sessions"][platform].append(session_info)

            # 保存映射
            self._save_mappings()

            self.logger.info(f"Generated dual UUIDs for {platform}: {prefix_uuid} <-> {standard_uuid}")

            return {
                "standard_uuid": standard_uuid,
                "prefix_uuid": prefix_uuid,
                "session_id": prefix_uuid  # 兼容性：返回前缀UUID作为会话ID
            }

        except Exception as e:
            self.logger.error(f"Error generating dual UUIDs: {e}")
            # 降级到简单UUID生成
            fallback_uuid = str(uuid.uuid4())
            return {
                "standard_uuid": fallback_uuid,
                "prefix_uuid": fallback_uuid,
                "session_id": fallback_uuid
            }

    def get_platform_from_session(self, session_id: str) -> Optional[str]:
        """从会话ID获取平台信息

        Args:
            session_id: 会话ID（可以是标准UUID或前缀UUID）

        Returns:
            平台名称，如果未找到则返回None
        """
        try:
            # 首先尝试前缀UUID查找
            if session_id in self.mappings["mappings"]:
                return self.mappings["mappings"][session_id]["platform"]

            # 然后尝试标准UUID查找
            if session_id in self.mappings["reverse_mappings"]:
                return self.mappings["reverse_mappings"][session_id]["platform"]

            # 尝试从平台前缀检测
            prefix = session_id.split("-")[0] if "-" in session_id else session_id[:2]
            for platform_key, platform_prefix in self.platform_prefixes.items():
                if prefix == platform_prefix:
                    return platform_key

            return None

        except Exception as e:
            self.logger.error(f"Error getting platform from session: {e}")
            return None

    def get_standard_uuid(self, session_id: str) -> Optional[str]:
        """从前缀UUID获取标准UUID

        Args:
            session_id: 会话ID

        Returns:
            标准UUID，如果未找到则返回None
        """
        try:
            # 如果是前缀UUID，返回对应的标准UUID
            if session_id in self.mappings["mappings"]:
                return self.mappings["mappings"][session_id]["standard_uuid"]

            # 如果已经是标准UUID，直接返回
            if session_id in self.mappings["reverse_mappings"]:
                return session_id

            return None

        except Exception as e:
            self.logger.error(f"Error getting standard UUID: {e}")
            return None

    def get_prefix_uuid(self, standard_uuid: str) -> Optional[str]:
        """从标准UUID获取前缀UUID

        Args:
            standard_uuid: 标准UUID

        Returns:
            前缀UUID，如果未找到则返回None
        """
        try:
            if standard_uuid in self.mappings["reverse_mappings"]:
                return self.mappings["reverse_mappings"][standard_uuid]["prefix_uuid"]

            return None

        except Exception as e:
            self.logger.error(f"Error getting prefix UUID: {e}")
            return None

    def update_session_activity(self, session_id: str) -> bool:
        """更新会话活动时间

        Args:
            session_id: 会话ID

        Returns:
            是否更新成功
        """
        try:
            platform = self.get_platform_from_session(session_id)
            if not platform:
                return False

            standard_uuid = self.get_standard_uuid(session_id)
            if not standard_uuid:
                return False

            # 更新映射中的活动时间
            if session_id in self.mappings["mappings"]:
                self.mappings["mappings"][session_id]["last_active"] = datetime.now().isoformat()

            if standard_uuid in self.mappings["reverse_mappings"]:
                self.mappings["reverse_mappings"][standard_uuid]["last_active"] = datetime.now().isoformat()

            # 更新平台会话列表中的活动时间
            if platform in self.mappings["platform_sessions"]:
                for session_info in self.mappings["platform_sessions"][platform]:
                    if session_info["standard_uuid"] == standard_uuid:
                        session_info["last_active"] = datetime.now().isoformat()
                        break

            # 保存映射
            return self._save_mappings()

        except Exception as e:
            self.logger.error(f"Error updating session activity: {e}")
            return False

    def get_platform_sessions(self, platform: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取指定平台的会话列表

        Args:
            platform: 平台名称
            limit: 返回的会话数量限制

        Returns:
            会话信息列表
        """
        try:
            if platform not in self.mappings["platform_sessions"]:
                return []

            # 按最后活动时间排序
            sessions = sorted(
                self.mappings["platform_sessions"][platform],
                key=lambda x: x.get("last_active", x.get("created_at", "")),
                reverse=True
            )

            return sessions[:limit]

        except Exception as e:
            self.logger.error(f"Error getting platform sessions: {e}")
            return []

    def get_recent_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取最近的会话列表

        Args:
            limit: 返回的会话数量限制

        Returns:
            会话信息列表
        """
        try:
            all_sessions = []

            for platform, sessions in self.mappings["platform_sessions"].items():
                for session_info in sessions:
                    session_info["platform"] = platform
                    all_sessions.append(session_info)

            # 按最后活动时间排序
            all_sessions.sort(
                key=lambda x: x.get("last_active", x.get("created_at", "")),
                reverse=True
            )

            return all_sessions[:limit]

        except Exception as e:
            self.logger.error(f"Error getting recent sessions: {e}")
            return []

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """清理旧的会话记录

        Args:
            days: 保留天数

        Returns:
            清理的会话数量
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            cutoff_str = cutoff_time.isoformat()

            cleaned_count = 0

            # 清理各个平台的会话列表
            for platform in list(self.mappings["platform_sessions"].keys()):
                original_count = len(self.mappings["platform_sessions"][platform])

                # 过滤出需要保留的会话
                self.mappings["platform_sessions"][platform] = [
                    session for session in self.mappings["platform_sessions"][platform]
                    if session.get("last_active", session.get("created_at", "")) >= cutoff_str
                ]

                cleaned_count += original_count - len(self.mappings["platform_sessions"][platform])

                # 如果平台没有会话了，删除该平台条目
                if not self.mappings["platform_sessions"][platform]:
                    del self.mappings["platform_sessions"][platform]

            # 清理映射表中对应的条目
            mappings_to_remove = []
            for session_id, mapping in self.mappings["mappings"].items():
                if mapping.get("last_active", mapping.get("created_at", "")) < cutoff_str:
                    standard_uuid = mapping.get("standard_uuid")
                    mappings_to_remove.append(session_id)

                    # 从反向映射中删除
                    if standard_uuid and standard_uuid in self.mappings["reverse_mappings"]:
                        del self.mappings["reverse_mappings"][standard_uuid]

            # 删除映射
            for session_id in mappings_to_remove:
                del self.mappings["mappings"][session_id]

            # 保存更新后的映射
            if cleaned_count > 0:
                self._save_mappings()
                self.logger.info(f"Cleaned up {cleaned_count} old sessions")

            return cleaned_count

        except Exception as e:
            self.logger.error(f"Error cleaning up old sessions: {e}")
            return 0

    def get_statistics(self) -> Dict[str, Any]:
        """获取会话统计信息

        Returns:
            统计信息字典
        """
        try:
            total_sessions = len(self.mappings["mappings"])
            platform_stats = {}

            for platform, sessions in self.mappings["platform_sessions"].items():
                platform_stats[platform] = {
                    "total_sessions": len(sessions),
                    "active_sessions_24h": 0,
                    "active_sessions_7d": 0
                }

                now = datetime.now()
                for session in sessions:
                    last_active = datetime.fromisoformat(
                        session.get("last_active", session.get("created_at", ""))
                    )

                    if now - last_active <= timedelta(hours=24):
                        platform_stats[platform]["active_sessions_24h"] += 1

                    if now - last_active <= timedelta(days=7):
                        platform_stats[platform]["active_sessions_7d"] += 1

            return {
                "total_sessions": total_sessions,
                "platform_stats": platform_stats,
                "platforms": list(self.mappings["platform_sessions"].keys()),
                "created_at": self.mappings.get("created_at"),
                "last_updated": self.mappings.get("last_updated"),
                "version": self.mappings.get("version", "2.0")
            }

        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {}


# 全局实例
_session_mapper = None


def get_session_mapper() -> SessionMapper:
    """获取全局会话映射器实例"""
    global _session_mapper
    if _session_mapper is None:
        _session_mapper = SessionMapper()
    return _session_mapper