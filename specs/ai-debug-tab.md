# Spec: AI 排障功能

> 分支: `spec/ai-debug-tab`
> 状态: 待审阅

---

## 1. 需求背景

用户在 debug / 造数时，经常遇到"SQL 预期能查出某条数据，但实际上没查到"的情况。需要手动逐条检查 JOIN 条件、WHERE 子句，排查效率低。

新增一个 AI 排障工具：用户给出 SQL + 自然语言描述（期望查到什么数据），工具调用 DeepSeek V4 Pro，自动分析 Doris 数据库中的实际数据，定位根因，并给出修复 SQL。

---

## 2. 用户故事

1. 用户在编辑器中粘贴一段 doris-api 日志（或直接写 SQL），无需手动格式化
2. 打开「AI 排障」对话框，SQL 自动填入（如果编辑器中有选中文本）
3. 用户用自然语言补充："我期望借据号 LN20251010162446951480 有签约文件，但没查到"
4. 点击「开始排查」
5. 工具流式展示 DeepSeek 的分析过程，自动执行查询，最终输出：
   - 根因：哪个表缺数据 / 哪个关联条件不满足
   - 修复方案：INSERT 或 UPDATE 语句

---

## 3. 架构设计

```
┌──────────────────────────┐    ┌──────────────────────┐
│     Publime UI           │    │   publime/config.json │
│                          │    │  (gitignored)         │
│  ┌────────────────────┐  │    │                      │
│  │  AI 排障对话框      │  │    │  deepseek_api_key    │
│  │                    │  │    │  doris_host           │
│  │  输入区:           │  │    │  doris_port           │
│  │   - SQL 文本框     │  │    │  doris_user           │
│  │   - 期望描述       │  │    │  doris_password       │
│  │   - 开始按钮       │  │    │  doris_database       │
│  │                    │  │    └──────────────────────┘
│  │  输出区:           │  │
│  │   - 流式对话       │  │    ┌──────────────────────┐
│  │   - 最终结论       │  │    │   DeepSeek V4 Pro     │
│  └────────────────────┘  │    │   (HTTPS API)         │
│                          │    └──────────┬───────────┘
└──────────────────────────┘               │
         │                                 │ SQL 语句
         │ Doris 只读查询                  │ (不含密码)
         ▼                                 ▼
┌──────────────────┐              ┌──────────────────┐
│   Doris (测试)    │◄─────────────│   MCP/工具调用    │
│   SELECT / DESC   │   返回结果    │  执行 SQL → 返回  │
└──────────────────┘              └──────────────────┘
```

核心安全原则：**账号密码只存在本地 config.json，绝不发送给大模型**。大模型产出的是 SQL 文本，由工具本地执行后，只把**查询结果**返回给大模型。

---

## 4. 配置文件

### 4.1 位置与格式

`publime/config.json`（已加入 .gitignore）

```json
{
  "deepseek": {
    "api_key": "sk-xxx",
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-v4-pro"
  },
  "doris": {
    "host": "10.x.x.x",
    "port": 9030,
    "user": "readonly_user",
    "password": "xxx",
    "database": "default_db",
    "catalog": "default_catalog"
  }
}
```

### 4.2 配置管理

- 首次启动时自动生成模板 config.json
- UI 提供「设置」入口，可弹窗编辑
- 程序启动时读取，不做本地缓存超时

---

## 5. Doris 连接方案

采用 PyMySQL 连接 Doris FE（兼容 MySQL 协议，端口 9030）：

```
pip install pymysql
```

核心操作：
- `SELECT ...` — 执行 LLM 生成的查询
- `DESC table_name` — 查询表结构
- `SHOW TABLES` — 列出可用表

所有查询通过只读账号执行。**代码层面强制校验**：`doris_connector.py` 在执行前用正则匹配 SQL 首词，仅允许 `SELECT`、`DESC`、`DESCRIBE`、`SHOW` 开头的语句，其余一律拒绝执行并返回错误。此外，**不允许多语句 SQL**（含分号的复合语句），每次只执行一条 SQL。

