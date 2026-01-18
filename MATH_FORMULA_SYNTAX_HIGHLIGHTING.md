# 数学公式内部语法高亮实现

## 问题描述

用户反馈：数学公式不仅需要鲜艳的颜色，还需要**区分对待**公式内部的不同元素。

通过对比 Sublime Text 的效果发现，Sublime 对数学公式内部应用了类似编程语言的语法高亮：
- 变量使用白色
- 数字使用紫色
- 操作符使用粉红色
- LaTeX 命令使用青色
- `$` 符号使用青色

## 解决方案

实现数学公式内部的语法高亮，对不同类型的元素应用不同的颜色。

### 实现方法

#### 1. 新增 `_highlight_math_content()` 方法

这个方法负责对数学公式内容应用语法高亮：

```python
def _highlight_math_content(self, text: str, start_pos: int, end_pos: int):
    """
    高亮数学公式内容（类似编程语言的语法高亮）
    
    规则：
    - LaTeX 命令（\int, \sum, \frac 等）→ 青色
    - 数字 → 紫色
    - 操作符（=, +, -, *, /, ^, _）→ 粉红色
    - 括号和花括号 → 粉红色
    - 变量和函数名 → 白色
    """
```

#### 2. 新增 `_highlight_inline_math()` 方法

这个方法负责查找并高亮行内数学公式 `$...$`：

```python
def _highlight_inline_math(self, text: str):
    """
    高亮行内数学公式（$...$）
    
    步骤：
    1. 查找所有 $...$ 模式
    2. 高亮 $ 符号（青色）
    3. 对公式内容应用 _highlight_math_content()
    """
```

#### 3. 修改 `_highlight_markdown_with_code_blocks()` 方法

在块级数学公式 `$$...$$` 中应用语法高亮：

```python
# 如果在数学公式块中，应用数学公式格式
if prev_state == 20:
    self.setCurrentBlockState(20)
    # 先应用基础格式
    self.setFormat(0, len(text), self.formats['markdown_math'])
    # 然后应用数学公式内部的语法高亮
    self._highlight_math_content(text, 0, len(text))
    return
```

#### 4. 修改 `_highlight_standard()` 方法

在标准高亮后，对 Markdown 的行内数学公式应用语法高亮：

```python
# 如果是 Markdown，对行内数学公式应用语法高亮
if self.language and self.language.lower() == 'markdown':
    self._highlight_inline_math(text)
```

## 颜色映射

| 元素 | 颜色 | 示例 |
|------|------|------|
| `$` 符号 | #66D9EF (青色) | `$`E = mc^2`$` |
| LaTeX 命令 | #66D9EF (青色) | `\int`, `\sum`, `\frac` |
| 变量 | #F8F8F2 (白色) | `E`, `m`, `c`, `x`, `a`, `b` |
| 数字 | #AE81FF (紫色) | `2`, `3`, `10` |
| 操作符 | #F92672 (粉红色) | `=`, `+`, `-`, `*`, `/`, `^`, `_` |
| 括号 | #F92672 (粉红色) | `(`, `)`, `{`, `}`, `[`, `]` |

## 效果展示

### 行内公式

**输入**:
```markdown
行内公式：$E = mc^2$
```

**高亮效果**:
- `$` → 青色
- `E` → 白色
- `=` → 粉红色
- `m` → 白色
- `c` → 白色
- `^` → 粉红色
- `2` → 紫色
- `$` → 青色

### 块级公式

**输入**:
```markdown
$$
\int_{a}^{b} f(x) dx = F(b) - F(a)
$$
```

**高亮效果**:
- `$$` → 青色
- `\int` → 青色（LaTeX 命令）
- `_` → 粉红色（操作符）
- `{` → 粉红色（括号）
- `a` → 白色（变量）
- `}` → 粉红色（括号）
- `^` → 粉红色（操作符）
- `{` → 粉红色（括号）
- `b` → 白色（变量）
- `}` → 粉红色（括号）
- `f` → 白色（函数）
- `(` → 粉红色（括号）
- `x` → 白色（变量）
- `)` → 粉红色（括号）
- `dx` → 白色（变量）
- `=` → 粉红色（操作符）
- `F` → 白色（函数）
- `(` → 粉红色（括号）
- `b` → 白色（变量）
- `)` → 粉红色（括号）
- `-` → 粉红色（操作符）
- `F` → 白色（函数）
- `(` → 粉红色（括号）
- `a` → 白色（变量）
- `)` → 粉红色（括号）
- `$$` → 青色

## 技术细节

### 高亮顺序

为了避免颜色覆盖问题，高亮顺序很重要：

1. **LaTeX 命令**（`\int`, `\sum` 等）- 先匹配，避免被变量规则覆盖
2. **数字** - 匹配所有数字
3. **操作符** - 匹配所有操作符
4. **括号** - 匹配所有括号
5. **变量**（最后）- 匹配剩余的字母，但排除 LaTeX 命令

### 正则表达式

```python
# LaTeX 命令
r'\\[a-zA-Z]+'

# 数字
r'\b\d+\b'

# 操作符
r'[=+\-*/^_]'

# 括号
r'[(){}\[\]]'

# 变量（排除 LaTeX 命令）
r'[a-zA-Z]+'  # 需要检查前面不是 \
```

## 测试结果

✅ 所有 202 个单元测试通过
✅ 所有 27 个语法高亮测试通过
✅ 行内数学公式内部语法高亮正确
✅ 块级数学公式内部语法高亮正确
✅ 与 Sublime Text Monokai 主题完全一致

## 文件修改

### core/syntax_highlighter.py

1. **新增方法**:
   - `_highlight_math_content()` - 对数学公式内容应用语法高亮
   - `_highlight_inline_math()` - 查找并高亮行内数学公式

2. **修改方法**:
   - `_highlight_standard()` - 添加行内数学公式处理
   - `_highlight_markdown_with_code_blocks()` - 添加块级数学公式内部高亮
   - `_get_markdown_rules()` - 移除行内数学公式规则（改为手动处理）

### themes/dark_theme.py

- `markdown_math_color`: 保持橙黄色 (#E6DB74)，但现在主要用于基础格式
- 实际显示效果由内部语法高亮决定（变量白色、数字紫色、操作符粉红色等）

## 演示程序

运行 `demo_markdown_improvements.py` 可以看到完整效果：

```bash
python demo_markdown_improvements.py
```

## 对比 Sublime Text

现在的实现与 Sublime Text Monokai 主题**完全一致**：

✅ `$` 符号使用青色  
✅ LaTeX 命令使用青色  
✅ 变量使用白色  
✅ 数字使用紫色  
✅ 操作符使用粉红色  
✅ 括号使用粉红色  

## 总结

通过实现数学公式内部的语法高亮，我们不仅让数学公式更加鲜艳，还实现了**区分对待**不同元素的效果。

**关键改进**：
1. 不再简单地把整个公式涂成一个颜色
2. 对公式内部的变量、数字、操作符、LaTeX 命令等分别应用不同颜色
3. 完全匹配 Sublime Text 的高亮效果

这正是用户期望的"见贤思齐"效果 - 不仅学习 Sublime 的配色，还学习了它的高亮逻辑！
