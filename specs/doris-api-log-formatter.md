# Spec: Doris-API 日志 → 填充变量 + SQL格式化

> 分支: `spec/doris-api-log-formatter`
> 状态: 待确认

---

## 1. 需求背景

Publime 目前已支持 myBatis 日志格式的"填充变量 + SQL格式化"。用户在编辑器中粘贴两行日志（SQL行 + 参数行），点格式化即可得到可执行SQL。

现需新增对 **doris-api 日志格式** 的支持。该格式的特点是 SQL 跨多行。

---

## 2. 两种日志格式对比

### 2.1 myBatis 格式（已支持）

```
行0: [日志前缀] ==>  Preparing: SELECT ... FROM ... WHERE id = ? AND name = ?
行1: [日志前缀] ==> Parameters: 42(Integer), hello(String)
```

特征：
- 两行，每行有独立的时间戳和日志前缀
- SQL 全部在一行内
- 参数格式为 `value(Type), value(Type)`

### 2.2 doris-api 格式（新需求）

```
行0:  [日志前缀] 执行sql:SELECT COUNT(1) as total FROM (with t_repay_record as (
行1:      SELECT t.task_no, trr.gmt_create, ...
行2:      FROM core_ms.t_repay_record trr
...
行92: order by tltc.enter_lawsuit_date desc) TMP
行93: [日志前缀] 执行参数:["2026-06-30 23:59:59", "2025-05-01 00:00:00", ...]
```

特征：
- SQL 跨多行：首行有 `执行sql:` 前缀 + SQL开头，后续续行是纯 SQL（无日志前缀）
- 参数行在最后一行，有日志前缀 + `执行参数:`
- 参数格式为 JSON 数组 `["value1", "value2", 123]`

### 2.3 共性

两种格式共享一致的**后处理管线**：

```
提取SQL模板 → 去除COUNT包裹 → 提取参数 → 替换?占位符 → SQL格式化
```

---

## 3. 当前代码现状

文件：`core/doris_log_processor.py`

### 3.1 `process_doris_log()` 当前逻辑

```python
lines = text.strip().split('\n')
sql_line = lines[0]      # 假设第0行就是完整SQL
param_line = lines[1]    # 假设第1行就是参数行
```

这个假设对 **myBatis 格式**成立，对 **doris-api 格式**不成立。

doris-api 格式中，`lines[0]` 只有SQL开头，`lines[1]` 是SQL续行而非参数行。当前逻辑会：
1. 丢失第1~92行的SQL内容
2. 把第1行（SQL续行）当参数行解析 → `无法识别的参数格式`

### 3.2 已验证的功能（不需要改动）

以下函数对两种格式**通用**，不需要修改：

| 函数 | 作用 | 改否 |
|---|---|---|
| `extract_sql_from_log()` | 从含前缀的行提取SQL | ❌ |
| `remove_count_wrapper()` | 去除 COUNT 包裹 | ❌ |
| `extract_parameters()` | 自动识别参数格式并提取 | ❌ |
| `replace_parameters()` | 替换 ? 为实际值 | ❌ |
| `is_datetime_param()` / `is_numeric()` | 参数类型判断 | ❌ |

### 3.3 现有测试

- 59 个单元测试全部通过（测试各子函数）
- 3 个集成测试失败 — 原因是测试引用的文件名为 `原始doris日志打印.txt`，实际文件名为 `原始doris-api日志打印.txt`（文件名多了 `-api`），且处理逻辑尚不支持多行SQL

---

## 4. 设计方案

### 4.1 修改范围

**只修改一个函数**：`process_doris_log()` in `core/doris_log_processor.py`

其他所有代码不变。

### 4.2 核心改动：行扫描逻辑

将"固定取第0行=SQL、第1行=参数"改为"扫描所有行，按前缀分类"：

```python
def process_doris_log(text: str) -> tuple[bool, str]:
    lines = text.strip().split('\n')

    sql_parts = []
    param_line = None
    sql_started = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # 检测参数行（独立的日志行，含参数前缀）
        if '执行参数:' in stripped or 'Parameters:' in stripped:
            param_line = stripped
            break  # 参数行之后不再有 SQL 内容

        # 检测 SQL 起始行（含 SQL 前缀的日志行）
        if '执行sql:' in stripped or 'Preparing:' in stripped:
            sql_started = True
            raw = extract_sql_from_log(stripped)
            sql_parts.append(raw)
            continue

        # SQL 续行（无日志前缀的纯 SQL 内容）
        if sql_started:
            sql_parts.append(stripped)

    if not sql_parts:
        return (False, "未找到SQL内容，请确认输入包含 '执行sql:' 或 'Preparing:'")
    if param_line is None:
        return (False, "未找到参数行，请确认输入包含 '执行参数:' 或 'Parameters:'")

    try:
        full_sql = ' '.join(sql_parts)
        processed_sql = remove_count_wrapper(full_sql)
        params = extract_parameters(param_line)
        executable_sql = replace_parameters(processed_sql, params)
        formatted_sql = format_sql(executable_sql)
        return (True, formatted_sql)
    except ValueError as e:
        return (False, str(e))
    except Exception as e:
        return (False, f"SQL处理异常: {str(e)}")
```

### 4.3 兼容性分析

