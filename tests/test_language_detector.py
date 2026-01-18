"""
语言检测器测试模块

测试 LanguageDetector 类的功能。
"""

import pytest
from utils.language_detector import LanguageDetector


class TestLanguageDetector:
    """测试 LanguageDetector 类"""
    
    def test_detect_python_extensions(self):
        """测试 Python 文件扩展名检测"""
        assert LanguageDetector.detect_language("test.py") == "python"
        assert LanguageDetector.detect_language("test.pyw") == "python"
        assert LanguageDetector.detect_language("test.pyi") == "python"
        assert LanguageDetector.detect_language("/path/to/file.py") == "python"
        assert LanguageDetector.detect_language("C:\\Users\\test\\file.py") == "python"
    
    def test_detect_java_extensions(self):
        """测试 Java 文件扩展名检测"""
        assert LanguageDetector.detect_language("test.java") == "java"
        assert LanguageDetector.detect_language("/path/to/Main.java") == "java"
    
    def test_detect_sql_extensions(self):
        """测试 SQL 文件扩展名检测"""
        assert LanguageDetector.detect_language("query.sql") == "sql"
        assert LanguageDetector.detect_language("/database/schema.sql") == "sql"
    
    def test_detect_json_extensions(self):
        """测试 JSON 文件扩展名检测"""
        assert LanguageDetector.detect_language("config.json") == "json"
        assert LanguageDetector.detect_language("/api/data.json") == "json"
    
    def test_detect_javascript_extensions(self):
        """测试 JavaScript 文件扩展名检测"""
        assert LanguageDetector.detect_language("app.js") == "javascript"
        assert LanguageDetector.detect_language("component.jsx") == "javascript"
        assert LanguageDetector.detect_language("module.mjs") == "javascript"
        assert LanguageDetector.detect_language("script.cjs") == "javascript"
    
    def test_detect_kotlin_extensions(self):
        """测试 Kotlin 文件扩展名检测"""
        assert LanguageDetector.detect_language("Main.kt") == "kotlin"
        assert LanguageDetector.detect_language("script.kts") == "kotlin"
    
    def test_case_insensitive_detection(self):
        """测试大小写不敏感的检测"""
        assert LanguageDetector.detect_language("test.PY") == "python"
        assert LanguageDetector.detect_language("test.Py") == "python"
        assert LanguageDetector.detect_language("test.JAVA") == "java"
        assert LanguageDetector.detect_language("test.SQL") == "sql"
        assert LanguageDetector.detect_language("test.JSON") == "json"
        assert LanguageDetector.detect_language("test.JS") == "javascript"
        assert LanguageDetector.detect_language("test.KT") == "kotlin"
    
    def test_unsupported_extensions(self):
        """测试不支持的文件扩展名"""
        assert LanguageDetector.detect_language("test.txt") is None
        assert LanguageDetector.detect_language("test.cpp") is None
        assert LanguageDetector.detect_language("test.rs") is None
        assert LanguageDetector.detect_language("test.go") is None
    
    def test_empty_or_invalid_paths(self):
        """测试空路径或无效路径"""
        assert LanguageDetector.detect_language("") is None
        assert LanguageDetector.detect_language("no_extension") is None
        assert LanguageDetector.detect_language(".hidden") is None
    
    def test_get_supported_extensions(self):
        """测试获取支持的扩展名列表"""
        extensions = LanguageDetector.get_supported_extensions()
        
        # 验证返回的是列表
        assert isinstance(extensions, list)
        
        # 验证包含所有必需的扩展名
        assert ".py" in extensions
        assert ".java" in extensions
        assert ".sql" in extensions
        assert ".json" in extensions
        assert ".js" in extensions
        assert ".kt" in extensions
        
        # 验证至少有这些扩展名
        assert len(extensions) >= 6
    
    def test_get_supported_languages(self):
        """测试获取支持的语言列表"""
        languages = LanguageDetector.get_supported_languages()
        
        # 验证返回的是列表
        assert isinstance(languages, list)
        
        # 验证包含所有必需的语言
        assert "python" in languages
        assert "java" in languages
        assert "sql" in languages
        assert "json" in languages
        assert "javascript" in languages
        assert "kotlin" in languages
        assert "markdown" in languages
        assert "xml" in languages
        assert "yaml" in languages
        
        # 验证语言数量（应该是 9 种）
        assert len(languages) == 9
    
    def test_is_supported(self):
        """测试文件是否支持语法高亮"""
        # 支持的文件
        assert LanguageDetector.is_supported("test.py") is True
        assert LanguageDetector.is_supported("test.java") is True
        assert LanguageDetector.is_supported("test.sql") is True
        assert LanguageDetector.is_supported("test.json") is True
        assert LanguageDetector.is_supported("test.js") is True
        assert LanguageDetector.is_supported("test.kt") is True
        
        # 不支持的文件
        assert LanguageDetector.is_supported("test.txt") is False
        assert LanguageDetector.is_supported("test.cpp") is False
        assert LanguageDetector.is_supported("") is False
        assert LanguageDetector.is_supported("no_extension") is False
    
    def test_complex_file_paths(self):
        """测试复杂的文件路径"""
        # Unix 风格路径
        assert LanguageDetector.detect_language("/home/user/projects/app.py") == "python"
        assert LanguageDetector.detect_language("./src/main.java") == "java"
        assert LanguageDetector.detect_language("../database/query.sql") == "sql"
        
        # Windows 风格路径
        assert LanguageDetector.detect_language("C:\\Projects\\app.py") == "python"
        assert LanguageDetector.detect_language("D:\\Code\\Main.java") == "java"
        
        # 带空格的路径
        assert LanguageDetector.detect_language("/path with spaces/file.py") == "python"
        assert LanguageDetector.detect_language("C:\\My Documents\\script.js") == "javascript"
    
    def test_files_with_multiple_dots(self):
        """测试包含多个点的文件名"""
        assert LanguageDetector.detect_language("test.backup.py") == "python"
        assert LanguageDetector.detect_language("config.dev.json") == "json"
        assert LanguageDetector.detect_language("script.min.js") == "javascript"
        assert LanguageDetector.detect_language("data.2024.01.01.sql") == "sql"
    
    def test_all_supported_extensions_map_to_valid_languages(self):
        """测试所有支持的扩展名都映射到有效的语言"""
        extensions = LanguageDetector.get_supported_extensions()
        languages = LanguageDetector.get_supported_languages()
        
        for ext in extensions:
            # 创建一个测试文件名
            test_file = f"test{ext}"
            detected_language = LanguageDetector.detect_language(test_file)
            
            # 验证检测到的语言在支持的语言列表中
            assert detected_language in languages, \
                f"Extension {ext} maps to {detected_language}, which is not in supported languages"
    
    def test_requirement_3_7_language_detection(self):
        """
        测试需求 3.7: 语法高亮器应根据文件扩展名自动检测语言类型
        
        验证所有支持的语言都能正确检测：
        - Python (.py, .pyw, .pyi)
        - Java (.java)
        - SQL (.sql)
        - JSON (.json)
        - JavaScript (.js, .jsx, .mjs, .cjs)
        - Kotlin (.kt, .kts)
        """
        # Python
        assert LanguageDetector.detect_language("example.py") == "python"
        
        # Java
        assert LanguageDetector.detect_language("Example.java") == "java"
        
        # SQL
        assert LanguageDetector.detect_language("query.sql") == "sql"
        
        # JSON
        assert LanguageDetector.detect_language("data.json") == "json"
        
        # JavaScript
        assert LanguageDetector.detect_language("app.js") == "javascript"
        
        # Kotlin
        assert LanguageDetector.detect_language("Main.kt") == "kotlin"


