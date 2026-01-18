"""
深色主题定义

该模块定义了编辑器的深色主题配色方案。
"""

from themes.theme import Theme


def get_dark_theme() -> Theme:
    """
    获取深色主题配置
    
    Returns:
        Theme: 深色主题对象
    """
    return Theme(
        name="Dark",
        background="#252526",  # 深灰色背景
        foreground="#D4D4D4",  # 浅灰色文本
        selection_bg="#264F78",  # 蓝灰色选中背景
        selection_fg="#FFFFFF",  # 白色选中文本
        line_number_bg="#1E1E1E",  # 更深的灰色
        line_number_fg="#858585",  # 中灰色行号
        current_line_bg="#2A2D2E",  # 稍亮的灰色当前行
        cursor_color="#AEAFAD",  # 浅灰色光标
        
        # 基础语法高亮颜色（Sublime Monokai 风格 - 更鲜艳醒目）
        keyword_color="#F92672",  # 粉红色关键字（public, static, void, new）- 醒目
        string_color="#E6DB74",  # 黄色字符串（"hello", "world"）- 更鲜艳！
        comment_color="#75715E",  # 灰绿色注释
        function_color="#A6E22E",  # 亮绿色函数名（forEach, process, asList）- 更醒目！
        number_color="#AE81FF",  # 紫色数字（1, 2, 3, 4, 5）- 更鲜艳！
        operator_color="#F92672",  # 粉红色操作符（->, +, *, =）- 与关键字一致
        class_color="#66D9EF",  # 亮青色类名（DataProcessor, Arrays, System）- 更鲜艳！
        
        # 扩展语法高亮颜色
        variable_color="#F8F8F2",  # 白色变量（processor, testData, result, item）- 更清晰
        type_color="#66D9EF",  # 亮青色类型（List, String, Integer）
        constant_color="#AE81FF",  # 紫色常量
        decorator_color="#66D9EF",  # 亮青色装饰器
        property_color="#F8F8F2",  # 白色属性
        tag_color="#F92672",  # 粉红色标签（与关键字一致）
        attribute_color="#A6E22E",  # 亮绿色属性
        markdown_heading_color="#F92672",  # 粉红色标题（更醒目）
        markdown_bold_color="#F8F8F2",  # 白色粗体
        markdown_italic_color="#E6DB74",  # 黄色斜体
        markdown_code_color="#E6DB74",  # 黄色代码
        markdown_link_color="#66D9EF",  # 亮青色链接
        markdown_math_color="#E6DB74",  # 橙黄色数学公式（与字符串颜色一致，更鲜艳）
    )
