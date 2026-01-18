"""
语法高亮器单元测试

测试 SyntaxHighlighter 和 LanguageRules 类的功能。
"""

import pytest
from PySide6.QtGui import QTextDocument
from core.syntax_highlighter import SyntaxHighlighter, LanguageRules, HighlightRule
from themes.dark_theme import get_dark_theme
from themes.light_theme import get_light_theme


class TestLanguageRules:
    """测试 LanguageRules 类"""
    
    def test_get_python_rules(self):
        """测试获取 Python 语法规则"""
        rules = LanguageRules.get_rules("python")
        assert len(rules) > 0
        assert any(rule.format_type == 'keyword' for rule in rules)
        assert any(rule.format_type == 'string' for rule in rules)
        assert any(rule.format_type == 'comment' for rule in rules)
    
    def test_get_java_rules(self):
        """测试获取 Java 语法规则"""
        rules = LanguageRules.get_rules("java")
        assert len(rules) > 0
        assert any(rule.format_type == 'keyword' for rule in rules)
        assert any(rule.format_type == 'string' for rule in rules)
        assert any(rule.format_type == 'comment' for rule in rules)
    
    def test_get_sql_rules(self):
        """测试获取 SQL 语法规则"""
        rules = LanguageRules.get_rules("sql")
        assert len(rules) > 0
        assert any(rule.format_type == 'keyword' for rule in rules)
        assert any(rule.format_type == 'string' for rule in rules)
        assert any(rule.format_type == 'comment' for rule in rules)
    
    def test_get_json_rules(self):
        """测试获取 JSON 语法规则"""
        rules = LanguageRules.get_rules("json")
        assert len(rules) > 0
        assert any(rule.format_type == 'keyword' for rule in rules)
        assert any(rule.format_type == 'string' for rule in rules)
        assert any(rule.format_type == 'number' for rule in rules)
    
    def test_get_javascript_rules(self):
        """测试获取 JavaScript 语法规则"""
        rules = LanguageRules.get_rules("javascript")
        assert len(rules) > 0
        assert any(rule.format_type == 'keyword' for rule in rules)
        assert any(rule.format_type == 'string' for rule in rules)
        assert any(rule.format_type == 'comment' for rule in rules)
    
    def test_get_kotlin_rules(self):
        """测试获取 Kotlin 语法规则"""
        rules = LanguageRules.get_rules("kotlin")
        assert len(rules) > 0
        assert any(rule.format_type == 'keyword' for rule in rules)
        assert any(rule.format_type == 'string' for rule in rules)
        assert any(rule.format_type == 'comment' for rule in rules)
    
    def test_unsupported_language(self):
        """测试不支持的语言返回空列表"""
        rules = LanguageRules.get_rules("unsupported")
        assert len(rules) == 0
    
    def test_case_insensitive_language_name(self):
        """测试语言名称不区分大小写"""
        rules_lower = LanguageRules.get_rules("python")
        rules_upper = LanguageRules.get_rules("PYTHON")
        rules_mixed = LanguageRules.get_rules("Python")
        
        assert len(rules_lower) == len(rules_upper) == len(rules_mixed)


class TestHighlightRule:
    """测试 HighlightRule 类"""
    
    def test_create_rule(self):
        """测试创建高亮规则"""
        rule = HighlightRule(r'\bdef\b', 'keyword')
        assert rule.format_type == 'keyword'
        assert rule.pattern.pattern() == r'\bdef\b'