---

## 6. DeepSeek 调用方案

### 6.1 SDK

使用官方 `openai` 兼容 SDK：

```
pip install openai
```

```python
from openai import OpenAI

client = OpenAI(
    api_key=config["deepseek"]["api_key"],
    base_url=config["deepseek"]["base_url"],
)

response = client.chat.completions.create(
    model=config["deepseek"]["model"],
    messages=[...],
    stream=True,  # 流式
)
```

### 6.2 流式输出

DeepSeek API 支持 SSE (Server-Sent Events) 流式输出。PySide6 实现方式：

1. 工作线程（QThread）调用 `client.chat.completions.create(stream=True)`
2. 每收到一个 token chunk，通过 signal 发送到主线程
3. 主线程更新 UI text widget

**结论：做流式**。用 QThread + Signal 实现，工作量与非流式差距不大（约多 20~30 行），收益明显——长达 10 轮的推理过程，看不到中间输出会让用户焦虑。

---

## 7. 多轮对话机制

### 7.1 方案：Function Calling（Tool Calls）

**DeepSeek API 支持 function calling**，格式兼容 OpenAI 标准。官方文档：[api-docs.deepseek.com/guides/tool_calls](https://api-docs.deepseek.com/guides/tool_calls)

比 prompt 约定方案更可靠：LLM 不会"忘记"生成 SQL 标记，工具调用的参数格式由 JSON Schema 约束。

定义两个工具：

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "execute_sql",
            "description": "在 Doris 数据库上执行一条只读 SQL（SELECT / DESC / SHOW TABLES）。"
                           "只用于查询数据和表结构，禁止 DDL/DML。",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "要执行的 SQL 语句，仅限 SELECT、DESC、SHOW TABLES"
                    },
                    "reason": {
                        "type": "string",
                        "description": "为什么需要执行这条 SQL（简要说明排查思路）"
                    }
                },
                "required": ["sql", "reason"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "report_finding",
            "description": "找到根因后，报告排查结论和修复方案，结束排查。"
                           "只有在确定根因后才能调用此函数。",
            "parameters": {
                "type": "object",
                "properties": {
                    "root_cause": {
                        "type": "string",
                        "description": "【根因】为什么没查到数据（哪个表缺数据/哪个条件不满足）"
                    },
                    "fix_sql": {
                        "type": "string",
                        "description": "【修复】基于 MySQL 语法的 INSERT 或 UPDATE 语句，用于写入 MySQL 源表。"
                                       "可以多条，用分号分隔。"
                                       "Doris 是查询端，通过 Flink 从 MySQL 同步数据。"
                                       "因此修复 SQL 中禁止出现 op_flag / sr_update 等 Doris 专属字段。"
                                       "如果无法给出修复 SQL，填空字符串或说明原因（如'无法确定修复方案'），不要编造。"
                    }
                },
                "required": ["root_cause", "fix_sql"],
                "additionalProperties": False
            }
        }
    }
]
```

### 7.2 System Prompt

```
你是一个 Doris 数据库排障专家。用户提供一段 SQL 和期望查到但没查到的数据描述。
本工具的前提：SQL 逻辑是正确的，问题出在数据侧（缺数据 / 数据不对）。因此修复方案通常是 INSERT/UPDATE 语句。

你可以使用 execute_sql 工具在 Doris 上执行只读查询（SELECT / DESC / SHOW TABLES）。
每次只能执行一条 SQL，不要在一次调用中包含多条语句。
分析数据后，当你确定根因时，使用 report_finding 报告结论。

排查策略：
- 先查看涉及的表结构（DESC）
- 从 WHERE 条件和 JOIN 关联条件入手
- 每次查询尽量精炼（SELECT 返回行数 ≤ 20）
- 不要生成 CREATE/ALTER/DROP 语句

