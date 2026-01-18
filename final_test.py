#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""最终测试 - 使用实际的main_window格式化方法"""

import sys
from PySide6.QtWidgets import QApplication
app = QApplication(sys.argv)

from ui.main_window import MainWindow
from ui.editor_pane import EditorPane

# 创建主窗口
window = MainWindow()

# 读取测试文件
with open('samples/complex_test.sql', 'r', encoding='utf-8') as f:
    content = f.read()

# 创建编辑器并设置内容
editor = EditorPane()
editor.setPlainText(content)
editor.set_language('sql')
editor.set_file_path('test.sql')  # 设置文件路径以便语言检测

# 添加到标签页
window.tab_widget.addTab(editor, 'test.sql')
window.tab_widget.setCurrentIndex(0)

# 执行格式化
try:
    print("开始格式化...")
    window.format_sql()
    print("格式化完成")
    
    # 获取格式化后的内容
    formatted = editor.toPlainText()
    
    print(f"格式化后长度: {len(formatted)}")
    print(f"原始长度: {len(content)}")
    
    # 保存到文件
    with open('final_formatted.sql', 'w', encoding='utf-8') as f:
        f.write(formatted)
    
    print("格式化成功！结果已保存到 final_formatted.sql")
    
except Exception as e:
    print(f"格式化失败: {str(e)}")
    import traceback
    traceback.print_exc()
