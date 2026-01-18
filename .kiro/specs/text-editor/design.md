# 设计文档

## 概述

本文档描述了一个基于 Python 和 PySide6 的文本编辑器的技术设计。该编辑器采用模块化架构，将核心编辑功能、UI 组件、搜索引擎和文件管理分离，以实现高性能和可维护性。

### 设计目标

- **性能**: 支持打开和编辑 50MB+ 的大型文本文件
- **响应性**: 保持 UI 流畅，输入延迟 < 100ms
- **可扩展性**: 模块化设计便于添加新语言支持和功能
- **用户体验**: 提供直观的界面和高效的编辑工具

### 技术栈

- **UI 框架**: PySide6 (Qt for Python)
- **语法高亮**: QSyntaxHighlighter + 自定义语法规则
- **文本编辑**: QPlainTextEdit (优化大文件性能)
- **代码补全**: QCompleter + 自定义补全模型
- **持久化**: JSON 文件存储历史记录

## 架构

### 整体架构

系统采用 MVC (Model-View-Controller) 变体架构，分为以下主要层次：

```
┌─────────────────────────────────────────────────────────┐
│                    主窗口 (MainWindow)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  菜单栏      │  │  工具栏      │  │  状态栏      │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
├─────────────────────────────────────────────────────────┤
│              标签页容器 (TabWidget)                      │
│  ┌────────────────────────────────────────────────────┐ │
│  │           编辑器窗格 (EditorPane)                  │ │
│  │           - 文本编辑区                             │ │
│  │           - 行号区域                               │ │
│  │           - 折叠指示器                             │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘

核心组件层:
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 语法高亮器   │  │ 搜索引擎     │  │ 代码补全器   │
└──────────────┘  └──────────────┘  └──────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 文件管理器   │  │ 主题管理器   │  │ 历史记录     │
└──────────────┘  └──────────────┘  └──────────────┘
```

### 模块划分

1. **UI 层** (`ui/`)
   - `main_window.py`: 主窗口和布局
   - `editor_pane.py`: 文本编辑窗格
   - `tab_widget.py`: 标签页管理
   - `dialogs.py`: 查找/替换对话框

2. **核心层** (`core/`)
   - `syntax_highlighter.py`: 语法高亮引擎
   - `search_engine.py`: 搜索和替换引擎
   - `code_completer.py`: 代码补全引擎
   - `file_manager.py`: 文件读写管理
   - `history_manager.py`: 历史记录管理

3. **主题层** (`themes/`)
   - `theme_manager.py`: 主题管理器
   - `dark_theme.py`: 深色主题定义
   - `light_theme.py`: 浅色主题定义

4. **工具层** (`utils/`)
   - `language_detector.py`: 文件类型检测
   - `text_utils.py`: 文本处理工具函数

## 组件和接口

### 1. MainWindow (主窗口)

**职责**: 应用程序的主入口，管理整体布局和顶层交互。

**接口**:
```python
class MainWindow(QMainWindow):
    def __init__(self):
        """初始化主窗口"""
        
    def open_file(self, file_path: str = None) -> None:
        """打开文件到新标签页"""
        
    def save_file(self) -> bool:
        """保存当前文件"""
        
    def save_file_as(self) -> bool:
        """另存为"""
        
    def close_tab(self, index: int) -> None:
        """关闭指定标签页"""
        
    def show_find_dialog(self) -> None:
        """显示查找对话框"""
        
    def show_find_in_files_dialog(self) -> None:
        """显示跨文件搜索对话框"""
        
    def toggle_theme(self) -> None:
        """切换主题"""
        
    def zoom_in(self) -> None:
        """放大字体"""
        
    def zoom_out(self) -> None:
        """缩小字体"""
```

**关键属性**:
- `tab_widget`: 标签页容器
- `theme_manager`: 主题管理器
- `history_manager`: 历史记录管理器
- `current_zoom_level`: 当前缩放级别

### 2. EditorPane (编辑器窗格)

**职责**: 单个文件的文本编辑区域，包含行号、折叠、语法高亮。