| 场景 | 当前行为 | 新行为 | 是否兼容 |
|---|---|---|---|
| myBatis 两行格式（SQL全在一行） | ✅ 正确 | ✅ 正确（sql_parts=[单行SQL]） | ✅ 完全兼容 |
| doris-api 多行格式 | ❌ 失败 | ✅ 正确 | ✅ 新支持 |
| SQL行在前、参数行在后 | ✅ 正确 | ✅ 正确 | ✅ 完全兼容 |
| 含空行 | ❌ 可能导致下标偏移 | ✅ 跳过空行 | ✅ 更健壮 |
| 无参数行 | ❌ 报错 | ❌ 报错（明确提示） | ✅ 一致 |
| 无SQL行 | ❌ 报错 | ❌ 报错（明确提示） | ✅ 一致 |

### 4.4 参数行位置说明

当前逻辑：`param_line = lines[1]`
新逻辑：`param_line = 含参数前缀的行的内容`

对于 myBatis 格式：参数行恰好在第1行 → 行为不变
对于 doris-api 格式：参数行在第93行 → 正确找到

---

## 5. 测试修正

`tests/test_doris_log_processor.py` 中需修正两处：

### 5.1 文件名修正

```python
# 修正前
path = os.path.join(SAMPLES_DIR, "原始doris日志打印.txt")

# 修正后
path = os.path.join(SAMPLES_DIR, "原始doris-api日志打印.txt")
```

同理修正 `expected_output` fixture 中的 `处理doris日志之后的效果.sql` → `处理doris-api日志之后的效果.sql`。

### 5.2 预期行为

集成测试预期：`process_doris_log(sample_input)` 返回 `(True, formatted_sql)`，且格式化结果与 `处理doris-api日志之后的效果.sql` **内容等价**（忽略关键字大小写差异）。

---

## 6. 验收标准

### 6.1 新功能验证

- [ ] 将 `samples/原始doris-api日志打印.txt` 粘贴到 Publime 编辑器
- [ ] 点击格式化
- [ ] 输出内容与 `samples/处理doris-api日志之后的效果.sql` 一致（忽略关键字大小写）

### 6.2 历史功能回归

- [ ] 将 `samples/原始myBatis日志打印.txt` 粘贴到 Publime 编辑器
- [ ] 点击格式化
- [ ] 输出内容与 `samples/处理myBatis日志之后的效果.sql` 一致（忽略关键字大小写）

### 6.3 SQL格式化回归（自测须知要求）

以下 6 个 sample 格式化后必须与对应的 target 完全一致：

- [ ] `complex_test.sql` → `complex_test_target.sql`
- [ ] `sample_1.sql` → `sample_1_target.sql`
- [ ] `sample_2.sql` → `sample_2_target.sql`
- [ ] `sample_3.sql` → `sample_3_target.sql`
- [ ] `sample_4.sql` → `sample_4_target.sql`
- [ ] `sample_5.sql` → `sample_5_target.sql`
- [ ] `sample_6.sql` → `sample_6_target.sql`

### 6.4 单元测试

- [ ] `pytest tests/test_doris_log_processor.py` 全部 62 个测试通过（59 单元 + 3 集成）

---

## 7. 待确认问题（已回复）

### Q1: "完全一致"的判定标准 ✅ 已回复

**回复**：请把当前的"宽松匹配"用文字描述下，写到"自测须知"里，看能不能接受。

**当前测试代码的宽松匹配逻辑（`normalize()` 函数）**：

| 步骤 | 操作 | 效果 |
|---|---|---|
| 1 | 去除首尾空白 | 去掉整段文本头尾的空格、换行 |
| 2 | 将所有连续空白（空格、换行、制表符）压缩为一个空格 | `SELECT  *\nFROM` → `SELECT * FROM` |
| 3 | 全部转为大写 | `select` → `SELECT` |
| 4 | 去除函数名与左括号之间的空格 | `COUNT (` → `COUNT(` |
| 5 | 去除左括号后的空格 | `( SELECT` → `(SELECT` |
| 6 | 去除右括号前的空格 | `value )` → `value)` |
| 7 | 规范化 `! =` 为 `!=` | `! =` → `!=` |

执行 normalize 后，如果实际输出和预期输出**字符串完全相等**，就算通过。

换句话说：**只要实际输出的每个 SQL 单词（关键字、表名、字段名、值）与预期一致，且出现顺序相同，就算通过。换行位置不同、缩进不同、关键字大小写不同、括号周围空格不同，都不算失败。**

此逻辑适用于 `原始doris-api日志打印.txt` 和 `原始myBatis日志打印.txt` 这两个日志类回归项。其余 7 个 sample 回归项仍然需要"完全一致"（但忽略关键字大小写）。

### Q2: "SQL续行"是什么意思？ ✅ 已解释

见上文 2.2 节示意图。doris-api 日志中，第 1~92 行是纯 SQL 内容（无日志前缀），它们是第 0 行 SQL 的延续。拼接方式：将每行 `strip()` 后用空格 `' '` 连接成一个完整 SQL 字符串，再交给 `format_sql` 重新格式化。format_sql 会自己决定换行和缩进，所以中间用什么连字符不影响最终输出。

### Q3: 分支策略 ✅ 已确认

当前 `spec/doris-api-log-formatter` 分支。等明确确认可以改代码后再动手。
