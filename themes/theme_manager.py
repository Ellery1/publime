"""
主题管理器

该模块负责管理编辑器主题，包括主题的加载、切换和应用。
"""

from typing import List, Optional
from themes.theme import Theme
from themes.dark_theme import get_dark_theme
from themes.light_theme import get_light_theme


class ThemeManager:
    """
    主题管理器类
    
    负责管理编辑器的主题系统，提供主题的加载、切换和应用功能。
    """
    
    def __init__(self):
        """初始化主题管理器"""
        self._current_theme_name: str = "Dark"  # 只存储主题名称，不缓存主题对象
    
    def get_theme(self, name: str) -> Optional[Theme]:
        """
        获取指定名称的主题（每次都重新加载）
        
        Args:
            name: 主题名称（"Dark" 或 "Light"）
            
        Returns:
            Theme: 主题对象，如果主题不存在则返回 None
        """
        if name == "Dark":
            return get_dark_theme()
        elif name == "Light":
            return get_light_theme()
        return None
    
    def get_current_theme(self) -> Theme:
        """
        获取当前主题（每次都重新加载）
        
        Returns:
            Theme: 当前主题对象
        """
        return self.get_theme(self._current_theme_name)
    
    def set_current_theme(self, name: str) -> bool:
        """
        设置当前主题
        
        Args:
            name: 主题名称
            
        Returns:
            bool: 设置成功返回 True，主题不存在返回 False
        """
        if name in ["Dark", "Light"]:
            self._current_theme_name = name
            return True
        return False
    
    def get_available_themes(self) -> List[str]:
        """
        获取所有可用主题的名称列表
        
        Returns:
            List[str]: 主题名称列表
        """
        return ["Dark", "Light"]
    
    def apply_theme(self, theme: Theme, window) -> None:
        """
        应用主题到主窗口
        
        该方法将主题应用到主窗口及其所有子组件，包括：
        - 编辑器窗格的背景色、前景色
        - 行号区域的颜色
        - 选中文本的颜色
        - 语法高亮器的颜色
        
        Args:
            theme: 要应用的主题对象
            window: 主窗口对象（MainWindow 实例）
        """
        # 应用主题到窗口
        # 注意：具体的应用逻辑将在 MainWindow 中实现
        # 这里只是提供接口，实际应用需要遍历所有编辑器窗格并更新样式
        if hasattr(window, 'apply_theme_to_all_editors'):
            window.apply_theme_to_all_editors(theme)
