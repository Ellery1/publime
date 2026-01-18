"""
语法高亮器模块

该模块实现了基于 QSyntaxHighlighter 的语法高亮功能，支持多种编程语言。
"""

import re
from typing import List, Tuple, Optional
from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QTextDocument
from themes.theme import Theme


class HighlightRule:
    """
    高亮规则类
    
    定义一个语法高亮规则，包含匹配模式和格式。
    """
    
    def __init__(self, pattern: str, format_type: str):
        """
        初始化高亮规则
        
        Args:
            pattern: 正则表达式模式
            format_type: 格式类型（keyword, string, comment, function, number, operator, class）
        """
        self.pattern = QRegularExpression(pattern)
        self.format_type = format_type


class LanguageRules:
    """
    语言规则定义类
    
    为不同编程语言定义语法高亮规则。
    """
    
    @staticmethod
    def get_rules(language: str) -> List[HighlightRule]:
        """
        获取指定语言的高亮规则
        
        Args:
            language: 语言名称，如果为None则返回空规则
            
        Returns:
            List[HighlightRule]: 高亮规则列表
        """
        if language is None:
            return []
        
        language = language.lower()
        
        if language == "python":
            return LanguageRules._get_python_rules()
        elif language == "java":
            return LanguageRules._get_java_rules()
        elif language == "sql":
            return LanguageRules._get_sql_rules()
        elif language == "json":
            return LanguageRules._get_json_rules()
        elif language == "javascript":
            return LanguageRules._get_javascript_rules()
        elif language == "kotlin":
            return LanguageRules._get_kotlin_rules()
        elif language == "markdown":
            return LanguageRules._get_markdown_rules()
        elif language == "xml":
            return LanguageRules._get_xml_rules()
        elif language == "yaml":
            return LanguageRules._get_yaml_rules()
        else:
            return []

    
    @staticmethod
    def _get_python_rules() -> List[HighlightRule]:
        """获取 Python 语法规则"""
        rules = []
        
        rules.append(HighlightRule(r'#[^\n]*', 'comment'))
        rules.append(HighlightRule(r'"""[\s\S]*?"""', 'comment'))
        rules.append(HighlightRule(r"'''[\s\S]*?'''", 'comment'))
        rules.append(HighlightRule(r'[fF]"[^"\\]*(\\.[^"\\]*)*"', 'string'))
        rules.append(HighlightRule(r"[fF]'[^'\\]*(\\.[^'\\]*)*'", 'string'))
        rules.append(HighlightRule(r'"[^"\\]*(\\.[^"\\]*)*"', 'string'))
        rules.append(HighlightRule(r"'[^'\\]*(\\.[^'\\]*)*'", 'string'))
        rules.append(HighlightRule(r'[rRbB]"[^"\\]*(\\.[^"\\]*)*"', 'string'))
        rules.append(HighlightRule(r"[rRbB]'[^'\\]*(\\.[^'\\]*)*'", 'string'))
        rules.append(HighlightRule(r'@[\w\.]+', 'decorator'))
        rules.append(HighlightRule(r'\b0[xX][0-9a-fA-F]+\b', 'number'))
        rules.append(HighlightRule(r'\b0[oO][0-7]+\b', 'number'))
        rules.append(HighlightRule(r'\b0[bB][01]+\b', 'number'))
        rules.append(HighlightRule(r'\b[0-9]+\.?[0-9]*([eE][+-]?[0-9]+)?\b', 'number'))
        
        keywords = ['and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue',
            'def', 'del', 'elif', 'else', 'except', 'False', 'finally', 'for',
            'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'None',
            'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'True', 'try',
            'while', 'with', 'yield', 'self', 'cls']
        keyword_pattern = r'\b(' + '|'.join(keywords) + r')\b'
        rules.append(HighlightRule(keyword_pattern, 'keyword'))
        
        builtins_types = ['Exception', 'ValueError', 'TypeError', 'KeyError', 'IndexError',
            'AttributeError', 'NameError', 'IOError', 'RuntimeError', 'StopIteration',
            'BaseException', 'SystemExit', 'KeyboardInterrupt', 'GeneratorExit',
            'StopAsyncIteration', 'ArithmeticError', 'AssertionError', 'EOFError',
            'ImportError', 'LookupError', 'MemoryError', 'OSError', 'ReferenceError',
            'SyntaxError', 'IndentationError', 'TabError', 'SystemError', 'UnicodeError']
        builtin_types_pattern = r'\b(' + '|'.join(builtins_types) + r')\b'
        rules.append(HighlightRule(builtin_types_pattern, 'class'))
        
        rules.append(HighlightRule(r'\b[A-Z][a-zA-Z0-9_]*\b', 'class'))
        
        builtins = ['print', 'len', 'range', 'str', 'int', 'float', 'list', 'dict', 'set',
            'tuple', 'bool', 'type', 'isinstance', 'issubclass', 'super', 'open',
            'input', 'enumerate', 'zip', 'map', 'filter', 'sorted', 'sum', 'min',
            'max', 'abs', 'round', 'all', 'any', 'dir', 'help', 'id', 'hash',
            'next', 'iter', 'reversed', 'slice', 'staticmethod', 'classmethod',
            'property', 'getattr', 'setattr', 'hasattr', 'delattr', 'callable']
        builtin_pattern = r'\b(' + '|'.join(builtins) + r')(?=\s*\()'
        rules.append(HighlightRule(builtin_pattern, 'function'))
        
        rules.append(HighlightRule(r'\b__\w+__\b', 'function'))
        rules.append(HighlightRule(r'(?<=\bdef\s)\w+', 'function'))
        rules.append(HighlightRule(r'(?<=\bclass\s)\w+', 'class'))
        rules.append(HighlightRule(r'\b[a-z_][a-zA-Z0-9_]*(?=\s*\()', 'function'))
        
        keywords_for_exclusion = '|'.join(keywords)
        variable_pattern = r'\b(?!' + keywords_for_exclusion + r'\b)[a-z_][a-zA-Z0-9_]*\b(?!\s*\()'
        rules.append(HighlightRule(variable_pattern, 'variable'))
        
        rules.append(HighlightRule(r'[+\-*/%=<>!&|^~]', 'operator'))
        
        return rules

    
    @staticmethod
    def _get_java_rules() -> List[HighlightRule]:
        """获取 Java 语法规则"""
        rules = []
        
        rules.append(HighlightRule(r'//[^\n]*', 'comment'))
        rules.append(HighlightRule(r'/\*.*?\*/', 'comment'))
        rules.append(HighlightRule(r'"[^"\\]*(\\.[^"\\]*)*"', 'string'))
        rules.append(HighlightRule(r"'[^'\\]*(\\.[^'\\]*)*'", 'string'))
        rules.append(HighlightRule(r'@[\w\.]+', 'decorator'))
        rules.append(HighlightRule(r'\b(package|import)\s+[\w\.]+', 'keyword'))
        rules.append(HighlightRule(r'\b0[xX][0-9a-fA-F]+[lL]?\b', 'number'))
        rules.append(HighlightRule(r'\b[0-9]+\.?[0-9]*([eE][+-]?[0-9]+)?[fFdDlL]?\b', 'number'))
        
        keywords = ['abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch',
            'char', 'class', 'const', 'continue', 'default', 'do', 'double',
            'else', 'enum', 'extends', 'final', 'finally', 'float', 'for',
            'goto', 'if', 'implements', 'import', 'instanceof', 'int', 'interface',
            'long', 'native', 'new', 'package', 'private', 'protected', 'public',
            'return', 'short', 'static', 'strictfp', 'super', 'switch', 'synchronized',
            'this', 'throw', 'throws', 'transient', 'try', 'void', 'volatile', 'while',
            'true', 'false', 'null', 'var']
        keyword_pattern = r'\b(' + '|'.join(keywords) + r')\b'
        rules.append(HighlightRule(keyword_pattern, 'keyword'))
        
        types = ['String', 'Integer', 'Long', 'Double', 'Float', 'Boolean', 'Character',
            'Byte', 'Short', 'Object', 'List', 'ArrayList', 'Map', 'HashMap',
            'Set', 'HashSet', 'Collection', 'Optional', 'Stream', 'Arrays',
            'System', 'Math', 'StringBuilder', 'StringBuffer', 'Thread',
            'Exception', 'RuntimeException', 'Throwable']
        type_pattern = r'\b(' + '|'.join(types) + r')\b'
        rules.append(HighlightRule(type_pattern, 'class'))
        
        rules.append(HighlightRule(r'\b[A-Z][a-zA-Z0-9_]*\b', 'class'))
        rules.append(HighlightRule(r'\b[a-z][a-zA-Z0-9_]*(?=\s*\()', 'function'))
        
        keywords_for_exclusion = '|'.join(keywords)
        variable_pattern = r'\b(?!' + keywords_for_exclusion + r'\b)[a-z][a-zA-Z0-9_]*\b(?!\s*\()'
        rules.append(HighlightRule(variable_pattern, 'variable'))
        
        rules.append(HighlightRule(r'(?<=\b(?:class|interface|enum)\s)\w+', 'class'))
        rules.append(HighlightRule(r'->|[+\-*/%=<>!&|^~]', 'operator'))
        
        return rules
    
    @staticmethod
    def _get_sql_rules() -> List[HighlightRule]:
        """获取 SQL 语法规则"""
        rules = []
        
        rules.append(HighlightRule(r'--[^\n]*', 'comment'))
        rules.append(HighlightRule(r'/\*.*?\*/', 'comment'))
        rules.append(HighlightRule(r"'[^']*'", 'string'))
        rules.append(HighlightRule(r'"[^"]*"', 'string'))
        rules.append(HighlightRule(r'\b[0-9]+\.?[0-9]*\b', 'number'))
        
        dml_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'MERGE',
                        'select', 'insert', 'update', 'delete', 'merge']
        dml_pattern = r'\b(' + '|'.join(dml_keywords) + r')\b'
        rules.append(HighlightRule(dml_pattern, 'keyword'))
        
        ddl_keywords = ['CREATE', 'ALTER', 'DROP', 'TRUNCATE', 'RENAME',
                        'create', 'alter', 'drop', 'truncate', 'rename']
        ddl_pattern = r'\b(' + '|'.join(ddl_keywords) + r')\b'
        rules.append(HighlightRule(ddl_pattern, 'keyword'))
        
        keywords = ['FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER', 'FULL',
            'CROSS', 'ON', 'AS', 'AND', 'OR', 'NOT', 'NULL', 'IS', 'IN', 'EXISTS',
            'BETWEEN', 'LIKE', 'ORDER', 'BY', 'GROUP', 'HAVING', 'LIMIT', 'OFFSET',
            'UNION', 'ALL', 'DISTINCT', 'INTO', 'VALUES', 'SET', 'CASE', 'WHEN',
            'THEN', 'ELSE', 'END', 'WITH', 'OVER', 'PARTITION', 'WINDOW',
            'PRIMARY', 'KEY', 'FOREIGN', 'REFERENCES', 'CONSTRAINT', 'UNIQUE',
            'INDEX', 'DEFAULT', 'AUTO_INCREMENT', 'CHECK', 'CASCADE', 'TABLE',
            'VIEW', 'DATABASE', 'SCHEMA', 'PROCEDURE', 'FUNCTION', 'TRIGGER',
            'from', 'where', 'join', 'inner', 'left', 'right', 'outer', 'full',
            'cross', 'on', 'as', 'and', 'or', 'not', 'null', 'is', 'in', 'exists',
            'between', 'like', 'order', 'by', 'group', 'having', 'limit', 'offset',
            'union', 'all', 'distinct', 'into', 'values', 'set', 'case', 'when',
            'then', 'else', 'end', 'with', 'over', 'partition', 'window',
            'primary', 'key', 'foreign', 'references', 'constraint', 'unique',
            'index', 'default', 'auto_increment', 'check', 'cascade', 'table',
            'view', 'database', 'schema', 'procedure', 'function', 'trigger']
        keyword_pattern = r'\b(' + '|'.join(keywords) + r')\b'
        rules.append(HighlightRule(keyword_pattern, 'keyword'))
        
        types = ['INT', 'INTEGER', 'BIGINT', 'SMALLINT', 'TINYINT', 'DECIMAL', 'NUMERIC',
            'FLOAT', 'REAL', 'DOUBLE', 'VARCHAR', 'CHAR', 'TEXT', 'BLOB',
            'DATE', 'TIME', 'DATETIME', 'TIMESTAMP', 'BOOLEAN', 'BOOL', 'ENUM',
            'int', 'integer', 'bigint', 'smallint', 'tinyint', 'decimal', 'numeric',
            'float', 'real', 'double', 'varchar', 'char', 'text', 'blob',
            'date', 'time', 'datetime', 'timestamp', 'boolean', 'bool', 'enum']
        type_pattern = r'\b(' + '|'.join(types) + r')\b'
        rules.append(HighlightRule(type_pattern, 'class'))
        
        functions = ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'UPPER', 'LOWER', 'LENGTH',
            'SUBSTRING', 'CONCAT', 'NOW', 'DATE', 'TIME', 'YEAR', 'MONTH', 'DAY',
            'COALESCE', 'NULLIF', 'CAST', 'CONVERT', 'ROUND', 'FLOOR', 'CEIL',
            'ABS', 'TRIM', 'LTRIM', 'RTRIM', 'REPLACE', 'CHARINDEX',
            'ROW_NUMBER', 'RANK', 'DENSE_RANK', 'NTILE', 'LAG', 'LEAD',
            'FIRST_VALUE', 'LAST_VALUE', 'DATEDIFF', 'DATEADD', 'GETDATE',
            'count', 'sum', 'avg', 'max', 'min', 'upper', 'lower', 'length',
            'substring', 'concat', 'now', 'date', 'time', 'year', 'month', 'day',
            'coalesce', 'nullif', 'cast', 'convert', 'round', 'floor', 'ceil',
            'abs', 'trim', 'ltrim', 'rtrim', 'replace', 'charindex',
            'row_number', 'rank', 'dense_rank', 'ntile', 'lag', 'lead',
            'first_value', 'last_value', 'datediff', 'dateadd', 'getdate']
        function_pattern = r'\b(' + '|'.join(functions) + r')(?=\s*\()'
        rules.append(HighlightRule(function_pattern, 'function'))
        
        rules.append(HighlightRule(r'[+\-*/%=<>!]', 'operator'))
        
        return rules
    
    @staticmethod
    def _get_json_rules() -> List[HighlightRule]:
        """获取 JSON 语法规则"""
        rules = []
        
        rules.append(HighlightRule(r'"[^"]*"\s*:', 'property'))
        rules.append(HighlightRule(r'\b(true|false|null)\b', 'keyword'))
        rules.append(HighlightRule(r'"[^"\\]*(\\.[^"\\]*)*"', 'string'))
        rules.append(HighlightRule(r'\b-?[0-9]+\.?[0-9]*([eE][+-]?[0-9]+)?\b', 'number'))
        rules.append(HighlightRule(r'[{}\[\],:]', 'operator'))
        
        return rules

    @staticmethod
    def _get_javascript_rules() -> List[HighlightRule]:
        """获取 JavaScript 语法规则"""
        rules = []
        
        rules.append(HighlightRule(r'//[^\n]*', 'comment'))
        rules.append(HighlightRule(r'/\*.*?\*/', 'comment'))
        rules.append(HighlightRule(r'`[^`]*`', 'string'))
        rules.append(HighlightRule(r'"[^"\\]*(\\.[^"\\]*)*"', 'string'))
        rules.append(HighlightRule(r"'[^'\\]*(\\.[^'\\]*)*'", 'string'))
        rules.append(HighlightRule(r'/[^/\n]+/[gimuy]*', 'string'))
        rules.append(HighlightRule(r'\b0[xX][0-9a-fA-F]+\b', 'number'))
        rules.append(HighlightRule(r'\b0[oO][0-7]+\b', 'number'))
        rules.append(HighlightRule(r'\b0[bB][01]+\b', 'number'))
        rules.append(HighlightRule(r'\b[0-9]+\.?[0-9]*([eE][+-]?[0-9]+)?\b', 'number'))
        
        keywords = ['async', 'await', 'break', 'case', 'catch', 'class', 'const', 'continue',
            'debugger', 'default', 'delete', 'do', 'else', 'export', 'extends',
            'finally', 'for', 'function', 'if', 'import', 'in', 'instanceof',
            'let', 'new', 'return', 'super', 'switch', 'this', 'throw', 'try',
            'typeof', 'var', 'void', 'while', 'with', 'yield', 'true', 'false',
            'null', 'undefined', 'of', 'static', 'get', 'set']
        keyword_pattern = r'\b(' + '|'.join(keywords) + r')\b'
        rules.append(HighlightRule(keyword_pattern, 'keyword'))
        
        builtins = ['console', 'Array', 'Object', 'String', 'Number', 'Boolean', 'Date',
            'Math', 'JSON', 'Promise', 'Set', 'Map', 'WeakSet', 'WeakMap',
            'Symbol', 'Proxy', 'Reflect', 'Error', 'TypeError', 'RangeError',
            'RegExp', 'Function', 'parseInt', 'parseFloat', 'isNaN', 'isFinite']
        builtin_pattern = r'\b(' + '|'.join(builtins) + r')\b'
        rules.append(HighlightRule(builtin_pattern, 'class'))
        
        rules.append(HighlightRule(r'\b[A-Z][a-zA-Z0-9_]*\b', 'class'))
        rules.append(HighlightRule(r'\b[a-z_$][a-zA-Z0-9_$]*(?=\s*\()', 'function'))
        rules.append(HighlightRule(r'=>', 'operator'))
        rules.append(HighlightRule(r'[+\-*/%=<>!&|^~]', 'operator'))
        
        return rules

    @staticmethod
    def _get_kotlin_rules() -> List[HighlightRule]:
        """获取 Kotlin 语法规则"""
        rules = []
        
        rules.append(HighlightRule(r'//[^\n]*', 'comment'))
        rules.append(HighlightRule(r'/\*.*?\*/', 'comment'))
        rules.append(HighlightRule(r'"""[\s\S]*?"""', 'string'))
        rules.append(HighlightRule(r'"[^"\\]*(\\.[^"\\]*)*"', 'string'))
        rules.append(HighlightRule(r"'[^'\\]*(\\.[^'\\]*)*'", 'string'))
        rules.append(HighlightRule(r'@[\w\.]+', 'decorator'))
        rules.append(HighlightRule(r'\b0[xX][0-9a-fA-F]+[lL]?\b', 'number'))
        rules.append(HighlightRule(r'\b0[bB][01]+[lL]?\b', 'number'))
        rules.append(HighlightRule(r'\b[0-9]+\.?[0-9]*([eE][+-]?[0-9]+)?[fFdDlL]?\b', 'number'))
        
        keywords = ['abstract', 'actual', 'annotation', 'as', 'break', 'by', 'catch', 'class',
            'companion', 'const', 'constructor', 'continue', 'crossinline', 'data',
            'delegate', 'do', 'dynamic', 'else', 'enum', 'expect', 'external',
            'false', 'final', 'finally', 'for', 'fun', 'get', 'if', 'import',
            'in', 'infix', 'init', 'inline', 'inner', 'interface', 'internal',
            'is', 'lateinit', 'noinline', 'null', 'object', 'open', 'operator',
            'out', 'override', 'package', 'private', 'protected', 'public',
            'reified', 'return', 'sealed', 'set', 'super', 'suspend', 'tailrec',
            'this', 'throw', 'true', 'try', 'typealias', 'typeof', 'val', 'var',
            'vararg', 'when', 'where', 'while']
        keyword_pattern = r'\b(' + '|'.join(keywords) + r')\b'
        rules.append(HighlightRule(keyword_pattern, 'keyword'))
        
        types = ['String', 'Int', 'Long', 'Double', 'Float', 'Boolean', 'Char', 'Byte',
            'Short', 'Any', 'Unit', 'Nothing', 'List', 'MutableList', 'Set',
            'MutableSet', 'Map', 'MutableMap', 'Array', 'IntArray', 'LongArray',
            'Pair', 'Triple', 'Sequence', 'Collection', 'Iterable']
        type_pattern = r'\b(' + '|'.join(types) + r')\b'
        rules.append(HighlightRule(type_pattern, 'class'))
        
        rules.append(HighlightRule(r'\b[A-Z][a-zA-Z0-9_]*\b', 'class'))
        rules.append(HighlightRule(r'\b[a-z][a-zA-Z0-9_]*(?=\s*\()', 'function'))
        rules.append(HighlightRule(r'->|[+\-*/%=<>!&|^~]', 'operator'))
        
        return rules

    @staticmethod
    def _get_markdown_rules() -> List[HighlightRule]:
        """获取 Markdown 语法规则（包含所有改进）"""
        rules = []
        
        # 标题 (橙红色，更醒目)
        rules.append(HighlightRule(r'^#{1,6}\s+.*$', 'heading'))
        
        # 粗体
        rules.append(HighlightRule(r'\*\*[^\*]+\*\*', 'bold'))
        rules.append(HighlightRule(r'__[^_]+__', 'bold'))
        
        # 斜体 (改进：避免匹配粗体)
        rules.append(HighlightRule(r'(?<!\*)\*(?!\*)([^\*]+)\*(?!\*)', 'italic'))
        rules.append(HighlightRule(r'(?<!_)_(?!_)([^_]+)_(?!_)', 'italic'))
        
        # 删除线
        rules.append(HighlightRule(r'~~[^~]+~~', 'strikethrough'))
        
        # 行内代码
        rules.append(HighlightRule(r'`[^`]+`', 'code'))
        
        # 链接
        rules.append(HighlightRule(r'\[([^\]]+)\]\(([^\)]+)\)', 'markdown_link'))
        
        # 图片
        rules.append(HighlightRule(r'!\[([^\]]*)\]\(([^\)]+)\)', 'markdown_link'))
        
        # 任务列表复选框 (青色，更醒目)
        rules.append(HighlightRule(r'^\s*[-\*\+]\s+\[[xX ]\]', 'markdown_link'))
        
        # 脚注引用和定义 (青色)
        rules.append(HighlightRule(r'\[\^[^\]]+\]', 'markdown_link'))
        
        # 表格分隔符 (特殊颜色)
        rules.append(HighlightRule(r'\|', 'operator'))
        
        # HTML 标签
        rules.append(HighlightRule(r'</?[a-zA-Z][^>]*>', 'tag'))
        
        # 注意：行内数学公式 $...$ 和块级数学公式 $$...$$ 
        # 现在通过 _highlight_inline_math() 和 _highlight_markdown_with_code_blocks() 手动处理
        # 以便对公式内部应用语法高亮
        
        # 列表
        rules.append(HighlightRule(r'^\s*[-\*\+]\s+', 'operator'))
        rules.append(HighlightRule(r'^\s*\d+\.\s+', 'operator'))
        
        # 引用
        rules.append(HighlightRule(r'^>\s+.*$', 'comment'))
        
        # 水平线
        rules.append(HighlightRule(r'^[-\*_]{3,}$', 'operator'))
        
        return rules

    @staticmethod
    def _get_xml_rules() -> List[HighlightRule]:
        """获取 XML 语法规则（改进版，匹配 Sublime Monokai 风格）"""
        rules = []
        
        # 注释（必须最先匹配，避免被其他规则覆盖）
        rules.append(HighlightRule(r'<!--.*?-->', 'comment'))
        
        # CDATA
        rules.append(HighlightRule(r'<!\[CDATA\[.*?\]\]>', 'string'))
        
        # XML 声明 <?xml ... ?>
        rules.append(HighlightRule(r'<\?xml', 'tag'))
        rules.append(HighlightRule(r'\?>', 'tag'))
        
        # DOCTYPE
        rules.append(HighlightRule(r'<!DOCTYPE.*?>', 'keyword'))
        
        # 开始标签和结束标签的标签名（粉红色）
        # 匹配 <tagname 和 </tagname
        rules.append(HighlightRule(r'</?[\w:]+', 'tag'))
        
        # 标签结束符号 > 和 />（粉红色）
        rules.append(HighlightRule(r'/?>',  'tag'))
        
        # 属性名（紫色）- 在标签内部，等号前面的单词
        rules.append(HighlightRule(r'\b[\w:]+(?==)', 'number'))
        
        # 属性值（橙黄色）- 引号包围的字符串
        rules.append(HighlightRule(r'"[^"]*"', 'string'))
        rules.append(HighlightRule(r"'[^']*'", 'string'))
        
        return rules
    
    @staticmethod
    def _get_yaml_rules() -> List[HighlightRule]:
        """获取 YAML 语法规则（改进版，匹配 Sublime Monokai 风格）"""
        rules = []
        
        # 注释（灰绿色）
        rules.append(HighlightRule(r'#[^\n]*', 'comment'))
        
        # 文档分隔符（粉红色）
        rules.append(HighlightRule(r'^---$', 'operator'))
        rules.append(HighlightRule(r'^\.\.\.$ ', 'operator'))
        
        # 时间相关的键名（橙黄色）- 必须在普通键名之前匹配
        rules.append(HighlightRule(r'^[\w\-]*[Dd]ate[\w\-]*:', 'string'))
        rules.append(HighlightRule(r'\s+[\w\-]*[Dd]ate[\w\-]*:', 'string'))
        rules.append(HighlightRule(r'^[\w\-]*[Tt]ime[\w\-]*:', 'string'))
        rules.append(HighlightRule(r'\s+[\w\-]*[Tt]ime[\w\-]*:', 'string'))
        
        # 键 (key:) - 青色
        # 匹配行首的键
        rules.append(HighlightRule(r'^[\w\-]+:', 'class'))
        # 匹配缩进后的键
        rules.append(HighlightRule(r'\s+[\w\-]+:', 'class'))
        
        # 布尔值和 null（粉红色）
        rules.append(HighlightRule(r'\b(true|false|null|True|False|Null|TRUE|FALSE|NULL)\b', 'keyword'))
        
        # 数字（紫色）
        rules.append(HighlightRule(r'\b-?[0-9]+\.?[0-9]*\b', 'number'))
        
        # 字符串值 - 引号包围（橙黄色）
        rules.append(HighlightRule(r'"[^"]*"', 'string'))
        rules.append(HighlightRule(r"'[^']*'", 'string'))
        
        # 列表标记（粉红色）
        rules.append(HighlightRule(r'^\s*-\s+', 'operator'))
        
        # 锚点和别名（青色）
        rules.append(HighlightRule(r'&[\w]+', 'class'))
        rules.append(HighlightRule(r'\*[\w]+', 'class'))
        
        return rules



