"""
主题系统模块

该模块提供编辑器的主题管理功能，包括主题定义、主题管理器和预定义主题。
"""

from themes.theme import Theme
from themes.theme_manager import ThemeManager
from themes.dark_theme import get_dark_theme
from themes.light_theme import get_light_theme

__all__ = [
    'Theme',
    'ThemeManager',
    'get_dark_theme',
    'get_light_theme',
]