class TestSyntaxHighlighter:
    """测试 SyntaxHighlighter 类"""
    
    def test_init_without_language(self):
        """测试不指定语言初始化"""
        doc = QTextDocument()
        highlighter = SyntaxHighlighter(doc)
        assert highlighter.language == ""
        assert len(highlighter.rules) == 0
    
    def test_init_with_language(self):
        """测试指定语言初始化"""
        doc = QTextDocument()
        highlighter = SyntaxHighlighter(doc, "python")
        assert highlighter.language == "python"
        assert len(highlighter.rules) > 0
    
    def test_set_language(self):
        """测试设置语言"""
        doc = QTextDocument()
        highlighter = SyntaxHighlighter(doc)
        
        highlighter.set_language("python")
        assert highlighter.language == "python"
        assert len(highlighter.rules) > 0
        
        highlighter.set_language("java")
        assert highlighter.language == "java"
        assert len(highlighter.rules) > 0
    
    def test_apply_theme(self):
        """测试应用主题"""
        doc = QTextDocument()
        highlighter = SyntaxHighlighter(doc, "python")
        
        # 应用深色主题
        dark_theme = get_dark_theme()
        highlighter.apply_theme(dark_theme)
        assert 'keyword' in highlighter.formats
        assert 'string' in highlighter.formats
        assert 'comment' in highlighter.formats
        
        # 应用浅色主题
        light_theme = get_light_theme()
        highlighter.apply_theme(light_theme)
        assert 'keyword' in highlighter.formats
        assert 'string' in highlighter.formats
        assert 'comment' in highlighter.formats
    
    def test_formats_initialized(self):
        """测试格式已初始化"""
        doc = QTextDocument()
        highlighter = SyntaxHighlighter(doc, "python")
        
        # 检查所有格式类型都已初始化
        expected_formats = ['keyword', 'string', 'comment', 'function', 'number', 'operator', 'class']
        for format_type in expected_formats:
            assert format_type in highlighter.formats
    
    def test_highlight_python_keywords(self):
        """测试 Python 关键字高亮"""
        doc = QTextDocument()
        doc.setPlainText("def test():\n    return True")
        highlighter = SyntaxHighlighter(doc, "python")
        
        # 验证高亮器已设置
        assert highlighter.document() == doc
        assert highlighter.language == "python"
    
    def test_highlight_java_keywords(self):
        """测试 Java 关键字高亮"""
        doc = QTextDocument()
        doc.setPlainText("public class Test {\n    public static void main(String[] args) {}\n}")
        highlighter = SyntaxHighlighter(doc, "java")
        
        assert highlighter.document() == doc
        assert highlighter.language == "java"
    
    def test_highlight_sql_keywords(self):
        """测试 SQL 关键字高亮"""
        doc = QTextDocument()
        doc.setPlainText("SELECT * FROM users WHERE id = 1")
        highlighter = SyntaxHighlighter(doc, "sql")
        
        assert highlighter.document() == doc
        assert highlighter.language == "sql"
    
    def test_highlight_json(self):
        """测试 JSON 高亮"""
        doc = QTextDocument()
        doc.setPlainText('{"name": "test", "value": 123, "active": true}')
        highlighter = SyntaxHighlighter(doc, "json")
        
        assert highlighter.document() == doc
        assert highlighter.language == "json"
    
    def test_highlight_javascript_keywords(self):
        """测试 JavaScript 关键字高亮"""
        doc = QTextDocument()
        doc.setPlainText("function test() {\n    const x = 10;\n    return x;\n}")
        highlighter = SyntaxHighlighter(doc, "javascript")
        
        assert highlighter.document() == doc
        assert highlighter.language == "javascript"
    
    def test_highlight_kotlin_keywords(self):
        """测试 Kotlin 关键字高亮"""
        doc = QTextDocument()
        doc.setPlainText("fun main() {\n    val x = 10\n    println(x)\n}")
        highlighter = SyntaxHighlighter(doc, "kotlin")
        
        assert highlighter.document() == doc
        assert highlighter.language == "kotlin"
    
    def test_multiple_language_switches(self):
        """测试多次切换语言"""
        doc = QTextDocument()
        highlighter = SyntaxHighlighter(doc)
        
        languages = ["python", "java", "sql", "json", "javascript", "kotlin"]
        for lang in languages:
            highlighter.set_language(lang)
            assert highlighter.language == lang
            assert len(highlighter.rules) > 0


class TestLanguageSpecificRules:
    """测试特定语言的规则"""
    
    def test_python_decorators(self):
        """测试 Python 装饰器规则"""
        rules = LanguageRules.get_rules("python")
        decorator_rules = [r for r in rules if '@' in r.pattern.pattern()]
        assert len(decorator_rules) > 0
    
    def test_java_annotations(self):
        """测试 Java 注解规则"""
        rules = LanguageRules.get_rules("java")
        annotation_rules = [r for r in rules if '@' in r.pattern.pattern()]
        assert len(annotation_rules) > 0
    
    def test_sql_functions(self):
        """测试 SQL 函数规则"""
        rules = LanguageRules.get_rules("sql")
        function_rules = [r for r in rules if r.format_type == 'function']
        assert len(function_rules) > 0
    
    def test_json_boolean_and_null(self):
        """测试 JSON 布尔值和 null 规则"""
        rules = LanguageRules.get_rules("json")
        # JSON 的 true/false/null 应该被标记为 keyword
        keyword_rules = [r for r in rules if r.format_type == 'keyword']
        assert len(keyword_rules) > 0
    
    def test_javascript_regex(self):
        """测试 JavaScript 正则表达式规则"""
        rules = LanguageRules.get_rules("javascript")
        # 正则表达式应该被标记为 string
        string_rules = [r for r in rules if r.format_type == 'string']
        assert len(string_rules) > 0
    
    def test_kotlin_data_class(self):
        """测试 Kotlin data class 关键字"""
        rules = LanguageRules.get_rules("kotlin")
        keyword_rules = [r for r in rules if r.format_type == 'keyword']
        assert len(keyword_rules) > 0
        # 检查 'data' 关键字是否在规则中
        keyword_pattern = keyword_rules[0].pattern.pattern()
        assert 'data' in keyword_pattern
