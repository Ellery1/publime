"""
主题数据类定义

该模块定义了编辑器主题的数据结构，包含所有界面元素和语法高亮的颜色配置。
"""

from dataclasses import dataclass


@dataclass
class Theme:
    """
    主题定义数据类
    
    包含编辑器所有界面元素和语法高亮的颜色配置。
    颜色值使用十六进制格式（如 "#RRGGBB"）。
    """
    name: str  # 主题名称
    background: str  # 编辑器背景色
    foreground: str  # 编辑器前景色（文本颜色）
    selection_bg: str  # 选中文本背景色
    selection_fg: str  # 选中文本前景色
    line_number_bg: str  # 行号区域背景色
    line_number_fg: str  # 行号前景色
    current_line_bg: str  # 当前行背景色
    cursor_color: str  # 光标颜色
    
    # 语法高亮颜色
    keyword_color: str  # 关键字颜色
    string_color: str  # 字符串颜色
    comment_color: str  # 注释颜色
    function_color: str  # 函数名颜色
    number_color: str  # 数字颜色
    operator_color: str  # 操作符颜色
    class_color: str  # 类名颜色
    
    # 扩展语法高亮颜色
    variable_color: str = None  # 变量颜色
    type_color: str = None  # 类型颜色
    constant_color: str = None  # 常量颜色
    decorator_color: str = None  # 装饰器颜色
    property_color: str = None  # 属性颜色
    tag_color: str = None  # 标签颜色（HTML/XML）
    attribute_color: str = None  # 属性颜色（HTML/XML）
    markdown_heading_color: str = None  # Markdown标题颜色
    markdown_bold_color: str = None  # Markdown粗体颜色
    markdown_italic_color: str = None  # Markdown斜体颜色
    markdown_code_color: str = None  # Markdown代码颜色
    markdown_link_color: str = None  # Markdown链接颜色
    markdown_math_color: str = None  # Markdown数学公式颜色
