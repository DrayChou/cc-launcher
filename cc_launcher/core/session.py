#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Session Manager - 会话管理器
负责创建和管理Claude Code会话
"""

import json
import uuid
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from ..utils.logger import get_logger
from ..utils.file_lock import safe_json_read, safe_json_write
from .session_mapper import get_session_mapper


class SessionManager:
    """会话管理器"""

    # 平台前缀映射
    PLATFORM_PREFIXES = {
        "gaccode": "01",
        "deepseek": "02",
        "kimi": "03",
        "siliconflow": "04",
        "local_proxy": "05",
        "vanchin": "06",
    }

    def __init__(self, config_manager):
        """初始化会话管理器"""
        self.config_manager = config_manager
        self.cache_dir = config_manager.get_cache_dir()
        self.sessions_dir = self.cache_dir / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger("session")

        # 获取增强的会话映射器
        self.session_mapper = get_session_mapper()

        # session映射文件（向后兼容）
        self.session_mappings_file = self.cache_dir / "session-mappings.json"

    def create_or_get_session(self, platform_name: str, continue_session: bool = False) -> Optional[Dict[str, Any]]:
        """
        创建新会话或获取现有会话

        Args:
            platform_name: 平台名称
            continue_session: 是否继续上次的会话

        Returns:
            会话信息字典
        """
        try:
            if continue_session:
                # 尝试继续上次的会话
                last_session = self.get_last_session(platform_name)
                if last_session:
                    self.logger.info(f"Continuing last session for {platform_name}: {last_session['session_id']}")
                    return last_session

            # 创建新会话
            session_info = self._create_new_session(platform_name)
            if session_info:
                self.logger.info(f"Created new session for {platform_name}: {session_info['session_id']}")
            return session_info

        except Exception as e:
            self.logger.error(f"Error creating/getting session for {platform_name}: {e}")
            return None

    def _create_new_session(self, platform_name: str) -> Optional[Dict[str, Any]]:
        """创建新会话"""
        try:
            # 使用增强的会话映射器生成双UUID
            uuid_mapping = self.session_mapper.generate_dual_uuids(platform_name)

            if uuid_mapping:
                # 构建会话信息
                session_info = {
                    "session_id": uuid_mapping["session_id"],  # 使用前缀UUID作为会话ID
                    "standard_uuid": uuid_mapping["standard_uuid"],
                    "prefix_uuid": uuid_mapping["prefix_uuid"],
                    "platform": platform_name,
                    "created_at": datetime.now().isoformat(),
                    "created_timestamp": time.time(),
                    "last_active": time.time()
                }

                # 更新最后使用的会话（向后兼容）
                self._update_last_session(platform_name, session_info)

                self.logger.info(f"Enhanced session created for {platform_name}: {uuid_mapping['prefix_uuid']} <-> {uuid_mapping['standard_uuid']}")
                return session_info
            else:
                # 降级到原始实现
                return self._fallback_create_session(platform_name)

        except Exception as e:
            self.logger.error(f"Error creating new session with enhanced mapper: {e}")
            # 降级到原始实现
            return self._fallback_create_session(platform_name)

    def _fallback_create_session(self, platform_name: str) -> Optional[Dict[str, Any]]:
        """降级会话创建方法"""
        try:
            # 生成标准UUID
            base_uuid = str(uuid.uuid4())

            # 获取平台前缀
            platform_prefix = self.PLATFORM_PREFIXES.get(platform_name, "01")

            # 创建带前缀的UUID
            prefixed_uuid = f"{platform_prefix}{base_uuid[2:]}"

            # 构建会话信息
            session_info = {
                "session_id": prefixed_uuid,
                "standard_uuid": base_uuid,
                "platform": platform_name,
                "created_at": datetime.now().isoformat(),
                "created_timestamp": time.time(),
                "last_active": time.time()
            }

            # 保存会话映射（向后兼容）
            self._save_session_mapping(prefixed_uuid, session_info)
            self._save_session_mapping(base_uuid, session_info)

            # 更新最后使用的会话
            self._update_last_session(platform_name, session_info)

            self.logger.info(f"Fallback session created for {platform_name}: {prefixed_uuid}")
            return session_info

        except Exception as e:
            self.logger.error(f"Error creating fallback session: {e}")
            return None

    def get_last_session(self, platform_name: str) -> Optional[Dict[str, Any]]:
        """获取平台最后使用的会话"""
        try:
            last_session_file = self.sessions_dir / f"last_session_{platform_name}.json"
            session_data = safe_json_read(last_session_file)

            if session_data:
                session_id = session_data.get("session_id")
                if session_id:
                    return self.get_session_info(session_id)

            return None

        except Exception as e:
            self.logger.warning(f"Error getting last session for {platform_name}: {e}")
            return None

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        try:
            # 从session映射文件读取
            mappings = self._load_session_mappings()
            return mappings.get("sessions", {}).get(session_id)

        except Exception as e:
            self.logger.warning(f"Error getting session info for {session_id}: {e}")
            return None

    def _save_session_mapping(self, session_id: str, session_info: Dict[str, Any]) -> bool:
        """保存会话映射"""
        try:
            mappings = self._load_session_mappings()
            mappings["sessions"][session_id] = session_info
            mappings["last_updated"] = datetime.now().isoformat()

            return safe_json_write(self.session_mappings_file, mappings)

        except Exception as e:
            self.logger.error(f"Error saving session mapping: {e}")
            return False

    def _load_session_mappings(self) -> Dict[str, Any]:
        """加载会话映射"""
        try:
            mappings = safe_json_read(self.session_mappings_file)
            if not mappings:
                mappings = {
                    "version": "1.0",
                    "created": datetime.now().isoformat(),
                    "sessions": {}
                }
            return mappings

        except Exception as e:
            self.logger.warning(f"Error loading session mappings: {e}")
            return {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "sessions": {}
            }

    def _update_last_session(self, platform_name: str, session_info: Dict[str, Any]) -> bool:
        """更新最后使用的会话"""
        try:
            last_session_file = self.sessions_dir / f"last_session_{platform_name}.json"
            return safe_json_write(last_session_file, session_info)

        except Exception as e:
            self.logger.error(f"Error updating last session: {e}")
            return False

    def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """清理旧会话"""
        try:
            cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
            mappings = self._load_session_mappings()

            sessions_to_remove = []
            for session_id, session_data in mappings.get("sessions", {}).items():
                created_timestamp = session_data.get("created_timestamp", 0)
                if created_timestamp < cutoff_time:
                    sessions_to_remove.append(session_id)

            # 删除旧会话
            for session_id in sessions_to_remove:
                del mappings["sessions"][session_id]

            if sessions_to_remove:
                mappings["last_cleanup"] = datetime.now().isoformat()
                safe_json_write(self.session_mappings_file, mappings)
                self.logger.info(f"Cleaned up {len(sessions_to_remove)} old sessions")

            return len(sessions_to_remove)

        except Exception as e:
            self.logger.error(f"Error cleaning up old sessions: {e}")
            return 0