class TestLanguageDetectorEdgeCases:
    """测试 LanguageDetector 的边界情况"""
    
    def test_none_input(self):
        """测试 None 输入"""
        # 虽然类型提示是 str，但测试健壮性
        assert LanguageDetector.detect_language(None) is None
    
    def test_whitespace_paths(self):
        """测试只包含空白字符的路径"""
        assert LanguageDetector.detect_language("   ") is None
        assert LanguageDetector.detect_language("\t") is None
        assert LanguageDetector.detect_language("\n") is None
    
    def test_extension_only(self):
        """测试只有扩展名的文件（隐藏文件）"""
        # 注意：".py" 这样的文件名在 Unix 系统中被视为隐藏文件，没有扩展名
        # os.path.splitext(".py") 返回 (".py", "")，所以扩展名为空
        assert LanguageDetector.detect_language(".py") is None
        assert LanguageDetector.detect_language(".java") is None
        assert LanguageDetector.detect_language(".sql") is None
    
    def test_very_long_paths(self):
        """测试非常长的文件路径"""
        long_path = "/".join(["dir"] * 100) + "/file.py"
        assert LanguageDetector.detect_language(long_path) == "python"
    
    def test_special_characters_in_path(self):
        """测试路径中包含特殊字符"""
        assert LanguageDetector.detect_language("/path/with-dashes/file.py") == "python"
        assert LanguageDetector.detect_language("/path/with_underscores/file.java") == "java"
        assert LanguageDetector.detect_language("/path/with@symbols/file.sql") == "sql"
        assert LanguageDetector.detect_language("/path/with#hash/file.json") == "json"
    
    def test_unicode_paths(self):
        """测试包含 Unicode 字符的路径"""
        assert LanguageDetector.detect_language("/路径/文件.py") == "python"
        assert LanguageDetector.detect_language("/путь/файл.java") == "java"
        assert LanguageDetector.detect_language("/パス/ファイル.sql") == "sql"
