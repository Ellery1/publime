"""
主题系统单元测试

测试主题数据类、主题管理器和预定义主题的功能。
"""

import pytest
from themes import Theme, ThemeManager, get_dark_theme, get_light_theme


class TestTheme:
    """测试 Theme 数据类"""
    
    def test_theme_creation(self):
        """测试主题对象创建"""
        theme = Theme(
            name="Test",
            background="#000000",
            foreground="#FFFFFF",
            selection_bg="#333333",
            selection_fg="#FFFFFF",
            line_number_bg="#111111",
            line_number_fg="#888888",
            current_line_bg="#222222",
            cursor_color="#FFFFFF",
            keyword_color="#0000FF",
            string_color="#FF0000",
            comment_color="#00FF00",
            function_color="#FFFF00",
            number_color="#FF00FF",
            operator_color="#00FFFF",
            class_color="#FFA500",
        )
        
        assert theme.name == "Test"
        assert theme.background == "#000000"
        assert theme.foreground == "#FFFFFF"
        assert theme.keyword_color == "#0000FF"
    
    def test_theme_attributes(self):
        """测试主题对象的所有属性"""
        theme = get_dark_theme()
        
        # 验证所有必需属性存在
        assert hasattr(theme, 'name')
        assert hasattr(theme, 'background')
        assert hasattr(theme, 'foreground')
        assert hasattr(theme, 'selection_bg')
        assert hasattr(theme, 'selection_fg')
        assert hasattr(theme, 'line_number_bg')
        assert hasattr(theme, 'line_number_fg')
        assert hasattr(theme, 'current_line_bg')
        assert hasattr(theme, 'cursor_color')
        assert hasattr(theme, 'keyword_color')
        assert hasattr(theme, 'string_color')
        assert hasattr(theme, 'comment_color')
        assert hasattr(theme, 'function_color')
        assert hasattr(theme, 'number_color')
        assert hasattr(theme, 'operator_color')
        assert hasattr(theme, 'class_color')


class TestDarkTheme:
    """测试深色主题"""
    
    def test_dark_theme_creation(self):
        """测试深色主题创建"""
        theme = get_dark_theme()
        assert theme is not None
        assert isinstance(theme, Theme)
    
    def test_dark_theme_name(self):
        """测试深色主题名称"""
        theme = get_dark_theme()
        assert theme.name == "Dark"
    
    def test_dark_theme_colors(self):
        """测试深色主题颜色值正确性"""
        theme = get_dark_theme()
        
        # 验证背景色是深色
        assert theme.background.startswith("#")
        assert len(theme.background) == 7  # #RRGGBB 格式
        
        # 验证前景色是浅色
        assert theme.foreground.startswith("#")
        
        # 验证所有颜色都是有效的十六进制格式
        colors = [
            theme.background, theme.foreground, theme.selection_bg,
            theme.selection_fg, theme.line_number_bg, theme.line_number_fg,
            theme.current_line_bg, theme.cursor_color, theme.keyword_color,
            theme.string_color, theme.comment_color, theme.function_color,
            theme.number_color, theme.operator_color, theme.class_color
        ]
        
        for color in colors:
            assert color.startswith("#")
            assert len(color) == 7
            # 验证是有效的十六进制
            int(color[1:], 16)


class TestLightTheme:
    """测试浅色主题"""
    
    def test_light_theme_creation(self):
        """测试浅色主题创建"""
        theme = get_light_theme()
        assert theme is not None
        assert isinstance(theme, Theme)
    
    def test_light_theme_name(self):
        """测试浅色主题名称"""
        theme = get_light_theme()
        assert theme.name == "Light"
    
    def test_light_theme_colors(self):
        """测试浅色主题颜色值正确性"""
        theme = get_light_theme()
        
        # 验证背景色是浅色
        assert theme.background.startswith("#")
        assert len(theme.background) == 7  # #RRGGBB 格式
        
        # 验证前景色是深色
        assert theme.foreground.startswith("#")
        
        # 验证所有颜色都是有效的十六进制格式
        colors = [
            theme.background, theme.foreground, theme.selection_bg,
            theme.selection_fg, theme.line_number_bg, theme.line_number_fg,
            theme.current_line_bg, theme.cursor_color, theme.keyword_color,
            theme.string_color, theme.comment_color, theme.function_color,
            theme.number_color, theme.operator_color, theme.class_color
        ]
        
        for color in colors:
            assert color.startswith("#")
            assert len(color) == 7
            # 验证是有效的十六进制
            int(color[1:], 16)


