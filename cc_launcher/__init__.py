#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cc-launcher - Claude Code Multi-Platform Launcher
"""

__version__ = "1.0.0"
__author__ = "Claude Code Community"
__description__ = "Claude Code Multi-Platform Launcher"

from .core.config import ConfigManager
from .core.session import SessionManager
from .core.environment import EnvironmentManager

__all__ = [
    "ConfigManager",
    "SessionManager",
    "EnvironmentManager",
    "__version__",
]