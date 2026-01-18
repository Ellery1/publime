# Code Completer Bug修复

## 修复日期
2026年1月16日

## 问题描述

**错误信息**:
```
AttributeError: 'NoneType' object has no attribute 'lower'
```

**错误位置**:
- 文件: `core/code_completer.py`
- 方法: `CodeCompleter.set_language()` 和 `get_keyword_completions()`
- 行号: 第128行和第206行

**触发条件**:
当用户在状态栏选择不支持语法高亮的语言（如Plain Text、XML、YAML）时，系统会将语言设置为`None`，但`code_completer.py`中的方法没有处理`None`的情况。

## 根本原因

与之前的`syntax_highlighter.py`问题类似，`CodeCompleter`类的两个方法假设`language`参数总是字符串：

1. **set_language方法**:
```python
def set_language(self, language: str) -> None:
    self.current_language = language.lower()  # 如果language是None，这里会报错
```

2. **get_keyword_completions方法**:
```python
def get_keyword_completions(self, language: str) -> List[str]:
    return self.LANGUAGE_KEYWORDS.get(language.lower(), [])  # 如果language是None，这里会报错
```

当用户选择Plain Text、XML或YAML等语言时，`editor_pane.py`会调用：
```python
self.code_completer.set_language(language)  # language可能是None
```

## 修复方案

### 1. 修复set_language方法

```python
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
```

### 2. 修复get_keyword_completions方法

```python
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
```

## 修复效果

修复后的行为：
1. 选择Plain Text、XML、YAML等语言时，不会报错
2. 这些语言的代码补全功能会被禁用（返回空列表）
3. 可以正常在支持代码补全的语言和不支持的语言之间切换

## 测试验证

```python
from core.code_completer import CodeCompleter
from PySide6.QtWidgets import QPlainTextEdit, QApplication
import sys

app = QApplication.instance() or QApplication(sys.argv)
editor = QPlainTextEdit()
completer = CodeCompleter(editor)

# 测试None参数
completer.set_language(None)
print("✓ set_language(None) 成功")

keywords = completer.get_keyword_completions(None)
print(f"✓ get_keyword_completions(None) 返回: {keywords}")  # 输出: []
```

结果：
- ✓ set_language(None) 成功
- ✓ get_keyword_completions(None) 返回: []

## 相关修复

这是继`syntax_highlighter.py`之后的第二个类似问题。两个问题的根本原因相同：
- 都是因为没有处理`None`参数
- 都是在语言切换功能中触发
- 修复方法也类似：添加`None`检查

## 修改的文件
- `core/code_completer.py` - 在`set_language`和`get_keyword_completions`方法中添加None检查

## 相关功能
此修复确保了以下功能正常工作：
- 状态栏语言选择器
- 在不同语言之间切换
- Plain Text、XML、YAML等无代码补全语言的支持
- 代码补全功能的启用/禁用

## 后续建议

1. **统一处理**: 考虑在所有接受`language`参数的方法中统一处理`None`的情况
2. **类型提示**: 可以将类型提示改为`Optional[str]`以明确表示可以接受`None`
3. **文档完善**: 在所有相关方法的文档字符串中说明`None`的含义和行为

## 完整的语言切换流程

当用户在状态栏选择语言时：
1. `MainWindow.on_language_changed()` 被调用
2. 根据语言映射获取内部语言标识符（可能是`None`）
3. 调用 `EditorPane.set_language(language)`
4. EditorPane调用：
   - `self.syntax_highlighter.set_language(language)` ✓ 已修复
   - `self.code_completer.set_language(language)` ✓ 已修复
5. 两个组件都正确处理`None`，不会报错

## 总结

通过在`code_completer.py`中添加`None`检查，解决了语言切换时的崩溃问题。现在用户可以自由地在所有语言之间切换，包括那些不支持代码补全的语言。
