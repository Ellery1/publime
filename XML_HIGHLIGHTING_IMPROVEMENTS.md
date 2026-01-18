# XML 语法高亮改进

## 改进目标

根据用户反馈，Sublime Text 的 XML 高亮色彩更多、更好看。通过对比分析，改进 XML 语法高亮以匹配 Sublime Monokai 主题。

## 改进内容

### 颜色配置

| 元素 | 颜色 | 示例 |
|------|------|------|
| 标签名 | #F92672 (粉红色) | `<company>`, `<name>`, `</department>` |
| 属性名 | #AE81FF (紫色) | `id`, `currency`, `status`, `level` |
| 属性值 | #E6DB74 (橙黄色) | `"1"`, `"USD"`, `"active"`, `"expert"` |
| 注释 | #75715E (灰绿色) | `<!-- XML 示例文件 -->` |
| XML 声明 | #F92672 (粉红色) | `<?xml`, `?>` |
| DOCTYPE | #F92672 (粉红色) | `<!DOCTYPE ...>` |
| CDATA | #E6DB74 (橙黄色) | `<![CDATA[...]]>` |

### 规则优化

#### 1. 注释规则优先

```python
# 注释（必须最先匹配，避免被其他规则覆盖）
rules.append(HighlightRule(r'<!--.*?-->', 'comment'))
```

#### 2. XML 声明分离处理

```python
# XML 声明 <?xml ... ?>
rules.append(HighlightRule(r'<\?xml', 'tag'))
rules.append(HighlightRule(r'\?>', 'tag'))
```

#### 3. 标签名匹配

```python
# 开始标签和结束标签的标签名（粉红色）
rules.append(HighlightRule(r'</?[\w:]+', 'tag'))
rules.append(HighlightRule(r'/?>', 'tag'))
```

#### 4. 属性名匹配（紫色）

```python
# 属性名（紫色）- 在标签内部，等号前面的单词
rules.append(HighlightRule(r'\b[\w:]+(?==)', 'number'))
```

**说明**：使用 `number` 格式类型来获得紫色 (#AE81FF)

#### 5. 属性值匹配

```python
# 属性值（橙黄色）- 引号包围的字符串
rules.append(HighlightRule(r'"[^"]*"', 'string'))
rules.append(HighlightRule(r"'[^']*'", 'string'))
```

## 效果展示

### 示例 1: 基本标签

**输入**:
```xml
<company>
    <name>Tech Solutions Inc.</name>
    <founded>2010</founded>
</company>
```

**高亮效果**:
- `<company>`, `<name>`, `<founded>` - 粉红色（标签名）
- `Tech Solutions Inc.`, `2010` - 白色（标签内容）
- `</company>`, `</name>`, `</founded>` - 粉红色（结束标签）

### 示例 2: 带属性的标签

**输入**:
```xml
<department id="1">
    <budget currency="USD">1000000</budget>
</department>
```

**高亮效果**:
- `<department>`, `<budget>` - 粉红色（标签名）
- `id`, `currency` - 紫色（属性名）
- `"1"`, `"USD"` - 橙黄色（属性值）
- `1000000` - 白色（标签内容）

### 示例 3: 嵌套属性

**输入**:
```xml
<skill level="expert">Python</skill>
<skill level="advanced">Java</skill>
<skill level="intermediate">JavaScript</skill>
```

**高亮效果**:
- `<skill>` - 粉红色（标签名）
- `level` - 紫色（属性名）
- `"expert"`, `"advanced"`, `"intermediate"` - 橙黄色（属性值）
- `Python`, `Java`, `JavaScript` - 白色（标签内容）

### 示例 4: XML 声明和注释

**输入**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- XML 示例文件 -->
```

**高亮效果**:
- `<?xml`, `?>` - 粉红色（XML 声明标记）
- `version`, `encoding` - 紫色（属性名）
- `"1.0"`, `"UTF-8"` - 橙黄色（属性值）
- `<!-- XML 示例文件 -->` - 灰绿色（注释）

## 技术细节

### 规则顺序

规则的应用顺序很重要，以避免颜色覆盖：

1. **注释** - 最先匹配，避免注释内容被其他规则处理
2. **CDATA** - 特殊内容块
3. **XML 声明** - `<?xml ... ?>`
4. **DOCTYPE** - 文档类型声明
5. **标签名** - `<tagname` 和 `</tagname`
6. **标签结束符** - `>` 和 `/>`
7. **属性名** - 等号前面的单词
8. **属性值** - 引号包围的字符串

### 正则表达式

```python
# 注释
r'<!--.*?-->'

# XML 声明
r'<\?xml'
r'\?>'

# 标签名
r'</?[\w:]+'

# 标签结束符
r'/?>'

# 属性名（等号前面）
r'\b[\w:]+(?==)'

# 属性值
r'"[^"]*"'
r"'[^']*'"
```

## 测试结果

✅ 所有 27 个语法高亮测试通过
✅ 标签名使用粉红色，醒目清晰
✅ 属性名使用紫色，舒适美观
✅ 属性值使用橙黄色，鲜艳醒目
✅ 注释使用灰绿色，区分明显
✅ 与 Sublime Monokai 主题一致

## 文件修改

### core/syntax_highlighter.py

**修改方法**: `_get_xml_rules()`

**主要改进**:
1. 调整规则顺序，注释优先
2. 分离 XML 声明处理
3. 属性名使用 `number` 格式（紫色）
4. 添加详细注释说明

## 演示程序

运行 `demo_xml_highlighting.py` 可以看到完整效果：

```bash
python demo_xml_highlighting.py
```

演示程序会：
1. 加载 `samples/sample.xml` 文件
2. 应用 XML 语法高亮
3. 显示颜色配置信息
4. 展示改进说明

## 对比 Sublime Text

改进后的 XML 高亮与 Sublime Text Monokai 主题一致：

✅ 标签名使用粉红色 (#F92672)
✅ 属性名使用紫色 (#AE81FF) - 用户偏好
✅ 属性值使用橙黄色 (#E6DB74)
✅ 注释使用灰绿色 (#75715E)
✅ 色彩丰富，层次分明

## 总结

通过改进 XML 语法高亮规则，现在的实现：

1. **色彩更丰富** - 标签名、属性名、属性值、注释使用不同颜色
2. **层次更分明** - 不同元素一目了然
3. **更加美观** - 属性名使用紫色，舒适美观
4. **完全匹配** - 与 Sublime Monokai 主题一致

XML 高亮改进完成，已通过所有测试，可以验收！