class SyntaxHighlighter(QSyntaxHighlighter):
    """
    语法高亮器类
    
    基于 QSyntaxHighlighter 实现的多语言语法高亮器。
    支持 Python, Java, JavaScript, Kotlin, SQL, JSON, Markdown, XML, YAML 等语言。
    """
    
    def __init__(self, document: QTextDocument, language: str = ""):
        """
        初始化语法高亮器
        
        Args:
            document: 文本文档对象
            language: 语言名称
        """
        super().__init__(document)
        self.theme = None
        self.language = language
        self.rules = []
        self.formats = {}
        
        self._setup_formats()
        self._setup_rules()
    
    def _setup_formats(self):
        """设置格式"""
        # 如果没有主题，使用默认颜色
        if not self.theme:
            # 创建默认格式（黑白）
            default_format = QTextCharFormat()
            default_format.setForeground(QColor("#000000"))
            
            self.formats['keyword'] = default_format
            self.formats['string'] = default_format
            self.formats['comment'] = default_format
            self.formats['function'] = default_format
            self.formats['number'] = default_format
            self.formats['operator'] = default_format
            self.formats['class'] = default_format
            self.formats['decorator'] = default_format
            self.formats['variable'] = default_format
            self.formats['property'] = default_format
            self.formats['heading'] = default_format
            self.formats['bold'] = default_format
            self.formats['italic'] = default_format
            self.formats['code'] = default_format
            self.formats['markdown_link'] = default_format
            self.formats['markdown_math'] = default_format
            self.formats['strikethrough'] = default_format
            self.formats['tag'] = default_format
            return
            
        # 关键字格式
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(self.theme.keyword_color))
        keyword_format.setFontWeight(QFont.Bold)
        self.formats['keyword'] = keyword_format
        
        # 字符串格式
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(self.theme.string_color))
        self.formats['string'] = string_format
        
        # 注释格式
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(self.theme.comment_color))
        comment_format.setFontItalic(True)
        self.formats['comment'] = comment_format
        
        # 函数格式
        function_format = QTextCharFormat()
        function_format.setForeground(QColor(self.theme.function_color))
        self.formats['function'] = function_format
        
        # 数字格式
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(self.theme.number_color))
        self.formats['number'] = number_format
        
        # 运算符格式
        operator_format = QTextCharFormat()
        operator_format.setForeground(QColor(self.theme.operator_color))
        self.formats['operator'] = operator_format
        
        # 类名格式
        class_format = QTextCharFormat()
        class_format.setForeground(QColor(self.theme.class_color))
        class_format.setFontWeight(QFont.Bold)
        self.formats['class'] = class_format
        
        # 装饰器格式
        decorator_format = QTextCharFormat()
        decorator_format.setForeground(QColor(self.theme.decorator_color))
        self.formats['decorator'] = decorator_format
        
        # 变量格式
        variable_format = QTextCharFormat()
        variable_format.setForeground(QColor(self.theme.variable_color))
        self.formats['variable'] = variable_format
        
        # JSON 属性格式
        property_format = QTextCharFormat()
        property_format.setForeground(QColor(self.theme.property_color))
        self.formats['property'] = property_format
        
        # Markdown 特殊格式
        heading_format = QTextCharFormat()
        heading_format.setForeground(QColor(self.theme.markdown_heading_color or self.theme.keyword_color))
        heading_format.setFontWeight(QFont.Bold)
        self.formats['heading'] = heading_format
        
        bold_format = QTextCharFormat()
        bold_format.setFontWeight(QFont.Bold)
        self.formats['bold'] = bold_format
        
        italic_format = QTextCharFormat()
        italic_format.setFontItalic(True)
        self.formats['italic'] = italic_format
        
        code_format = QTextCharFormat()
        code_format.setForeground(QColor(self.theme.string_color))
        code_format.setBackground(QColor(self.theme.background).lighter(110))
        self.formats['code'] = code_format
        
        markdown_link_format = QTextCharFormat()
        markdown_link_format.setForeground(QColor(self.theme.markdown_link_color))
        markdown_link_format.setFontUnderline(True)
        self.formats['markdown_link'] = markdown_link_format
        
        # 数学公式格式
        markdown_math_format = QTextCharFormat()
        markdown_math_format.setForeground(QColor(self.theme.markdown_math_color))
        self.formats['markdown_math'] = markdown_math_format
        
        # 删除线格式
        strikethrough_format = QTextCharFormat()
        strikethrough_format.setFontStrikeOut(True)
        self.formats['strikethrough'] = strikethrough_format
        
        # HTML 标签格式
        tag_format = QTextCharFormat()
        tag_format.setForeground(QColor(self.theme.tag_color))
        self.formats['tag'] = tag_format
    
    def _setup_rules(self):
        """设置高亮规则"""
        self.rules = LanguageRules.get_rules(self.language)
    
    def set_language(self, language: str):
        """
        设置语言
        
        Args:
            language: 语言名称
        """
        self.language = language
        self._setup_rules()
        self.rehighlight()
    
    def set_theme(self, theme: Theme):
        """
        设置主题（别名方法）
        
        Args:
            theme: 主题对象
        """
        self.apply_theme(theme)
    
    def apply_theme(self, theme: Theme):
        """
        应用主题
        
        Args:
            theme: 主题对象
        """
        self.theme = theme
        self._setup_formats()
        self.rehighlight()
    
    def highlightBlock(self, text: str):
        """
        高亮文本块
        
        Args:
            text: 要高亮的文本
        """
        if not self.language:
            return
        
        # 根据语言选择不同的高亮方法
        if self.language.lower() == 'python':
            self._highlight_python_multiline(text)
        elif self.language.lower() == 'markdown':
            self._highlight_markdown_with_code_blocks(text)
        else:
            self._highlight_standard(text)
    
    def _highlight_standard(self, text: str):
        """
        标准高亮方法
        
        Args:
            text: 要高亮的文本
        """
        for rule in self.rules:
            iterator = rule.pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                start = match.capturedStart()
                length = match.capturedLength()
                format_type = rule.format_type
                
                if format_type in self.formats:
                    self.setFormat(start, length, self.formats[format_type])
        
        # 如果是 Markdown，对行内数学公式应用语法高亮
        if self.language and self.language.lower() == 'markdown':
            self._highlight_inline_math(text)
    
    def _highlight_python_multiline(self, text: str):
        """
        Python 多行字符串和 f-string 高亮
        
        Args:
            text: 要高亮的文本
        """
        # 首先应用标准规则
        self._highlight_standard(text)
        
        # 处理多行字符串
        self.setCurrentBlockState(0)
        
        # 三引号字符串状态: 1="""  2='''
        start_index = 0
        if self.previousBlockState() != 1 and self.previousBlockState() != 2:
            # 查找多行字符串的开始
            triple_double = text.find('"""')
            triple_single = text.find("'''")
            
            if triple_double != -1 and (triple_single == -1 or triple_double < triple_single):
                start_index = triple_double
                self.setCurrentBlockState(1)
            elif triple_single != -1:
                start_index = triple_single
                self.setCurrentBlockState(2)
        else:
            self.setCurrentBlockState(self.previousBlockState())
            start_index = 0
        
        # 应用多行字符串格式
        while self.currentBlockState() in [1, 2]:
            if self.currentBlockState() == 1:
                end_index = text.find('"""', start_index + 3 if start_index == 0 else start_index)
                delimiter_length = 3
            else:
                end_index = text.find("'''", start_index + 3 if start_index == 0 else start_index)
                delimiter_length = 3
            
            if end_index == -1:
                # 多行字符串继续到下一行
                self.setFormat(start_index, len(text) - start_index, self.formats['comment'])
                break
            else:
                # 多行字符串在本行结束
                length = end_index - start_index + delimiter_length
                self.setFormat(start_index, length, self.formats['comment'])
                self.setCurrentBlockState(0)
                break
        
        # 处理 f-string 中的表达式
        self._highlight_fstring_expressions(text)
    
    def _highlight_fstring_expressions(self, text: str):
        """
        高亮 f-string 中的表达式
        
        Args:
            text: 要高亮的文本
        """
        # 查找 f-string
        fstring_pattern = re.compile(r'[fF](["\'])(?:[^"\'\\]|\\.)*?\1')
        for match in fstring_pattern.finditer(text):
            fstring_start = match.start()
            fstring_text = match.group()
            
            # 查找 f-string 中的 {} 表达式
            expr_pattern = re.compile(r'\{([^}]+)\}')
            for expr_match in expr_pattern.finditer(fstring_text):
                expr_start = fstring_start + expr_match.start()
                expr_length = expr_match.end() - expr_match.start()
                
                # 对表达式内容应用变量格式
                self.setFormat(expr_start + 1, expr_length - 2, self.formats['variable'])
    
    def _highlight_markdown_with_code_blocks(self, text: str):
        """
        Markdown 高亮（包含代码块内语法高亮和块级数学公式）
        
        Args:
            text: 要高亮的文本
        """
        # 状态码:
        # 0 = 正常 Markdown
        # 10-16 = 代码块 (10=无语言, 11=python, 12=javascript, 13=java, 14=sql, 15=json, 16=kotlin)
        # 20 = 块级数学公式 $$...$$
        
        # 检查是否在特殊块中
        prev_state = self.previousBlockState()
        
        # 检查是否是块级数学公式结束标记
        if prev_state == 20 and text.strip() == '$$':
            # 数学公式块结束
            self.setCurrentBlockState(0)
            # $$ 符号使用青色
            self.setFormat(0, len(text), self.formats['markdown_link'])
            return
        
        # 检查是否是块级数学公式开始标记
        if prev_state == 0 and text.strip() == '$$':
            # 数学公式块开始
            self.setCurrentBlockState(20)
            # $$ 符号使用青色
            self.setFormat(0, len(text), self.formats['markdown_link'])
            return
        
        # 如果在数学公式块中，应用数学公式格式
        if prev_state == 20:
            self.setCurrentBlockState(20)
            # 先应用基础格式
            self.setFormat(0, len(text), self.formats['markdown_math'])
            # 然后应用数学公式内部的语法高亮
            self._highlight_math_content(text, 0, len(text))
            return
        
        # 检查是否是代码块结束标记（必须在检查开始标记之前）
        if prev_state >= 10 and prev_state < 20 and text.strip() == '```':
            # 代码块结束
            self.setCurrentBlockState(0)
            self.setFormat(0, len(text), self.formats['comment'])
            return
        
        # 检查是否是代码块开始标记
        code_block_start = re.match(r'^```(\w+)?', text)
        if code_block_start:
            # 代码块开始
            lang = code_block_start.group(1)
            if lang:
                lang = lang.lower()
                if lang == 'python':
                    self.setCurrentBlockState(11)
                elif lang in ['javascript', 'js']:
                    self.setCurrentBlockState(12)
                elif lang == 'java':
                    self.setCurrentBlockState(13)
                elif lang == 'sql':
                    self.setCurrentBlockState(14)
                elif lang == 'json':
                    self.setCurrentBlockState(15)
                elif lang == 'kotlin':
                    self.setCurrentBlockState(16)
                else:
                    self.setCurrentBlockState(10)
            else:
                self.setCurrentBlockState(10)
            
            # 高亮 ``` 标记（只高亮三个反引号，语言名称不高亮）
            self.setFormat(0, 3, self.formats['comment'])  # 只高亮 ```
            # 如果有语言名称，可以选择性地高亮（这里保持默认色）
            return
        
        # 如果在代码块中，应用代码高亮
        if prev_state >= 10 and prev_state < 20:
            self.setCurrentBlockState(prev_state)
            self._highlight_code_block_content(text, prev_state)
            return
        
        # 否则应用标准 Markdown 规则
        self.setCurrentBlockState(0)
        self._highlight_standard(text)
    
    def _highlight_code_block_content(self, text: str, state: int):
        """
        高亮代码块内容
        
        Args:
            text: 要高亮的文本
            state: 代码块状态（10-16）
        """
        # 根据状态确定语言
        language_map = {
            10: None,
            11: 'python',
            12: 'javascript',
            13: 'java',
            14: 'sql',
            15: 'json',
            16: 'kotlin'
        }
        
        lang = language_map.get(state)
        if not lang:
            # 无语言，使用默认代码格式
            self.setFormat(0, len(text), self.formats['code'])
            return
        
        # 获取该语言的规则并应用
        rules = LanguageRules.get_rules(lang)
        for rule in rules:
            iterator = rule.pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                start = match.capturedStart()
                length = match.capturedLength()
                format_type = rule.format_type
                
                if format_type in self.formats:
                    self.setFormat(start, length, self.formats[format_type])
    
    def _highlight_math_content(self, text: str, start_pos: int, end_pos: int):
        """
        高亮数学公式内容（类似编程语言的语法高亮）
        
        Args:
            text: 完整文本
            start_pos: 数学公式开始位置（不包括 $）
            end_pos: 数学公式结束位置（不包括 $）
        """
        math_content = text[start_pos:end_pos]
        
        # LaTeX 命令（如 \int, \sum, \frac 等）- 使用青色
        latex_commands = re.finditer(r'\\[a-zA-Z]+', math_content)
        for match in latex_commands:
            self.setFormat(start_pos + match.start(), match.end() - match.start(), 
                          self.formats['markdown_link'])
        
        # 数字 - 使用紫色
        numbers = re.finditer(r'\b\d+\b', math_content)
        for match in numbers:
            self.setFormat(start_pos + match.start(), match.end() - match.start(), 
                          self.formats['number'])
        
        # 操作符（=, +, -, *, /, ^, _）- 使用粉红色
        operators = re.finditer(r'[=+\-*/^_]', math_content)
        for match in operators:
            self.setFormat(start_pos + match.start(), match.end() - match.start(), 
                          self.formats['operator'])
        
        # 括号和花括号 - 使用粉红色
        brackets = re.finditer(r'[(){}\[\]]', math_content)
        for match in brackets:
            self.setFormat(start_pos + match.start(), match.end() - match.start(), 
                          self.formats['operator'])
        
        # 变量和函数名（单个字母或多个字母）- 使用白色（variable 格式）
        # 这个规则应该最后应用，避免覆盖其他高亮
        variables = re.finditer(r'[a-zA-Z]+', math_content)
        for match in variables:
            # 检查是否已经被 LaTeX 命令匹配（以 \ 开头）
            if start_pos + match.start() > 0 and text[start_pos + match.start() - 1] != '\\':
                self.setFormat(start_pos + match.start(), match.end() - match.start(), 
                              self.formats['variable'])
    
    def _highlight_inline_math(self, text: str):
        """
        高亮行内数学公式（$...$）
        
        Args:
            text: 要高亮的文本
        """
        # 查找所有行内数学公式 $...$
        inline_math = re.finditer(r'\$([^\$\n]+)\$', text)
        for match in inline_math:
            # 高亮 $ 符号 - 使用青色
            self.setFormat(match.start(), 1, self.formats['markdown_link'])
            self.setFormat(match.end() - 1, 1, self.formats['markdown_link'])
            
            # 高亮公式内容
            self._highlight_math_content(text, match.start() + 1, match.end() - 1)