**接口**:
```python
class EditorPane(QPlainTextEdit):
    def __init__(self, parent=None):
        """初始化编辑器窗格"""
        
    def set_file_path(self, path: str) -> None:
        """设置关联的文件路径"""
        
    def get_file_path(self) -> str:
        """获取文件路径"""
        
    def is_modified(self) -> bool:
        """检查是否已修改"""
        
    def set_language(self, language: str) -> None:
        """设置语法高亮语言"""
        
    def add_cursor_at_position(self, position: int) -> None:
        """在指定位置添加光标"""
        
    def clear_extra_cursors(self) -> None:
        """清除额外光标"""
        
    def apply_theme(self, theme: Theme) -> None:
        """应用主题"""
        
    def wheelEvent(self, event: QWheelEvent) -> None:
        """处理鼠标滚轮事件（用于缩放）"""
```

**关键属性**:
- `file_path`: 关联的文件路径
- `syntax_highlighter`: 语法高亮器实例
- `line_number_area`: 行号显示区域
- `code_completer`: 代码补全器
- `extra_cursors`: 额外光标列表

### 3. LineNumberArea (行号区域)

**职责**: 显示行号和代码折叠指示器。

**接口**:
```python
class LineNumberArea(QWidget):
    def __init__(self, editor: EditorPane):
        """初始化行号区域"""
        
    def paintEvent(self, event: QPaintEvent) -> None:
        """绘制行号和折叠指示器"""
        
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """处理折叠/展开点击"""
        
    def sizeHint(self) -> QSize:
        """返回建议大小"""
```

### 4. SyntaxHighlighter (语法高亮器)

**职责**: 为不同编程语言提供语法高亮。

**接口**:
```python
class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document: QTextDocument, language: str):
        """初始化语法高亮器"""
        
    def highlightBlock(self, text: str) -> None:
        """高亮单个文本块"""
        
    def set_language(self, language: str) -> None:
        """设置高亮语言"""
        
    def apply_theme(self, theme: Theme) -> None:
        """应用主题颜色"""

class LanguageRules:
    """语言规则定义"""
    
    @staticmethod
    def get_rules(language: str) -> List[HighlightRule]:
        """获取指定语言的高亮规则"""
```

**支持的语言规则**:
- Python: 关键字、字符串、注释、函数定义、装饰器
- Java: 关键字、类型、注释、字符串、注解
- SQL: 关键字、函数、字符串、注释
- JSON: 键、值、数字、布尔值
- JavaScript: 关键字、字符串、注释、正则表达式
- Kotlin: 关键字、字符串、注释、注解

### 5. SearchEngine (搜索引擎)

**职责**: 处理文件内和跨文件搜索、替换操作。

**接口**:
```python
class SearchEngine:
    def __init__(self):
        """初始化搜索引擎"""
        
    def find_in_text(
        self, 
        text: str, 
        pattern: str, 
        case_sensitive: bool = False,
        regex: bool = False
    ) -> List[Match]:
        """在文本中查找所有匹配项"""
        
    def replace_in_text(
        self,
        text: str,
        pattern: str,
        replacement: str,
        case_sensitive: bool = False,
        regex: bool = False,
        replace_all: bool = False
    ) -> Tuple[str, int]:
        """替换文本，返回新文本和替换次数"""
        
    def find_in_files(
        self,
        directory: str,
        pattern: str,
        file_patterns: List[str] = None,
        case_sensitive: bool = False,
        regex: bool = False
    ) -> Dict[str, List[Match]]:
        """在多个文件中搜索，返回结果字典"""

class Match:
    """搜索匹配结果"""
    line_number: int
    column: int
    matched_text: str
    line_content: str
```

**说明**: 跨文件搜索结果将在对话框中以列表形式展示，用户可以点击结果项跳转到对应文件和位置。

### 6. CodeCompleter (代码补全器)

**职责**: 提供基于上下文的代码补全建议。

**接口**:
```python
class CodeCompleter(QCompleter):
    def __init__(self, editor: EditorPane):
        """初始化代码补全器"""
        
    def update_completions(self, text: str) -> None:
        """根据当前文本更新补全列表"""
        
    def get_keyword_completions(self, language: str) -> List[str]:
        """获取语言关键字补全"""
        
    def get_context_completions(self, text: str) -> List[str]:
        """获取上下文补全（文件中已有的标识符）"""
```

### 7. FileManager (文件管理器)

**职责**: 处理文件读写操作，支持大文件优化。

**接口**:
```python
class FileManager:
    @staticmethod
    def read_file(file_path: str) -> str:
        """读取文件内容"""
        
    @staticmethod
    def write_file(file_path: str, content: str) -> bool:
        """写入文件内容"""
        
    @staticmethod
    def detect_encoding(file_path: str) -> str:
        """检测文件编码"""
        
    @staticmethod
    def is_large_file(file_path: str, threshold_mb: int = 10) -> bool:
        """检查是否为大文件"""
```

