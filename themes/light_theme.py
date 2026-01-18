"""
浅色主题定义

该模块定义了编辑器的浅色主题配色方案。
"""

from themes.theme import Theme


def get_light_theme() -> Theme:
    """
    获取浅色主题配置
    
    Returns:
        Theme: 浅色主题对象
    """
    return Theme(
        name="Light",
        background="#FFFFFF",  # 白色背景
        foreground="#000000",  # 黑色文本
        selection_bg="#ADD6FF",  # 浅蓝色选中背景
        selection_fg="#000000",  # 黑色选中文本
        line_number_bg="#F5F5F5",  # 浅灰色行号背景
        line_number_fg="#237893",  # 蓝灰色行号
        current_line_bg="#F0F0F0",  # 浅灰色当前行
        cursor_color="#000000",  # 黑色光标
        
        # 基础语法高亮颜色（类似 VS Code Light+ 主题）
        keyword_color="#0000FF",  # 蓝色关键字
        string_color="#A31515",  # 红色字符串
        comment_color="#008000",  # 绿色注释
        function_color="#795E26",  # 棕色函数名
        number_color="#098658",  # 深绿色数字
        operator_color="#000000",  # 黑色操作符
        class_color="#267F99",  # 蓝绿色类名
        
        # 扩展语法高亮颜色
        variable_color="#001080",  # 深蓝色变量
        type_color="#267F99",  # 蓝绿色类型
        constant_color="#0070C1",  # 亮蓝色常量
        decorator_color="#AF00DB",  # 紫色装饰器
        property_color="#001080",  # 深蓝色属性
        tag_color="#800000",  # 深红色标签
        attribute_color="#FF0000",  # 红色属性
        markdown_heading_color="#0000FF",  # 蓝色标题
        markdown_bold_color="#000000",  # 黑色粗体
        markdown_italic_color="#AF00DB",  # 紫色斜体
        markdown_code_color="#A31515",  # 红色代码
        markdown_link_color="#0000EE",  # 蓝色链接
        markdown_math_color="#AF00DB",  # 紫色数学公式
    )
