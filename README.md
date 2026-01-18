# Publime - 文本编辑器

一个使用 Python 和 PySide6 构建的文本编辑器，作为 Sublime Text 的轻量级替代方案。

## 项目特性

### 核心功能
- ✅ 多标签页文件管理
- ✅ 单实例应用（双击文件在现有窗口打开）
- ✅ 语法高亮（Python, Java, JavaScript, SQL, JSON, Kotlin, Markdown）
- ✅ 查找和替换
- ✅ 跨文件搜索（支持文件名和内容搜索）
- ✅ 自动换行
- ✅ 代码格式化（JSON, SQL）
- ✅ 主题切换（深色/浅色）
- ✅ 文件拖放支持
- ✅ 最近文件历史
- ✅ 大文件处理（50MB+）
- ✅ 崩溃恢复（自动保存）
- ✅ 会话恢复（记住上次打开的文件）
- ✅ 编码选择（UTF-8, GBK, GB2312 等）
- ✅ 语言手动切换

### 高级搜索功能
- 文件内容搜索（支持正则表达式）
- 文件名搜索（模糊匹配/精确匹配）
- 区分大小写选项
- 文件类型过滤
- 搜索结果分组显示

## 项目结构

```
publime/
├── ui/                      # UI 组件
│   ├── main_window.py       # 主窗口
│   ├── editor_pane.py       # 编辑器面板
│   ├── tab_widget.py        # 标签页组件
│   ├── dialogs.py           # 对话框（查找、替换、跨文件搜索）
│   └── sekiro.icon          # 应用图标
├── core/                    # 核心功能
│   ├── file_manager.py      # 文件管理
│   ├── search_engine.py     # 搜索引擎
│   ├── syntax_highlighter.py # 语法高亮
│   ├── history_manager.py   # 历史记录管理
│   └── code_completer.py    # 代码补全（基础）
├── themes/                  # 主题系统
│   ├── theme_manager.py     # 主题管理器
│   ├── dark_theme.py        # 深色主题
│   └── light_theme.py       # 浅色主题
├── utils/                   # 工具函数
│   └── language_detector.py # 语言检测
├── tests/                   # 单元测试
├── samples/                 # 示例文件
├── main.py                  # 应用入口
├── build_exe.py             # 打包脚本
├── sql_formatter_new.py     # SQL 格式化器
└── requirements.txt         # Python 依赖
```

## 开发环境设置

### 前置要求

- Python 3.9 或更高版本
- pip（Python 包管理器）

### 安装步骤

1. 克隆仓库：
```bash
git clone <repository-url>
cd publime
```

2. 创建虚拟环境（推荐）：
```bash
python -m venv .venv
```

3. 激活虚拟环境：
   - Windows: `.venv\Scripts\activate`
   - Linux/Mac: `source .venv/bin/activate`

4. 安装依赖：
```bash
pip install -r requirements.txt
```

### 运行应用

```bash
python main.py
```

## 打包成 EXE

### 方法 1：使用打包脚本（推荐）

```bash
python build_exe.py
```

生成的 EXE 文件位于 `dist/Publime.exe`

### 方法 2：手动使用 PyInstaller

```bash
pyinstaller --name=Publime --windowed --icon=ui/sekiro.icon --onefile --clean --add-data="ui/sekiro.icon;ui" main.py
```

### 打包说明

- `--windowed`: 不显示控制台窗口
- `--onefile`: 打包成单个 EXE 文件
- `--icon`: 设置应用图标
- `--add-data`: 包含图标文件到打包中
- `--clean`: 清理临时文件

打包后的 EXE 文件大小约 44MB，包含所有依赖。

## 开发指南

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_dialogs.py

# 运行带覆盖率的测试
pytest --cov=. --cov-report=html

# 运行特定测试类
pytest tests/test_dialogs.py::TestFindInFilesDialog -v
```

### 代码格式化

```bash
# 格式化代码
black .

# 检查代码风格
flake8 .
```

### Git 提交规范

使用语义化提交信息：
- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `test:` 测试相关
- `refactor:` 代码重构
- `chore:` 构建/工具相关

示例：
```bash
git commit -m "feat: Add dual search modes for file search"
git commit -m "fix: Fix search progress indicator"
```

## 依赖项

### 核心依赖
- **PySide6** (6.7.2): Qt for Python UI 框架
- **PyInstaller** (6.18.0): 打包工具

### 开发依赖
- **pytest** (7.4.4): 测试框架
- **pytest-qt** (4.5.0): Qt 测试支持
- **pytest-cov**: 代码覆盖率
- **hypothesis**: 属性测试

## 快捷键

### 文件操作
- `Ctrl+N`: 新建文件
- `Ctrl+O`: 打开文件
- `Ctrl+S`: 保存文件
- `Ctrl+Shift+S`: 另存为
- `Ctrl+Q`: 退出

### 编辑操作
- `Ctrl+Z`: 撤销
- `Ctrl+Y`: 重做
- `Ctrl+X`: 剪切
- `Ctrl+C`: 复制
- `Ctrl+V`: 粘贴

### 搜索操作
- `Ctrl+F`: 查找
- `Ctrl+Shift+F`: 在文件中查找

### 其他
- `Ctrl+Alt+F`: 格式化代码（JSON/SQL）
- `Ctrl+Shift+T`: 切换主题

## 架构说明

### 主题系统
- 基于 QSS（Qt Style Sheets）
- 支持深色和浅色主题
- 主题配置包括：背景色、前景色、选中色、关键字颜色等

### 语法高亮
- 基于 QSyntaxHighlighter
- 支持多种编程语言
- 使用正则表达式匹配关键字、字符串、注释等

### 搜索引擎
- 支持正则表达式搜索
- 支持跨文件搜索
- 支持文件名模糊/精确匹配
- 递归遍历目录

### 文件管理
- 支持多种编码格式
- 大文件优化处理
- 自动保存和崩溃恢复

## 性能优化

- 大文件（>10MB）自动禁用语法高亮
- 大文件（>50MB）显示警告
- 搜索结果限制和分页显示
- 使用 QPlainTextEdit 而非 QTextEdit 提高性能

## 故障排除

### 打包问题
- 确保已安装 PyInstaller: `pip install pyinstaller`
- 确保图标文件存在: `ui/sekiro.icon`
- 如果打包失败，尝试删除 `build` 和 `dist` 目录后重新打包

### 运行问题
- 如果缺少依赖，运行: `pip install -r requirements.txt`
- 如果 Qt 相关错误，尝试重新安装 PySide6: `pip install --force-reinstall PySide6`

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

MIT License

## 作者

Publime 开发团队

## 致谢

- 灵感来源于 Sublime Text
- 使用 PySide6 (Qt for Python) 构建
- 图标来源：ui/sekiro.icon