### 8. ThemeManager (主题管理器)

**职责**: 管理编辑器主题和颜色方案。

**接口**:
```python
class Theme:
    """主题数据类"""
    name: str
    background: str
    foreground: str
    selection_bg: str
    selection_fg: str
    line_number_bg: str
    line_number_fg: str
    current_line_bg: str
    syntax_colors: Dict[str, str]

class ThemeManager:
    def __init__(self):
        """初始化主题管理器"""
        
    def get_theme(self, name: str) -> Theme:
        """获取指定主题"""
        
    def apply_theme(self, theme: Theme, window: MainWindow) -> None:
        """应用主题到窗口"""
        
    def get_available_themes(self) -> List[str]:
        """获取可用主题列表"""
```

### 9. HistoryManager (历史记录管理器)

**职责**: 管理最近打开文件的历史记录。

**接口**:
```python
class HistoryManager:
    def __init__(self, max_items: int = 20):
        """初始化历史记录管理器"""
        
    def add_file(self, file_path: str) -> None:
        """添加文件到历史记录"""
        
    def get_recent_files(self) -> List[str]:
        """获取最近文件列表"""
        
    def clear_history(self) -> None:
        """清空历史记录"""
        
    def save_to_disk(self) -> None:
        """保存历史记录到磁盘"""
        
    def load_from_disk(self) -> None:
        """从磁盘加载历史记录"""
```

### 9. HistoryManager (历史记录管理器)

### 文件状态模型

```python
@dataclass
class FileState:
    """文件状态"""
    path: str
    content: str
    is_modified: bool
    cursor_position: int
    scroll_position: int
    language: str
    encoding: str = "utf-8"
```

### 搜索结果模型

```python
@dataclass
class SearchResult:
    """搜索结果"""
    file_path: str
    matches: List[Match]
    total_matches: int

@dataclass
class Match:
    """单个匹配项"""
    line_number: int
    column: int
    matched_text: str
    line_content: str
    start_pos: int
    end_pos: int
```

### 主题模型

```python
@dataclass
class Theme:
    """主题定义"""
    name: str
    background: str
    foreground: str
    selection_bg: str
    selection_fg: str
    line_number_bg: str
    line_number_fg: str
    current_line_bg: str
    cursor_color: str
    
    # 语法高亮颜色
    keyword_color: str
    string_color: str
    comment_color: str
    function_color: str
    number_color: str
    operator_color: str
    class_color: str
```

### 历史记录模型

```python
@dataclass
class HistoryEntry:
    """历史记录条目"""
    file_path: str
    last_opened: datetime
    exists: bool  # 文件是否仍然存在
```

## 正确性属性

*属性是一个特征或行为，应该在系统的所有有效执行中保持为真——本质上是关于系统应该做什么的形式化陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*


### 属性 1: 复制粘贴往返一致性
*对于任何* 文本内容和选择范围，复制选中文本然后粘贴应该产生与原始选中文本相同的内容
**验证需求: 1.1, 1.2**

### 属性 2: 撤销重做往返一致性
*对于任何* 编辑操作序列，执行操作、撤销、然后重做应该恢复到操作后的状态
**验证需求: 1.3, 1.4**

### 属性 3: 文本插入位置正确性
*对于任何* 文本内容、光标位置和插入文本，在指定位置插入文本后，该文本应该出现在正确的位置
**验证需求: 1.5**

### 属性 4: 标签页数量一致性
*对于任何* 打开的文件列表，打开 N 个文件应该创建 N 个标签页
**验证需求: 2.1, 8.4**

### 属性 5: 标签页切换正确性
*对于任何* 打开的标签页集合，切换到标签页 i 应该显示第 i 个文件的内容
**验证需求: 2.2**

### 属性 6: 标签页关闭后数量减少
*对于任何* 包含 N 个标签页的编辑器，关闭一个标签页后应该剩余 N-1 个标签页
**验证需求: 2.3**

### 属性 7: 修改状态指示器正确性
*对于任何* 文件，当内容被修改时，标签页应该显示未保存状态；保存后应该清除该状态
**验证需求: 2.4, 7.5**

### 属性 8: 语法高亮语言检测正确性
*对于任何* 支持的文件扩展名（.py, .java, .sql, .json, .js, .kt），语法高亮器应该检测到正确的语言类型并应用对应的高亮规则
**验证需求: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**

