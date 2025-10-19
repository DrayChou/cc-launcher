#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cc-launcher detector modules
"""

from .claude import ClaudeDetector
from .platform import PlatformDetector

__all__ = [
    "ClaudeDetector",
    "PlatformDetector",
]