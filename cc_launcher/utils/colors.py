#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Color utilities for terminal output
"""

import os
import sys
from typing import Optional


class Colors:
    """ANSI颜色代码"""

    # 基础颜色
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"

    # 明亮颜色
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # 样式
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"

    @staticmethod
    def is_supported() -> bool:
        """检查终端是否支持ANSI颜色"""
        # Windows 10+ 支持ANSI颜色
        if os.name == 'nt':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                # 启用虚拟终端处理
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                return True
            except:
                return False
        else:
            # Unix系统通常都支持
            return sys.stdout.isatty()


class ColorPrinter:
    """彩色输出打印器"""

    def __init__(self, enabled: Optional[bool] = None):
        """
        初始化彩色打印器

        Args:
            enabled: 是否启用彩色输出，None表示自动检测
        """
        if enabled is None:
            self.enabled = Colors.is_supported()
        else:
            self.enabled = enabled

    def colorize(self, text: str, color: str, bold: bool = False) -> str:
        """
        为文本添加颜色

        Args:
            text: 要着色的文本
            color: 颜色代码
            bold: 是否加粗

        Returns:
            着色后的文本
        """
        if not self.enabled:
            return text

        result = color
        if bold:
            result += Colors.BOLD
        result += text + Colors.RESET
        return result

    def print(self, text: str, color: str = "", bold: bool = False, end: str = "\n"):
        """
        打印彩色文本

        Args:
            text: 要打印的文本
            color: 颜色代码
            bold: 是否加粗
            end: 行结束符
        """
        colored_text = self.colorize(text, color, bold)
        print(colored_text, end=end)

    def success(self, text: str, bold: bool = False):
        """打印成功消息（绿色）"""
        self.print(text, Colors.GREEN, bold)

    def error(self, text: str, bold: bool = True):
        """打印错误消息（红色）"""
        self.print(text, Colors.RED, bold)

    def warning(self, text: str, bold: bool = False):
        """打印警告消息（黄色）"""
        self.print(text, Colors.YELLOW, bold)

    def info(self, text: str, bold: bool = False):
        """打印信息消息（青色）"""
        self.print(text, Colors.CYAN, bold)

    def debug(self, text: str, bold: bool = False):
        """打印调试消息（灰色）"""
        self.print(text, Colors.GRAY, bold)

    def header(self, text: str):
        """打印标题（洋红色加粗）"""
        self.print(text, Colors.MAGENTA, bold=True)

    def highlight(self, text: str):
        """打印高亮文本（蓝色）"""
        self.print(text, Colors.BLUE, bold=False)