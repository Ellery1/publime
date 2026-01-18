"""
代码补全器测试模块

测试代码补全器的关键字补全和上下文补全功能。
"""

import pytest
from PySide6.QtWidgets import QApplication

from ui.editor_pane import EditorPane
from core.code_completer import CodeCompleter


@pytest.fixture
def app(qapp):
    """Qt 应用程序 fixture"""
    return qapp


@pytest.fixture
def editor(app):
    """编辑器窗格 fixture"""
    editor = EditorPane()
    return editor


@pytest.fixture
def completer(editor):
    """代码补全器 fixture"""
    return editor.code_completer


def test_completer_creation(completer):
    """测试补全器创建"""
    assert completer is not None
    assert isinstance(completer, CodeCompleter)


def test_set_language(completer):
    """测试设置语言"""
    completer.set_language("python")
    assert completer.current_language == "python"
    
    completer.set_language("Java")
    assert completer.current_language == "java"


def test_get_python_keyword_completions(completer):
    """测试获取 Python 关键字补全"""
    keywords = completer.get_keyword_completions("python")
    
    # 验证包含常见关键字
    assert "def" in keywords
    assert "class" in keywords
    assert "if" in keywords
    assert "for" in keywords
    assert "while" in keywords
    assert "import" in keywords
    assert "return" in keywords
    
    # 验证包含内置函数
    assert "print" in keywords
    assert "len" in keywords
    assert "range" in keywords


def test_get_java_keyword_completions(completer):
    """测试获取 Java 关键字补全"""
    keywords = completer.get_keyword_completions("java")
    
    # 验证包含常见关键字
    assert "public" in keywords
    assert "private" in keywords
    assert "class" in keywords
    assert "interface" in keywords
    assert "extends" in keywords
    assert "implements" in keywords
    
    # 验证包含常用类
    assert "String" in keywords
    assert "Integer" in keywords


def test_get_javascript_keyword_completions(completer):
    """测试获取 JavaScript 关键字补全"""
    keywords = completer.get_keyword_completions("javascript")
    
    # 验证包含常见关键字
    assert "function" in keywords
    assert "const" in keywords
    assert "let" in keywords
    assert "var" in keywords
    assert "async" in keywords
    assert "await" in keywords
    
    # 验证包含常用对象
    assert "console" in keywords
    assert "Promise" in keywords


def test_get_sql_keyword_completions(completer):
    """测试获取 SQL 关键字补全"""
    keywords = completer.get_keyword_completions("sql")
    
    # 验证包含常见关键字
    assert "SELECT" in keywords
    assert "FROM" in keywords
    assert "WHERE" in keywords
    assert "INSERT" in keywords
    assert "UPDATE" in keywords
    assert "DELETE" in keywords
    assert "CREATE" in keywords
    assert "TABLE" in keywords


def test_get_context_completions_simple(completer):
    """测试获取简单上下文补全"""
    text = """
def my_function():
    my_variable = 10
    my_other_variable = 20
    return my_variable
"""
    
    # 查找以 "my" 开头的标识符
    completions = completer.get_context_completions(text, "my")
    
    # 验证找到了所有标识符
    assert "my_function" in completions
    assert "my_variable" in completions
    assert "my_other_variable" in completions


def test_get_context_completions_case_insensitive(completer):
    """测试上下文补全大小写不敏感"""
    text = """
MyClass = None
myFunction = None
MYCONST = None
"""
    
    # 使用小写前缀查找
    completions = completer.get_context_completions(text, "my")
    
    # 验证找到了所有变体
    assert "MyClass" in completions
    assert "myFunction" in completions
    assert "MYCONST" in completions


def test_get_context_completions_excludes_prefix(completer):
    """测试上下文补全排除前缀本身"""
    text = """
test_value = 10
test_function()
"""
    
    # 查找以 "test_value" 开头的标识符
    completions = completer.get_context_completions(text, "test_value")
    
    # 验证不包含前缀本身
    assert "test_value" not in completions


def test_get_context_completions_min_length(completer):
    """测试上下文补全只提取至少2个字符的标识符"""
    text = """
a = 10
ab = 20
abc = 30
"""
    
    # 查找以 "a" 开头的标识符
    completions = completer.get_context_completions(text, "a")
    
    # 验证只包含至少2个字符的标识符
    assert "a" not in completions
    assert "ab" in completions
    assert "abc" in completions


def test_text_under_cursor(editor, completer):
    """测试获取光标下的文本"""
    # 设置文本
    editor.setPlainText("hello world test")
    
    # 将光标移动到 "world" 中间
    cursor = editor.textCursor()
    cursor.setPosition(8)  # "w" 的位置
    editor.setTextCursor(cursor)
    
    # 获取光标下的文本
    text = completer.text_under_cursor()
    assert text == "world"


def test_keyword_completion_filtering(completer):
    """测试关键字补全过滤"""
    completer.set_language("python")
    
    # 获取所有以 "de" 开头的补全
    all_completions = completer._get_all_completions("de")
    
    # 验证包含 "def" 和 "del"
    assert "def" in all_completions
    assert "del" in all_completions
    
    # 验证不包含不匹配的关键字
    assert "if" not in all_completions
    assert "for" not in all_completions


def test_combined_keyword_and_context_completions(completer, editor):
    """测试关键字和上下文补全的组合"""
    # 设置语言
    completer.set_language("python")
    
    # 设置包含自定义标识符的文本
    editor.setPlainText("""
def my_function():
    define_something = 10
    return define_something
""")
    
    # 获取以 "def" 开头的补全
    completions = completer._get_all_completions("def")
    
    # 验证包含关键字
    assert "def" in completions
    
    # 验证包含上下文标识符
    assert "define_something" in completions


def test_completion_prefix_too_short(completer, editor):
    """测试前缀太短时不显示补全"""
    completer.set_language("python")
    editor.setPlainText("test")
    
    # 尝试用单字符前缀更新补全
    completer.update_completions("t")
    
    # 验证弹窗未显示
    assert not completer.popup().isVisible()


def test_completion_with_valid_prefix(completer, editor):
    """测试有效前缀时显示补全"""
    completer.set_language("python")
    editor.setPlainText("test")
    
    # 用两字符前缀更新补全
    completer.update_completions("de")
    
    # 验证有补全结果
    assert completer.completionCount() > 0


def test_no_completions_for_unknown_language(completer):
    """测试未知语言没有关键字补全"""
    keywords = completer.get_keyword_completions("unknown_language")
    assert keywords == []


def test_context_completions_with_special_characters(completer):
    """测试包含特殊字符的文本的上下文补全"""
    text = """
my_var = 10
my-invalid = 20  # 不是有效标识符
my.invalid = 30  # 不是有效标识符
my_valid_var = 40
"""
    
    completions = completer.get_context_completions(text, "my")
    
    # 验证只包含有效标识符
    assert "my_var" in completions
    assert "my_valid_var" in completions
    # 无效标识符不应该被提取
    assert "my-invalid" not in completions
    assert "my.invalid" not in completions