class TestThemeManager:
    """测试主题管理器"""
    
    def test_theme_manager_creation(self):
        """测试主题管理器创建"""
        manager = ThemeManager()
        assert manager is not None
    
    def test_default_theme(self):
        """测试默认主题是深色主题"""
        manager = ThemeManager()
        current = manager.get_current_theme()
        assert current is not None
        assert current.name == "Dark"
    
    def test_get_theme(self):
        """测试获取指定主题"""
        manager = ThemeManager()
        
        dark = manager.get_theme("Dark")
        assert dark is not None
        assert dark.name == "Dark"
        
        light = manager.get_theme("Light")
        assert light is not None
        assert light.name == "Light"
    
    def test_get_nonexistent_theme(self):
        """测试获取不存在的主题"""
        manager = ThemeManager()
        theme = manager.get_theme("NonExistent")
        assert theme is None
    
    def test_set_current_theme(self):
        """测试设置当前主题"""
        manager = ThemeManager()
        
        # 切换到浅色主题
        result = manager.set_current_theme("Light")
        assert result is True
        assert manager.get_current_theme().name == "Light"
        
        # 切换回深色主题
        result = manager.set_current_theme("Dark")
        assert result is True
        assert manager.get_current_theme().name == "Dark"
    
    def test_set_nonexistent_theme(self):
        """测试设置不存在的主题"""
        manager = ThemeManager()
        original = manager.get_current_theme()
        
        result = manager.set_current_theme("NonExistent")
        assert result is False
        # 当前主题应该保持不变
        assert manager.get_current_theme() == original
    
    def test_get_available_themes(self):
        """测试获取可用主题列表"""
        manager = ThemeManager()
        themes = manager.get_available_themes()
        
        assert isinstance(themes, list)
        assert len(themes) == 2
        assert "Dark" in themes
        assert "Light" in themes
    
    def test_theme_switching(self):
        """测试主题切换功能"""
        manager = ThemeManager()
        
        # 初始是深色主题
        assert manager.get_current_theme().name == "Dark"
        
        # 切换到浅色
        manager.set_current_theme("Light")
        assert manager.get_current_theme().name == "Light"
        
        # 再切换回深色
        manager.set_current_theme("Dark")
        assert manager.get_current_theme().name == "Dark"
    
    def test_apply_theme_interface(self):
        """测试应用主题接口存在"""
        manager = ThemeManager()
        
        # 验证 apply_theme 方法存在
        assert hasattr(manager, 'apply_theme')
        assert callable(manager.apply_theme)


class TestThemeIntegration:
    """测试主题系统集成"""
    
    def test_dark_and_light_themes_different(self):
        """测试深色和浅色主题的颜色不同"""
        dark = get_dark_theme()
        light = get_light_theme()
        
        # 背景色应该不同
        assert dark.background != light.background
        # 前景色应该不同
        assert dark.foreground != light.foreground
    
    def test_theme_manager_provides_correct_themes(self):
        """测试主题管理器提供的主题与直接获取的主题一致"""
        manager = ThemeManager()
        
        dark_from_manager = manager.get_theme("Dark")
        dark_direct = get_dark_theme()
        
        # 验证主题属性相同
        assert dark_from_manager.name == dark_direct.name
        assert dark_from_manager.background == dark_direct.background
        assert dark_from_manager.foreground == dark_direct.foreground
        
        light_from_manager = manager.get_theme("Light")
        light_direct = get_light_theme()
        
        assert light_from_manager.name == light_direct.name
        assert light_from_manager.background == light_direct.background
        assert light_from_manager.foreground == light_direct.foreground