### 属性 9: 代码折叠展开往返一致性
*对于任何* 包含可折叠代码块的文本，折叠然后立即展开应该恢复到原始显示状态
**验证需求: 4.2, 4.4**

### 属性 10: 字体缩放边界限制
*对于任何* 缩放操作序列，字体大小应该始终保持在 6pt 到 72pt 范围内
**验证需求: 6.1, 6.2, 6.3**

### 属性 11: 文件读写往返一致性
*对于任何* 文本内容，写入文件然后读取应该得到相同的内容
**验证需求: 7.2, 7.3**

### 属性 12: 文件读取错误处理
*对于任何* 不存在或无权限的文件路径，尝试读取应该返回错误而不是崩溃，并保持编辑器当前状态不变
**验证需求: 7.6**

### 属性 13: 拖拽多文件打开正确性
*对于任何* 拖拽的文件列表，释放拖拽后应该为每个文件创建一个新标签页
**验证需求: 8.2, 8.3, 8.4**

### 属性 14: 搜索匹配项完整性
*对于任何* 文本和搜索模式，搜索引擎返回的所有匹配项都应该确实匹配该模式，且不应遗漏任何匹配项
**验证需求: 9.2**

### 属性 15: 大小写敏感搜索正确性
*对于任何* 包含不同大小写的文本，大小写敏感搜索应该只匹配完全相同大小写的文本，大小写不敏感搜索应该匹配所有大小写变体
**验证需求: 9.3**

### 属性 16: 正则表达式搜索正确性
*对于任何* 有效的正则表达式模式，搜索引擎应该返回所有符合该正则表达式的匹配项
**验证需求: 9.4, 10.6**

### 属性 17: 单项替换正确性
*对于任何* 文本、搜索模式和替换文本，单项替换应该只替换当前匹配项，其他匹配项保持不变
**验证需求: 9.5**

### 属性 18: 全部替换正确性
*对于任何* 文本、搜索模式和替换文本，全部替换后文本中不应再包含任何原始模式的匹配项
**验证需求: 9.6**

### 属性 19: 搜索结果计数准确性
*对于任何* 文本和搜索模式，返回的匹配项数量应该等于实际匹配项的数量
**验证需求: 9.7**

### 属性 20: 跨文件搜索完整性
*对于任何* 目录和搜索模式，跨文件搜索应该返回该目录下所有文件中的所有匹配项
**验证需求: 10.2**

### 属性 21: 搜索结果按文件分组
*对于任何* 跨文件搜索结果，结果应该按文件路径分组，每个文件的所有匹配项应该在一起
**验证需求: 10.3, 10.4**

### 属性 22: 文件类型过滤正确性
*对于任何* 文件类型过滤器，跨文件搜索应该只返回匹配该类型的文件中的结果
**验证需求: 10.7**

### 属性 23: 多光标添加正确性
*对于任何* 点击位置序列，每次 Ctrl+点击应该在该位置添加一个新光标
**验证需求: 11.1**

### 属性 24: 多光标同步操作
*对于任何* 多光标状态和编辑操作（插入或删除），该操作应该在所有光标位置同步执行
**验证需求: 11.2, 11.3**

### 属性 25: 清除额外光标
*对于任何* 包含多个光标的编辑器状态，按 Escape 键后应该只剩下一个主光标
**验证需求: 11.4**

### 属性 26: Ctrl+D 选择下一个匹配
*对于任何* 选中的文本，按 Ctrl+D 应该选择下一个相同文本的出现位置并添加光标
**验证需求: 11.5**

### 属性 27: 代码补全建议完整性
*对于任何* 输入前缀，代码补全器返回的建议应该包含所有匹配该前缀的语言关键字和文件中已有的标识符
**验证需求: 12.1, 12.2, 12.3**

### 属性 28: 补全文本插入正确性
*对于任何* 选中的补全建议，插入后光标位置的文本应该是该补全文本
**验证需求: 12.4**

### 属性 29: 主题切换颜色更新
*对于任何* 主题切换操作，切换后所有界面元素和语法高亮应该使用新主题的颜色方案
**验证需求: 13.3, 13.4**

### 属性 30: 历史记录添加正确性
*对于任何* 打开的文件，该文件路径应该被添加到历史记录中
**验证需求: 15.1**

### 属性 31: 历史记录容量限制
*对于任何* 历史记录状态，打开超过 20 个文件后，历史记录应该保持最近的 20 个文件
**验证需求: 15.2**

