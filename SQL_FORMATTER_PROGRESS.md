# SQL 格式化器改进进度报告

## 已完成的改进 ✅

### 1. 分号重复问题 ✅
- **问题**: 每次格式化都会追加分号
- **解决方案**: 在所有 format 函数中，先移除分号 (`statement.rstrip(';').strip()`)，然后在最后统一添加
- **状态**: 已修复

### 2. ON DUPLICATE KEY UPDATE 格式化 ✅
- **问题**: ON DUPLICATE KEY UPDATE 没有换行并缩进
- **解决方案**: 
  - 在 `format_insert()` 中检测 ON DUPLICATE KEY UPDATE
  - 将其分离并格式化为单独的行
  - UPDATE 部分的赋值语句缩进 2 个空格
- **状态**: 已实现并测试通过

### 3. CASE 语句格式化 ✅
- **问题**: CASE 语句没有每个 WHEN 单独一行
- **解决方案**:
  - 改进 `format_case_expression()` 函数
  - 每个 WHEN/THEN 单独一行并缩进
  - 在 UPDATE 和 SELECT 中正确调用
- **状态**: 已实现，基本功能正常

### 4. INSERT INTO ... SELECT 支持 ✅
- **问题**: INSERT INTO ... SELECT 被错误解析为 VALUES
- **解决方案**:
  - 在 `format_insert_basic()` 中先检测 SELECT 关键字
  - 使用独立的正则表达式匹配 INSERT INTO ... SELECT
  - 格式化 SELECT 部分
- **状态**: 已修复并测试通过

### 5. WITH 子句（CTE）基础支持 ✅
- **问题**: WITH 子句没有正确格式化
- **解决方案**:
  - 实现 `format_with_clause()` 函数
  - 支持多个 CTE（逗号分隔）
  - 每个 CTE 的 SELECT 语句递归格式化并缩进
  - 支持 CREATE TABLE AS WITH 和独立 WITH 语句
- **状态**: 基础功能已实现，但有已知问题（见下文）

## 当前存在的问题 ⚠️

### 1. WITH 子句中的窗口函数 ⚠️
- **问题**: 当 CTE 的 SELECT 语句包含窗口函数（如 `NTILE(4) OVER(ORDER BY ...)`）时，格式化会出现重复内容
- **原因**: `format_select()` 函数使用简单的正则表达式提取 ORDER BY 子句，会错误匹配 OVER() 内部的 ORDER BY
- **示例**:
  ```sql
  -- 输入
  SELECT cs.*, NTILE(4) OVER(ORDER BY lifetime_value DESC) as value_quartile
  FROM customer_stats cs
  
  -- 当前输出（错误）
  SELECT
    cs.*,
    NTILE(4) OVER(ORDER BY lifetime_value DESC) as value_quartile
  FROM
    customer_stats cs
  ORDER BY
    lifetime_value DESC) as value_quartile FROM customer_stats cs  -- 重复内容！
  ```
- **影响**: 包含窗口函数的 CTE 会产生语法错误的 SQL

### 2. UPDATE SET 中的 CASE 语句包含子查询 ⚠️
- **问题**: 当 CASE 语句的 WHEN 条件包含子查询时，格式化不够完美
- **示例**:
  ```sql
  UPDATE users SET user_level = CASE 
    WHEN user_id IN(SELECT user_id FROM top_customers WHERE value_quartile = 1) THEN 'platinum'
    ...
  ```
- **当前输出**: 子查询的 WHERE 子句会被单独提取出来，导致格式混乱
- **影响**: 可读性较差，但 SQL 语法仍然正确

### 3. 子查询缩进 ⚠️
- **问题**: 虽然实现了 `format_subquery_in_column()` 和 `format_condition_with_subquery()`，但在复杂场景下效果不理想
- **影响**: 子查询的缩进不够一致

## 测试结果

### 单元测试
- ✅ 所有 27 个语法高亮测试通过
- ✅ 基础 SQL 格式化功能正常

### 复杂 SQL 测试
- ✅ CREATE TABLE 格式化正常
- ✅ INSERT INTO ... VALUES 格式化正常
- ✅ INSERT INTO ... SELECT 格式化正常
- ✅ INSERT ... ON DUPLICATE KEY UPDATE 格式化正常
- ✅ UPDATE 基础格式化正常
- ✅ DELETE 格式化正常
- ⚠️ WITH 子句在包含窗口函数时有问题
- ⚠️ UPDATE SET 中的复杂 CASE 语句有问题

## 建议的解决方案

### 短期方案（1-2天）
1. **改进 SELECT 解析**:
   - 重写 `format_select()` 函数，使用基于括号深度的解析而不是简单的正则表达式
   - 在提取 ORDER BY、GROUP BY 等子句时，跳过括号内的关键字
   - 这将解决窗口函数的问题

2. **改进 CASE 语句中的子查询处理**:
   - 在 `format_case_expression()` 中检测并格式化子查询
   - 确保子查询的缩进正确

### 长期方案（3-5天）
1. **实现完整的 SQL 解析器**:
   - 使用词法分析器（tokenizer）将 SQL 分解为 tokens
   - 使用语法分析器（parser）构建抽象语法树（AST）
   - 基于 AST 进行格式化，避免正则表达式的局限性

2. **考虑使用现有库**:
   - 虽然用户不满意 sqlparse，但可以考虑其他库如 `sqlglot`
   - 或者使用 sqlparse 的 tokenizer 部分，自己实现格式化逻辑

## 当前代码状态

### 文件列表
- `sql_formatter_new.py` - 主格式化器（约 700 行）
- `ui/main_window.py` - 集成了格式化功能
- `test_user_complex_sql.py` - 复杂 SQL 测试
- `test_with_debug.py` - WITH 子句调试测试
- `test_with_debug2.py` - WITH 子句详细调试

### 代码质量
- ✅ 代码结构清晰，函数职责明确
- ✅ 有详细的文档字符串
- ✅ 基础功能稳定
- ⚠️ 复杂场景下需要改进

## 下一步行动

### 选项 1: 继续改进当前实现
- **优点**: 保持代码自主性，完全可控
- **缺点**: 需要更多时间处理边缘情况
- **时间**: 2-3 天

### 选项 2: 使用混合方案
- **方案**: 使用 sqlparse 的 tokenizer 进行词法分析，自己实现格式化逻辑
- **优点**: 利用成熟的词法分析，避免正则表达式的局限性
- **缺点**: 需要学习 sqlparse 的 API
- **时间**: 1-2 天

### 选项 3: 先发布当前版本
- **方案**: 接受当前的局限性，在文档中说明不支持的场景
- **优点**: 快速发布，大部分场景已经可用
- **缺点**: 用户可能遇到格式化错误的情况
- **时间**: 立即可用

## 建议

我建议采用**选项 1**，继续改进当前实现，重点解决窗口函数的问题。这是最常见的问题，解决后将大大提高格式化器的可用性。

具体步骤：
1. 重写 `format_select()` 函数，使用基于括号深度的关键字提取
2. 测试窗口函数场景
3. 改进 CASE 语句中的子查询处理
4. 全面测试并修复发现的问题

预计时间：2-3 天的开发时间。
