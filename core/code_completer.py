"""
代码补全器模块

该模块实现了基于上下文的代码补全功能，提供语言关键字和文件内标识符的补全建议。
"""

import re
from typing import List, Set
from PySide6.QtWidgets import QCompleter
from PySide6.QtCore import Qt, QStringListModel


class CodeCompleter(QCompleter):
    """
    代码补全器类
    
    提供基于语言关键字和文件内容的代码补全建议。
    """
    
    # 各语言的关键字
    LANGUAGE_KEYWORDS = {
        "python": [
            "False", "None", "True", "and", "as", "assert", "async", "await",
            "break", "class", "continue", "def", "del", "elif", "else", "except",
            "finally", "for", "from", "global", "if", "import", "in", "is",
            "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
            "try", "while", "with", "yield",
            # 内置函数
            "abs", "all", "any", "bin", "bool", "bytes", "chr", "dict", "dir",
            "enumerate", "filter", "float", "format", "frozenset", "getattr",
            "hasattr", "hash", "help", "hex", "id", "input", "int", "isinstance",
            "issubclass", "iter", "len", "list", "map", "max", "min", "next",
            "object", "oct", "open", "ord", "pow", "print", "range", "repr",
            "reversed", "round", "set", "setattr", "slice", "sorted", "str",
            "sum", "super", "tuple", "type", "vars", "zip",
            # 常用模块
            "self", "cls", "__init__", "__str__", "__repr__",
        ],
        "java": [
            "abstract", "assert", "boolean", "break", "byte", "case", "catch",
            "char", "class", "const", "continue", "default", "do", "double",
            "else", "enum", "extends", "final", "finally", "float", "for",
            "goto", "if", "implements", "import", "instanceof", "int", "interface",
            "long", "native", "new", "package", "private", "protected", "public",
            "return", "short", "static", "strictfp", "super", "switch", "synchronized",
            "this", "throw", "throws", "transient", "try", "void", "volatile", "while",
            # 常用类
            "String", "Integer", "Double", "Boolean", "Character", "Long", "Float",
            "Object", "System", "Math", "ArrayList", "HashMap", "HashSet",
        ],
        "javascript": [
            "abstract", "arguments", "await", "boolean", "break", "byte", "case",
            "catch", "char", "class", "const", "continue", "debugger", "default",
            "delete", "do", "double", "else", "enum", "eval", "export", "extends",
            "false", "final", "finally", "float", "for", "function", "goto", "if",
            "implements", "import", "in", "instanceof", "int", "interface", "let",
            "long", "native", "new", "null", "package", "private", "protected",
            "public", "return", "short", "static", "super", "switch", "synchronized",
            "this", "throw", "throws", "transient", "true", "try", "typeof", "var",
            "void", "volatile", "while", "with", "yield",
            # 常用对象和方法
            "console", "log", "document", "window", "Array", "Object", "String",
            "Number", "Boolean", "Date", "Math", "JSON", "Promise", "async",
        ],
        "kotlin": [
            "abstract", "annotation", "as", "break", "by", "catch", "class",
            "companion", "const", "constructor", "continue", "crossinline", "data",
            "delegate", "do", "dynamic", "else", "enum", "external", "false",
            "field", "file", "final", "finally", "for", "fun", "get", "if",
            "import", "in", "infix", "init", "inline", "inner", "interface",
            "internal", "is", "lateinit", "noinline", "null", "object", "open",
            "operator", "out", "override", "package", "param", "private", "property",
            "protected", "public", "receiver", "reified", "return", "sealed", "set",
            "setparam", "super", "suspend", "tailrec", "this", "throw", "true",
            "try", "typealias", "typeof", "val", "var", "vararg", "when", "where", "while",
            # 常用类型
            "String", "Int", "Long", "Double", "Float", "Boolean", "Char", "Byte",
            "Short", "Any", "Unit", "Nothing", "List", "Map", "Set", "Array",
        ],
        "sql": [
            "SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "DELETE", "CREATE",
            "DROP", "ALTER", "TABLE", "DATABASE", "INDEX", "VIEW", "JOIN",
            "INNER", "LEFT", "RIGHT", "OUTER", "ON", "AS", "AND", "OR", "NOT",
            "IN", "BETWEEN", "LIKE", "IS", "NULL", "ORDER", "BY", "GROUP",
            "HAVING", "LIMIT", "OFFSET", "UNION", "ALL", "DISTINCT", "COUNT",
            "SUM", "AVG", "MAX", "MIN", "PRIMARY", "KEY", "FOREIGN", "REFERENCES",
            "CONSTRAINT", "UNIQUE", "CHECK", "DEFAULT", "AUTO_INCREMENT",
            "VARCHAR", "INT", "INTEGER", "BIGINT", "DECIMAL", "FLOAT", "DOUBLE",
            "DATE", "TIME", "DATETIME", "TIMESTAMP", "TEXT", "BLOB",
        ],
        "json": [
            "true", "false", "null",
        ],
    }
    
    def __init__(self, editor):
        """
        初始化代码补全器
        
        Args:
            editor: 关联的编辑器窗格
        """
        super().__init__(editor)
        
        self.editor = editor
        self.current_language = None
        
        # 设置补全器属性
        self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.setWrapAround(False)
        
        # 创建模型
        self.model = QStringListModel()
        self.setModel(self.model)
        
        # 连接到编辑器
        self.setWidget(editor)
        self.activated.connect(self._insert_completion)
    
    def set_language(self, language: str) -> None:
        """
        设置当前语言
        
        Args:
            language: 语言名称，如果为None则禁用代码补全
        """
        if language is None:
            self.current_language = None
        else:
            self.current_language = language.lower()
    
    def update_completions(self, prefix: str) -> None:
        """
        根据当前前缀更新补全列表
        
        Args:
            prefix: 输入前缀
        """
        if not prefix or len(prefix) < 2:
            # 前缀太短，不显示补全
            self.popup().hide()
            return
        
        # 获取所有补全建议
        completions = self._get_all_completions(prefix)
        
        if not completions:
            self.popup().hide()
            return
        
        # 更新模型
        self.model.setStringList(sorted(completions))
        
        # 设置前缀并显示补全
        self.setCompletionPrefix(prefix)
        
        # 显示补全弹窗
        if self.completionCount() > 0:
            # 计算弹窗位置
            cursor_rect = self.editor.cursorRect()
            cursor_rect.setWidth(
                self.popup().sizeHintForColumn(0) +
                self.popup().verticalScrollBar().sizeHint().width()
            )
            self.complete(cursor_rect)
    
    def _get_all_completions(self, prefix: str) -> List[str]:
        """
        获取所有补全建议
        
        Args:
            prefix: 输入前缀
            
        Returns:
            List[str]: 补全建议列表
        """
        completions = set()
        
        # 添加语言关键字补全
        if self.current_language:
            keyword_completions = self.get_keyword_completions(self.current_language)
            completions.update(
                kw for kw in keyword_completions
                if kw.lower().startswith(prefix.lower())
            )
        
        # 添加上下文补全（文件中的标识符）
        text = self.editor.toPlainText()
        context_completions = self.get_context_completions(text, prefix)
        completions.update(context_completions)
        
        return list(completions)
    
    def get_keyword_completions(self, language: str) -> List[str]:
        """
        获取语言关键字补全
        
        Args:
            language: 语言名称，如果为None则返回空列表
            
        Returns:
            List[str]: 关键字列表
        """
        if language is None:
            return []
        return self.LANGUAGE_KEYWORDS.get(language.lower(), [])
    
    def get_context_completions(self, text: str, prefix: str) -> Set[str]:
        """
        获取上下文补全（文件中已有的标识符）
        
        Args:
            text: 文件文本内容
            prefix: 输入前缀
            
        Returns:
            Set[str]: 标识符集合
        """
        # 使用正则表达式提取标识符
        # 匹配字母、数字、下划线组成的标识符（至少2个字符）
        pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]+\b'
        identifiers = re.findall(pattern, text)
        
        # 过滤出匹配前缀的标识符
        matching = {
            identifier for identifier in identifiers
            if identifier.lower().startswith(prefix.lower()) and identifier != prefix
        }
        
        return matching
    
    def _insert_completion(self, completion: str) -> None:
        """
        插入选中的补全文本
        
        Args:
            completion: 补全文本
        """
        # 获取当前光标
        cursor = self.editor.textCursor()
        
        # 计算需要替换的字符数
        extra = len(completion) - len(self.completionPrefix())
        
        # 插入补全文本的剩余部分
        cursor.insertText(completion[-extra:])
        
        # 更新光标
        self.editor.setTextCursor(cursor)
    
    def text_under_cursor(self) -> str:
        """
        获取光标下的文本（当前单词）
        
        Returns:
            str: 光标下的文本
        """
        cursor = self.editor.textCursor()
        cursor.select(cursor.SelectionType.WordUnderCursor)
        return cursor.selectedText()