report_finding 的 fix_sql 字段：
- 给出的 INSERT 或 UPDATE 必须基于 MySQL 语法，不是 Doris
- Doris 是查询端，通过 Flink 从 MySQL 同步数据，写入只能在 MySQL 源表上进行
- 禁止出现 op_flag / sr_update 等 Doris 专属字段。DESC 结果的字段中去掉这两列，就是 MySQL 的字段
- 如果确实无法给出修复 SQL，填空字符串或说明原因，不要编造
```

### 7.3 对话流程（基于 Function Calling）

```
轮次 1:
  LLM → tool_calls: execute_sql("DESC core_ms.t_repay_record", reason="查看表结构")
  Tool → 执行 DESC
  Tool → 在 messages 中追加 assistant(tool_calls) + tool(result)
  LLM → tool_calls: execute_sql("SELECT * FROM ... WHERE ...", reason="检查关联条件")
  Tool → 执行 SELECT，返回结果

...每轮中 LLM 可能调用 0~N 个 tool...

终止:
  LLM → tool_calls: report_finding(root_cause="...", fix_sql="...")
  Tool → 检测到 report_finding 调用 → 触发终止
```

注意：每轮 LLM 可能同时返回多个 `tool_calls`。例如一次同时请求查两张表的结构。这种情况应并行执行，不算多轮。

### 7.4 Tool Result 返回格式

`execute_sql` 执行后，结果以文本形式返回给 LLM。格式规则：

| SQL 类型 | 返回格式 |
|---|---|
| `SELECT` | Markdown 表格（列名 + 前 20 行）。如果总行数 > 20，末尾追加 `... 共 N 行（已截断）` |
| `DESC` / `DESCRIBE` | Markdown 表格，不限制行数 |
| `SHOW TABLES` | Markdown 表格，不限制行数 |
| 空结果（0 行） | `查询返回 0 行` |
| 执行错误 | `执行错误: {error_message}` |
| SQL 被拦截（非 SELECT/DESC/SHOW） | `拒绝执行：仅允许 SELECT / DESC / SHOW TABLES 语句` |
| 多语句 SQL | `拒绝执行：每次只能执行一条 SQL 语句` |

示例（SELECT 结果）：

```
| id | name | status |
|---|---|---|
| 1 | 张三 | active |
| 2 | 李四 | inactive |