### 属性 32: 历史记录时间排序
*对于任何* 文件打开序列，历史记录应该按打开时间倒序排列（最近打开的在最前）
**验证需求: 15.5**

### 属性 33: 历史记录持久化往返一致性
*对于任何* 历史记录状态，保存到磁盘然后加载应该得到相同的历史记录列表
**验证需求: 15.6, 15.7**

## 错误处理

### 文件操作错误

1. **文件不存在**: 显示友好的错误消息，提示用户文件不存在
2. **权限不足**: 显示权限错误消息，不尝试强制操作
3. **文件过大**: 对于超过 100MB 的文件，显示警告并询问用户是否继续
4. **编码错误**: 尝试多种编码（UTF-8, GBK, GB2312），失败时提示用户选择编码
5. **磁盘空间不足**: 保存文件前检查磁盘空间，不足时提示用户

### 搜索错误

1. **无效正则表达式**: 捕获正则表达式语法错误，显示错误位置和原因
2. **搜索超时**: 对于大型目录搜索，设置超时（30秒），超时后允许用户取消或继续
3. **目录不存在**: 验证搜索目录存在，不存在时提示用户

### UI 错误

1. **内存不足**: 监控内存使用，接近限制时警告用户并建议关闭部分标签页
2. **渲染错误**: 捕获 Qt 渲染异常，记录日志但不崩溃
3. **主题加载失败**: 主题文件损坏时回退到默认主题

### 恢复机制

1. **自动保存**: 每 5 分钟自动保存所有修改的文件到临时位置
2. **崩溃恢复**: 启动时检查临时文件，提示用户恢复未保存的内容
3. **状态持久化**: 保存窗口大小、位置、打开的文件列表，下次启动时恢复

## 测试策略

### 双重测试方法

本项目采用单元测试和基于属性的测试相结合的方法，以确保全面的代码覆盖和正确性验证。

**单元测试**:
- 验证特定示例和边界条件
- 测试组件之间的集成点
- 测试错误处理和异常情况
- 使用 pytest 框架
- 重点关注具体场景而非穷举所有输入

**基于属性的测试**:
- 验证跨所有输入的通用属性
- 通过随机化实现全面的输入覆盖
- 使用 Hypothesis 库
- 每个属性测试至少运行 100 次迭代
- 每个测试必须引用其设计文档属性

### 测试配置

**属性测试标签格式**:
```python
# Feature: text-editor, Property 11: 文件读写往返一致性
@given(st.text())
def test_file_read_write_roundtrip(content):
    ...
```

**最小迭代次数**: 每个属性测试 100 次

### 测试覆盖范围

**核心编辑功能**:
- 单元测试: 特定的复制/粘贴场景、撤销/重做边界情况
- 属性测试: 属性 1-3（复制粘贴、撤销重做、文本插入）

**标签页管理**:
- 单元测试: 打开/关闭标签页的边界情况、空标签页处理
- 属性测试: 属性 4-7（标签页数量、切换、关闭、修改状态）

**语法高亮**:
- 单元测试: 每种语言的特定语法示例
- 属性测试: 属性 8（语言检测正确性）

**搜索和替换**:
- 单元测试: 边界情况（空文本、无匹配、特殊字符）
- 属性测试: 属性 14-22（搜索匹配、替换、跨文件搜索）

**多光标编辑**:
- 单元测试: 特定的多光标场景
- 属性测试: 属性 23-26（光标添加、同步操作、清除）

**文件操作**:
- 单元测试: 错误处理（权限、不存在的文件）
- 属性测试: 属性 11-13（读写一致性、错误处理、拖拽）

**代码补全**:
- 单元测试: 特定语言的关键字补全
- 属性测试: 属性 27-28（补全建议、插入正确性）

**主题和历史**:
- 单元测试: 主题切换的特定场景、历史记录边界
- 属性测试: 属性 29-33（主题切换、历史记录管理）

**性能测试**:
- 大文件加载测试（50MB, 100MB）
- 搜索性能测试（大型目录）
- 内存使用监控测试

### 测试工具

- **pytest**: 单元测试框架
- **Hypothesis**: 基于属性的测试库
- **pytest-qt**: Qt 应用测试支持
- **pytest-cov**: 代码覆盖率报告
- **pytest-benchmark**: 性能基准测试

### CI/CD 集成

- 所有测试在每次提交时自动运行
- 属性测试在 CI 中运行更多迭代（1000 次）
- 性能测试作为夜间构建的一部分运行
- 代码覆盖率目标: 80% 以上