... 共 158 行（已截断）
```

### 7.5 终止条件

满足以下任一条件时暂停，询问用户：

1. LLM 调用了 `report_finding` → 给出根因 + 修复 SQL
2. 达到 20 轮 LLM 调用上限（一轮可能包含多次 tool call）
3. 达到总轮次上限 40 轮 → 强制结束，展示已有结论

用户选择（条件 1、2 时）：
- **「确认完成」** → 结束，展示结论
- **「继续排查」** → 重置当前轮次计数（不重置总轮次），追加消息 "请继续排查是否还有其他原因"，继续对话

### 7.6 LLM 纯文本回复处理

如果 LLM 返回纯文本内容（不调用任何 tool），正常展示给用户，同时计入轮次。如果连续 2 轮都没调用任何 tool，自动追加提示消息："请使用 execute_sql 查询数据来验证你的假设"。

### 7.7 SQL 输入自动识别

用户可以在 SQL 输入框中直接粘贴**原始日志**（myBatis 或 doris-api 格式）。

点击「开始排查」时，代码自动检测：
- 如果包含 `执行sql:` / `Preparing:` / `执行参数:` / `Parameters:` → 调用已有 `process_doris_log()` 转换为完整 SQL
- 如果已是纯 SQL → 直接使用

**不需要**用户手动点击「格式化为SQL」按钮。

---

## 8. UI 设计

### 8.1 方案：独立对话框（Modeless）

不再使用 tab 方式，改为**独立对话框**，理由：
- 无需改造 `tab_widget.py`，零回归风险
- 用户可同时查看编辑器中的 SQL 和 AI 排障的排查过程（modeless 窗口自由拖动）
- 通过菜单栏「工具 → AI 排障」（`Ctrl+Shift+D`）打开
- 如果编辑器中有选中文本，自动填入 SQL 输入框

### 8.2 对话框结构

```
┌─────────────────────────────────────────────────────┐
│  AI 排障 - Publime                          [_][□][X]│
├─────────────────────────────────────────────────────┤
│  ┌─ SQL 输入 ─────────────────────────────────┐    │
│  │  粘贴 SQL 或日志（自动识别并转换）           │    │
│  │  ┌──────────────────────────────────────┐  │    │
│  │  │ SELECT ... FROM ... WHERE ...        │  │    │
│  │  │ (可编辑)                              │  │    │
│  │  └──────────────────────────────────────┘  │    │
│  └──────────────────────────────────────────┘    │
│                                                    │
│  ┌─ 期望查到什么 ─────────────────────────────┐    │
│  │  ┌──────────────────────────────────────┐  │    │
│  │  │ 我希望借据号 XXX 有签约文件...         │  │    │
│  │  └──────────────────────────────────────┘  │    │
│  └──────────────────────────────────────────┘    │
│                                                    │
│  [⚙ 设置]                          [▶ 开始排查]    │
│                                                    │
│  ┌─ 排查过程 ─────────────────────────────────┐    │
│  │  (流式输出，QTextBrowser，只读)             │    │
│  └──────────────────────────────────────────┘    │
│                                                    │
│  [停止]  [确认完成]  [继续排查]                      │
└─────────────────────────────────────────────────────┘
```

### 8.3 交互细节

| 控件 | 说明 |
|---|---|
| SQL 输入框 | QPlainTextEdit，可直接粘贴 SQL 或 doris-api/myBatis 日志。「开始排查」时自动识别并调用 `process_doris_log()` 转换 |
| 期望描述 | QPlainTextEdit（约 3 行高度），自然语言 |
| 排查过程 | QTextBrowser，只读，流式追加。不同角色用不同颜色区分 |
| 「开始排查」按钮 | 禁用输入区，启动排查 |
| 「停止」按钮 | 终止排查，保留已输出内容 |
| 「确认完成」/「继续排查」 | 终止条件满足后显示 |
| 对话框打开时 | 如果编辑器中有选中文本，自动填入 SQL 输入框 |

### 8.4 菜单入口

在菜单栏「工具」菜单下新增：
- **AI 排障** (`Ctrl+Shift+D`) → 打开模型对话框

```python
# main_window.py
ai_debug_action = QAction("AI 排障(&A)", self)
ai_debug_action.setShortcut(QKeySequence("Ctrl+Shift+D"))
ai_debug_action.triggered.connect(self.open_ai_debug_dialog)
tool_menu.addAction(ai_debug_action)
```

### 8.5 对话框单例约束

AI 排障对话框为**单例**：同一时间只允许一个实例。如果用户再次点击菜单或快捷键，激活已有窗口（raise + setFocus），不创建新实例。

### 8.6 配置编辑弹窗（config_dialog.py）

点击对话框中的「⚙ 设置」按钮，弹出 Modal 对话框编辑 `config.json`。

```
┌─────────────────────────────────────────┐
│  AI 排障 - 设置                    [X]   │
├─────────────────────────────────────────┤
│  DeepSeek API                           │
│  ┌─────────────────────────────────┐   │
│  │ API Key:  [sk-xxx            ]  │   │
│  │ Base URL: [https://api.deepseek.com] │
│  │ Model:    [deepseek-v4-pro   ]  │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Doris 数据库                           │
│  ┌─────────────────────────────────┐   │
│  │ Host:     [10.x.x.x         ]  │   │
│  │ Port:     [9030              ]  │   │
│  │ User:     [readonly_user     ]  │   │
│  │ Password: [••••••            ]  │   │
│  │ Database: [default_db        ]  │   │
│  │ Catalog:  [default_catalog   ]  │   │
│  └─────────────────────────────────┘   │
│                                         │
│              [取消]  [保存]              │
└─────────────────────────────────────────┘
```

| 字段 | 控件 | 校验 |
|---|---|---|
| API Key | QLineEdit（密码模式，可切换显示） | 非空 |
| Base URL | QLineEdit | 非空，合法 URL |
| Model | QLineEdit | 非空 |
| Host | QLineEdit | 非空 |
| Port | QSpinBox（范围 1-65535） | 默认 9030 |
| User | QLineEdit | 非空 |
| Password | QLineEdit（密码模式） | 非空 |
| Database | QLineEdit | 非空 |
| Catalog | QLineEdit | 可选，默认 `default_catalog` |

保存时：校验通过 → 写入 `config.json` → 弹窗提示"保存成功"。校验失败 → 高亮错误字段，不关闭弹窗。

---

## 9. 异常处理

| 场景 | 处理 |
|---|---|
| config.json 不存在 | 首次启动弹窗引导填写配置 |
| config.json 缺少字段 | 弹窗提示具体缺失字段 |
| DeepSeek API 超时/报错 | 在输出区显示红色错误信息，提供重试按钮 |
| Doris 连接失败 | 在输出区显示连接错误详情，不传给 LLM |
| Doris 查询超时（>30s） | 取消查询，告知 LLM 超时 |
| LLM 返回纯文本（不调用 tool） | 正常展示，计入轮次；连续 2 轮无 tool 调用则追加提示 |
| LLM 返回的不是有效 tool_call | 忽略本轮，追加 "请使用 execute_sql 或 report_finding 工具" 后重试 |
| LLM 生成的 SQL 包含 DDL/DML | 代码层拦截，返回 "拒绝执行：仅允许 SELECT/DESC/SHOW TABLES" |
| LLM 生成的 SQL 包含多条语句 | 代码层拦截，返回 "拒绝执行：每次只能执行一条 SQL 语句" |
| 用户手动停止 | 终止 LLM 请求和 Doris 查询 |
| SELECT 返回数据超过 20 行 | 截断为前 20 行 + `... 共 N 行（已截断）` |

---

## 10. 文件结构

```
publime/
├── config.json                    # 新增，gitignored，LLM + Doris 配置
├── core/
│   ├── ai_debug/
│   │   ├── __init__.py
│   │   ├── config_manager.py      # 配置读取/写入/校验
│   │   ├── doris_connector.py     # Doris 查询封装
│   │   ├── deepseek_client.py     # DeepSeek API 封装（含流式）
│   │   └── debug_session.py       # 多轮对话编排
├── ui/
│   ├── ai_debug_dialog.py         # AI 排障对话框（替代原计划 ai_debug_tab.py）
│   ├── config_dialog.py           # 配置编辑弹窗
│   └── main_window.py             # 修改：菜单栏新增「AI 排障」入口，open_ai_debug_dialog()
├── .gitignore                     # 修改：添加 config.json
└── requirements.txt               # 修改：添加 pymysql, openai
```

---

## 11. 开发阶段

| 阶段 | 内容 | 预计影响 |
|---|---|---|
| Phase 1 | config.json 管理 + .gitignore | 基础设施 |
| Phase 2 | Doris 连接器（PyMySQL） | 基础设施 |
| Phase 3 | DeepSeek 客户端（含流式） | 核心逻辑 |
| Phase 4 | 多轮对话编排（debug_session） | 核心逻辑 |
| Phase 5 | AI 排障对话框 UI | UI |
| Phase 6 | 配置编辑弹窗 | UI |
| Phase 7 | 集成到主窗口（菜单入口 + 对话框调用） | 集成 |
| Phase 8 | 异常处理 + 边界情况 | 健壮性 |
| Phase 9 | 测试 + 回归 | 质量 |

---

## 12. 决策记录

| 问题 | 决策 | 理由 |
|---|---|---|
| 「格式化为SQL」按钮 | 不做按钮，自动识别 | 用户粘贴日志后点开始排查，代码自动 detect 并调用 `process_doris_log()` |
| 期望描述文本框 | 多行 QPlainTextEdit（~3 行高度） | 自然语言描述可能 2~3 行 |
| DeepSeek Function Calling | **支持**，使用 tool_calls 方案 | 官方文档确认，比 prompt 约定更可靠 |
| 模型选择 | `deepseek-v4-pro` | 用户指定的 V4 Pro |
| 流式输出 | 做 | QThread + Signal，工作量与非流式差距不大 |
| SQL 安全 | 代码层强制校验（正则匹配首词） | 仅靠 prompt 引导不可靠，LLM 可能幻觉出 DDL/DML |
| 多语句 SQL | 不允许，每次只执行一条 | 避免注入风险，简化实现 |
| 轮次上限 | 单轮 20 次，总上限 40 次 | 每次只执行一条 SQL，需要更多轮次；总上限防止无限循环 |
| SELECT 结果截断 | 前 20 行 | 控制上下文窗口消耗 |
| 对话框实例 | 单例 | 避免多个排查会话同时写 Doris |
| fix_sql 字段 | 允许空字符串或说明原因 | 避免迫使 LLM 编造修复 SQL |

---

## 13. 验收标准

- [ ] 首次启动弹窗引导填写 config.json
- [ ] 通过菜单「工具 → AI 排障」或 `Ctrl+Shift+D` 打开对话框
- [ ] 对话框为单例，重复打开时激活已有窗口
- [ ] 编辑器中选中文本时，打开对话框自动填入 SQL
- [ ] 粘贴 myBatis / doris-api 日志，点开始排查自动转换为 SQL
- [ ] 输入 SQL + 期望描述，点击开始排查，流式展示 LLM 分析
- [ ] LLM 生成的 SELECT 自动在 Doris 执行，结果显示在对话中
- [ ] DDL/DML/多语句 SQL 被代码层拦截，不执行
- [ ] SELECT 结果截断为前 20 行，DESC/SHOW 不截断
- [ ] 多轮对话正确传递上下文
- [ ] 满足终止条件后显示「确认完成」「继续排查」按钮
- [ ] 选择「继续排查」重置当前轮次计数（总轮次不重置）
- [ ] 总轮次达到 40 次后强制结束
- [ ] LLM 连续 2 轮纯文本回复时自动追加提示
- [ ] 「停止」按钮可终止当前流程
- [ ] Doris 连接失败 / API 超时等异常有友好提示
- [ ] 配置编辑弹窗可正常编辑和保存配置
- [ ] config.json 不会被提交到 git
- [ ] 已有功能（SQL 格式化、doris 日志处理）不受影响

---

## 14. 技术设计

### 14.1 线程模型

排查流程涉及阻塞操作（HTTP API 调用、数据库查询），必须在工作线程执行，避免冻结 UI。

```
┌─ 主线程 (UI) ─────────────────────┐    ┌─ 工作线程 (QThread) ────────┐
│                                    │    │                             │
│  ai_debug_dialog.py                │    │  debug_session.run()        │
│  - 控件渲染、流式追加               │    │  ├─ deepseek_client.chat() │
│  - Signal → slot 更新 QTextBrowser │◄───│  ├─ doris_connector.query() │
│  - 「停止」→ 设置 stop_flag        │───▶│  ├─ 轮次计数 & 终止判断      │
│                                    │    │  └─ emit signal 到主线程     │
└────────────────────────────────────┘    └─────────────────────────────┘
```

**信号定义**（在 `DebugWorker` 中，继承 `QObject`，moveToThread）：

| 信号 | 参数 | 说明 |
|---|---|---|
| `thinking` | `str` | LLM 回复的文本 delta（流式） |
| `tool_call_start` | `str` (tool_name), `str` (reason 或摘要) | LLM 发起一个新的 tool 调用 |
| `tool_call_result` | `str` (tool_name), `str` (result 摘要) | tool 执行完毕，显示结果 |
| `round_count` | `int` (current), `int` (max) | 轮次进度 |
| `finding_ready` | `dict` ({root_cause, fix_sql}) | 排查完成，展示结论 |
| `error` | `str` | 可恢复的错误（API 超时等） |
| `done` | — | 流程结束（无论成功/失败/停止） |

**停止机制**：工作线程每轮开始前检查 `stop_flag`（`threading.Event`），若被设置则立即终止。

### 14.2 模块接口

#### `core/ai_debug/config_manager.py`

```python
class ConfigManager:
    CONFIG_PATH = Path("publime/config.json")

    @staticmethod
    def load() -> dict:
        """读取 config.json，校验必填字段，缺失则抛 ConfigError"""

    @staticmethod
    def save(config: dict) -> None:
        """写入 config.json"""

    @staticmethod
    def template() -> dict:
        """返回默认模板"""

class ConfigError(Exception):
    """配置相关异常，携带缺失字段列表"""
```

#### `core/ai_debug/doris_connector.py`

```python
class DorisConnector:
    def __init__(self, config: dict):
        """config = config["doris"] 子字典"""

    def connect(self) -> None:
        """建立 pymysql 连接，失败抛 DorisError"""

    def close(self) -> None:
        """关闭连接"""

    def execute(self, sql: str) -> str:
        """
        校验 → 执行 → 格式化结果。
        1. 正则校验 SQL 首词，拦截非法语句 → 返回错误字符串
        2. 执行查询，cursor.fetchmany(21) 取前 21 行
        3. 按 §7.4 格式化为字符串返回
        """

class DorisError(Exception):
    """连接/查询异常"""
```

#### `core/ai_debug/deepseek_client.py`

```python
class DeepSeekClient:
    def __init__(self, config: dict):
        """config = config["deepseek"] 子字典，初始化 OpenAI client"""

    def chat(self, messages: list, tools: list, stream_callback: Callable[[str], None]) -> dict:
        """
        发起一次 chat completion（非流式），返回完整 response dict。
        如果 response 包含 tool_calls，返回 {"tool_calls": [...]}。
        否则返回 {"content": "..."}。
        """

    def chat_stream(self, messages: list, tools: list, delta_callback: Callable[[str], None]) -> dict:
        """
        发起流式 chat completion。
        每收到一个 delta.content，调用 delta_callback(delta)。
        最终返回合并后的完整 response dict（含 tool_calls 或 content）。
        """
```

> 注：流式和非流式二选一实现即可。流式版本在收到完整 response 后提取 tool_calls 再返回。

#### `core/ai_debug/debug_session.py`

```python
class DebugSession:
    """
    编排一次完整的排查对话。
    由 DebugWorker 在工作线程中调用。
    """

    def __init__(self, client: DeepSeekClient, connector: DorisConnector):
        ...

    def run(self, sql: str, expectation: str,
            stream_callback: Callable[[str], None],
            tool_callback: Callable[[str, str], None],
            result_callback: Callable[[str, str], None],
            stop_event: threading.Event) -> dict | None:
        """
        主循环：
        1. 构建初始 messages（system + user）
        2. 循环：
           a. 调用 client.chat_stream() 流式输出
           b. 如果 stop_event.is_set() → 返回 None
           c. 如果 content → 累计到缓冲区，回调 stream_callback
           d. 如果 tool_calls → 并行执行每条 SQL
              - 对每条 tool_call：回调 tool_callback(name, reason)
              - execute_sql → connector.execute(sql)
              - report_finding → 标记结束，回调 result_callback，返回 {"root_cause": ..., "fix_sql": ...}
              - 回调 result_callback(name, 摘要)
           e. 轮次 +1，检查终止条件
           f. 如果连续 2 轮无 tool_call → 追加提示消息
        3. 终止 → 返回 findings 或 None
        """

    def _build_initial_messages(self, sql: str, expectation: str) -> list:
        """构建 system + user messages"""

    def _format_tool_result(self, sql: str, result: str) -> dict:
        """将 execute_sql 结果包装为 tool result message"""

    def _check_termination(self, round_num: int, total_rounds: int) -> str | None:
        """检查终止条件，返回 None/hit_limit/report_found"""
```

#### `ui/ai_debug_dialog.py`

```python
class AiDebugDialog(QDialog):
    """单例对话框。详见 §8.2 / §8.3"""

    # 流式显示
    def _on_stream_delta(self, text: str):
        """追加 text 到排查过程 QTextBrowser"""

    def _on_tool_call_start(self, tool_name: str, reason: str):
        """显示 '🔍 正在执行: {reason}' """

    def _on_tool_call_result(self, tool_name: str, result_summary: str):
        """显示查询结果摘要（截断后）"""

    def _on_round_count(self, current: int, max_rounds: int):
        """更新轮次进度提示"""

    def _on_finding_ready(self, finding: dict):
        """流式输出结束，展示结论面板，显示「确认完成」「继续排查」"""

    def _on_error(self, msg: str):
        """红色显示错误信息"""

    def _on_done(self):
        """恢复按钮状态"""

    def _on_start_clicked(self):
        """开始排查：禁用输入 → 启动 DebugWorker 线程"""

    def _on_stop_clicked(self):
        """设置 stop_event"""

    def _on_confirm_clicked(self):
        """用户确认完成，关闭结论面板"""

    def _on_continue_clicked(self):
        """用户选择继续排查，重置当前轮次计数，追加消息，继续循环"""
```

### 14.3 完整调用链

```
用户点击「开始排查」
  │
  ├─ AiDebugDialog._on_start_clicked()
  │   ├─ 检测 SQL 输入，自动调用 process_doris_log() 转换
  │   ├─ 创建 DebugWorker(QObject)，moveToThread
  │   ├─ 连接 signals → slots
  │   └─ 启动线程，worker 开始 run()
  │
  ▼
DebugWorker.run()  [工作线程]
  │
  ├─ 实例化 DebugSession(DeepSeekClient, DorisConnector)
  └─ session.run(sql, expectation, callbacks, stop_event)
       │
       ├─ 构建 messages: [system_prompt, user_input]
       │
       └─ 循环:
            │
            ├─ stop_event 检查
            ├─ client.chat_stream(messages, tools, delta_cb)
            │   └─ delta_cb → signal → UI 流式追加
            │
            ├─ 解析 response:
            │   ├─ 有 tool_calls? → 并行执行每个 tool:
            │   │   ├─ execute_sql → connector.execute() → 格式化
            │   │   └─ report_finding → 标记终止，记录结论
            │   └─ 只有 content? → 纯文本，计入轮次，检查连续 2 轮
            │
            ├─ 追加 assistant + tool messages 到 history
            ├─ 检查终止条件 → 需要暂停? → break
            └─ 继续下一轮
       │
       └─ 返回 findings / None
  │
  ▼
DebugWorker 完成后 emit finding_ready / done
  │
  ▼
AiDebugDialog._on_finding_ready(finding)  [主线程]
  │
  ├─ 显示结论面板（根因 + 修复 SQL）
  └─ 用户交互：确认完成 / 继续排查
```

### 14.4 错误传递

```
工作线程异常
  │
  ├─ DeepSeek API 超时/网络错误
  │   └─ 捕获异常 → emit error("DeepSeek API 超时，请检查网络后重试")
  │       用户可点「开始排查」重试整个流程
  │
  ├─ Doris 连接失败
  │   └─ 捕获 DorisError → emit error("Doris 连接失败: {host}:{port}")
  │       （错误详情不传给 LLM，只显示在 UI）
  │
  ├─ Doris 查询超时（>30s）
  │   └─ 设置 conn timeout 或手动取消 → emit error("Doris 查询超时")
  │       后续：追加 system 消息 "上次查询超时，请优化查询条件"
  │
  └─ 用户「停止」
       └─ stop_event.set() → 工作线程检测到 → return None → emit done
```

**UI 层的错误恢复策略**：
- 「重试」= 从头开始重新创建 Session，不清空历史输出
- 「停止后重新排查」= 清空历史，全新开始
- 配置问题（config.json 缺失/损坏）→ 不启动工作线程，直接弹 ConfigDialog
