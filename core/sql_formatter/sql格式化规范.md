# SQL 格式化规则

## 0. 格式化原则

### 0.1 允许的变更
格式化过程中，以下变更是**允许的**，不视为内容变更：
- **换行和缩进**：调整SQL语句的换行位置和缩进级别
- **空格**：调整关键字、运算符、括号等周围的空格
- **关键字大小写**：将SQL关键字统一转换为大写（如：`select` → `SELECT`，`and` → `AND`）

### 0.2 禁止的变更
格式化过程中，以下变更是**禁止的**，会触发内容变更告警：
- **添加或删除关键字**：不能添加或删除任何SQL关键字（如：不能添加`AS`关键字）
- **修改标识符**：不能修改表名、列名、别名等标识符
- **修改字面量**：不能修改字符串、数字等字面量的值
- **修改注释**：不能修改或删除注释内容
- **修改函数名**：不能修改函数名称

### 0.3 内容完整性检查
- 格式化完成后，会自动检查内容是否发生变更（忽略空白字符和关键字大小写）
- 如果检测到禁止的内容变更，会弹出告警窗口提示用户
- 用户应该检查格式化结果，确认是否接受变更

## 1. 关键字处理
- 所有 SQL 关键字必须大写，包括：SELECT, FROM, WHERE, GROUP BY, HAVING, ORDER BY, LIMIT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, TRUNCATE, WITH, CASE, WHEN, THEN, ELSE, END, JOIN, INNER, LEFT, RIGHT, ON, AS, AND, OR, NOT, IN, BETWEEN, LIKE, IS, NULL, TRUE, FALSE, IF, EXISTS 等
- 函数名保持原始大小写（如：get_json_string, JSON_OBJECT, DATE_FORMAT 等）
- **注意**：关键字大小写的标准化（如：`and` → `AND`）不视为内容变更

## 2. 缩进规则
- 每个语句块缩进 2 个空格
- SELECT, FROM, WHERE 等关键字后的内容缩进 2 个空格
- 子查询缩进 2 个空格
- CASE 语句的 WHEN/THEN/ELSE 子句缩进 2 个空格
- 括号内的多行内容缩进 2 个空格
- ON DUPLICATE KEY UPDATE 子句缩进 2 个空格

## 3. 换行规则

### 3.1 主要关键字换行
- 主要关键字（SELECT, FROM, WHERE, GROUP BY, HAVING, ORDER BY, LIMIT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, TRUNCATE, WITH）**必须**单独一行
- ORDER BY 关键字**必须**单独一行，其后的排序列各自单独一行并缩进

### 3.2 SELECT子句换行
- SELECT 关键字单独一行
- **每个**列名/表达式**必须**单独一行，逗号放在行尾
- 列名/表达式前缩进 2 个空格
- 示例：
```sql
SELECT
  column1,
  column2,
  function(column3) as alias
```

### 3.3 FROM子句换行
- FROM 关键字单独一行
- 每个表名/子查询单独一行并缩进
- 子查询的开始括号紧跟在FROM后，然后换行
- 示例：
```sql
FROM
  (
    SELECT
      ...
  ) alias
```

### 3.4 JOIN子句换行
- 每个 JOIN 关键字单独一行
- ON 条件可以紧跟在JOIN后，也可以单独一行
- 多个ON条件时，每个条件单独一行

### 3.5 WHERE子句换行
- WHERE 关键字单独一行
- 每个条件单独一行，AND/OR 放在条件前面
- 条件前缩进 2 个空格

### 3.6 CASE语句换行
- CASE 关键字单独一行
- **每个** WHEN 子句单独一行并缩进，THEN 后的结果紧跟在同一行
- ELSE 子句单独一行并缩进
- END 关键字单独一行（与CASE对齐）
- 示例：
```sql
CASE
  WHEN condition1 THEN result1
  WHEN condition2 THEN result2
  ELSE default_result
END as alias
```

### 3.7 JSON_OBJECT函数换行
- JSON_OBJECT 的开始括号后**必须**换行
- **每个**键值对单独一行并缩进
- 键和值用逗号分隔，逗号后有空格
- 结束括号单独一行（与JSON_OBJECT对齐）
- 示例：
```sql
JSON_OBJECT(
  'key1', value1,
  'key2', value2,
  'key3', value3
)
```

### 3.8 子查询换行
- 子查询的开始括号紧跟在FROM/JOIN等关键字后，然后换行
- 子查询内的所有内容相对于外层查询缩进 2 个空格
- 结束括号单独一行，与开始括号对齐
- 嵌套子查询遵循相同规则，每层额外缩进 2 个空格

### 3.9 其他换行规则
- 每个 GROUP BY 列单独一行
- 每个 HAVING 条件单独一行
- 每个 ORDER BY 列单独一行
- 每个 INSERT INTO 的值列表单独一行
- OVER() 窗口函数子句单独一行
- LIMIT 子句单独一行

## 4. 空格规则
- 等号（=）前后必须有空格
- 比较运算符（>, <, >=, <=, !=）前后必须有空格
- 逻辑运算符（AND, OR, NOT）前后必须有空格
- 逗号（,）后面必须有空格
- 括号（(, )）前后必须有空格（除非括号内是函数调用或表达式）
- JOIN 关键字前后必须有空格
- ON 关键字前后必须有空格
- AS 关键字前后必须有空格
- CASE 关键字前面必须有空格（如：`user_level = CASE`）
- BETWEEN/AND 之间必须有空格
- **IN 关键字后必须有空格**（如：`IN (1, 2)` 而不是 `IN(1, 2)`）
- IN 括号内的元素之间用逗号和空格分隔

## 5. 括号处理
- 函数调用的括号（如：COUNT(*), MAX(order_date)）前后无空格
- 子查询的括号前后有空格
- CASE 表达式的括号前后有空格
- OVER() 窗口函数的括号前后有空格

## 6. 注释处理
- 单行注释使用 --，后面跟一个空格
- 多行注释使用 /* */
- 注释保持在原始位置，适当缩进
- 语句后的注释单独一行，与语句保持相同缩进

## 7. 其他规则
- 分号（;）放在语句的最后
- 表名和列名使用下划线命名法（如：user_id, order_date）
- 别名使用 AS 关键字（如：`COUNT(o.order_id) as total_orders`）
- JSON 对象的键值对每个单独一行，键和值之间有空格
- VALUES 关键字后的数据行，每个值单独一行
- IN 子句的元素列表，每个元素单独一行
- BETWEEN...AND 条件分行书写

## 8. 特殊语句格式化

### 8.1 SELECT 语句（标准格式）
```sql
SELECT
  column1,
  column2,
  function(column3) as alias
FROM
  table1 t1
  JOIN table2 t2 ON t1.id = t2.t1_id
WHERE
  condition1
  AND condition2
GROUP BY
  column1,
  column2
HAVING
  aggregate_condition
ORDER BY
  column1 DESC,
  column2 ASC
LIMIT
  100;
```

### 8.2 SELECT 语句（带子查询）
```sql
SELECT
  column1,
  column2
FROM
  (
    SELECT
      inner_column1,
      inner_column2
    FROM
      inner_table
    WHERE
      inner_condition
  ) alias
WHERE
  outer_condition;
```

### 8.3 CASE 语句（详细格式）
```sql
CASE
  WHEN condition1 THEN result1
  WHEN condition2
  AND condition2_extra THEN result2
  WHEN condition3 THEN JSON_OBJECT(
    'key1', value1,
    'key2', value2
  )
  ELSE default_result
END as alias
```

**重要说明：**
- CASE 必须单独一行
- 每个 WHEN 单独一行，THEN 紧跟在同一行
- 如果 THEN 后的结果是复杂表达式（如JSON_OBJECT），开始括号后换行
- ELSE 单独一行
- END 单独一行，与 CASE 对齐

### 8.4 JSON_OBJECT 函数（详细格式）
```sql
JSON_OBJECT(
  'key1', value1,
  'key2', value2,
  'key3', DATE_FORMAT(date_column, '%Y-%m-%d'),
  'key4', nested_function(column)
)
```

**重要说明：**
- JSON_OBJECT 后的开始括号必须换行
- 每个键值对单独一行，键在前，逗号，值在后
- 所有键值对缩进 2 个空格
- 结束括号单独一行，与 JSON_OBJECT 对齐

### 8.5 UPDATE 语句
```sql
UPDATE
  table_name
SET
  column1 = value1,
  column2 = value2
WHERE
  condition;
```

### 8.6 INSERT 语句
```sql
INSERT INTO
  table_name (column1, column2, column3)
VALUES
  (value1, value2, value3),
  (value4, value5, value6);
```

### 8.7 DELETE 语句
```sql
DELETE FROM
  table_name
WHERE
  condition;
```

### 8.8 CREATE TABLE 语句
```sql
CREATE TABLE table_name (
  column1 INT PRIMARY KEY AUTO_INCREMENT,
  column2 VARCHAR(50) NOT NULL,
  column3 DECIMAL(10, 2),
  FOREIGN KEY (column2) REFERENCES other_table(id)
);
```

### 8.9 WITH 子句（CTE）
```sql
WITH cte_name AS (
  SELECT
    column1,
    column2
  FROM
    table_name
  WHERE
    condition
)
SELECT
  *
FROM
  cte_name;
```

### 8.10 窗口函数
```sql
ROW_NUMBER() OVER(
  PARTITION BY column1
  ORDER BY
    column2 DESC
) as rank_in_group
```

### 8.11 复杂嵌套查询示例
```sql
SELECT
  outer_column,
  CASE
    WHEN condition THEN JSON_OBJECT(
      'key1', value1,
      'key2', value2
    )
    ELSE NULL
  END as result
FROM
  (
    SELECT
      inner_column,
      nested_function(column) as outer_column
    FROM
      (
        SELECT
          *
        FROM
          deepest_table
        WHERE
          deepest_condition
      ) level2
    WHERE
      level2_condition
  ) level1
WHERE
  outer_condition
ORDER BY
  outer_column DESC
LIMIT
  100;
```

## 9. 注意事项
- 保持 SQL 语句的可读性和一致性
- 复杂查询应适当使用换行和缩进来提高可读性
- 避免过长的单行语句（超过 80 个字符）
- 保持注释的简洁和有用性
- 绝对不允许在格式化中出现修改原本内容的情况。格式化只能做 ”换行、缩进、空格“ 的操作


## 10. 测试要求与错误处理

### 10.1 必须通过的测试
格式化功能必须通过以下测试，格式化结果必须与目标文件**完全一致**：
1. `complex_test.sql` 格式化后与 `complex_test_target.sql` 完全一致
2. `sample_1.sql` 格式化后与 `sample_1_target.sql` 完全一致
3. `sample_2.sql` 格式化后与 `sample_2_target.sql` 完全一致

### 10.2 内容完整性检查
- 格式化完成后，**必须**检查前后内容是否有变更（除空白字符外）
- 检查方法：移除所有空白字符后比较原始SQL和格式化后的SQL
- 如果检测到内容变更，**必须**提示用户："建议手动格式化"
- 不应该因为格式化失败而导致原始SQL丢失或损坏

### 10.3 一致性原则
- 相同类型的语句结构必须使用相同的格式化规则
- 缩进必须统一使用 2 个空格（不使用Tab）
- 关键字必须统一大写
- 函数名保持原始大小写

## 11. Sample_2 Bug修复说明

### 11.1 问题描述
sample_2.sql 格式化后的结果与 sample_2_target.sql 不一致，主要问题包括：

1. **SELECT列未正确换行**：所有列应该各自单独一行
2. **CASE语句格式错误**：WHEN/THEN子句应该正确换行和缩进
3. **JSON_OBJECT参数未换行**：每个键值对应该单独一行
4. **子查询括号位置错误**：开始括号应该紧跟FROM后并换行
5. **ORDER BY未单独一行**：ORDER BY关键字应该单独一行

### 11.2 正确格式示例

#### SELECT列的正确格式
```sql
-- 错误：所有列在同一行或少数几行
select '0000' batch_no, tttt.*, get_json_string(tttt.check_voucher_result, 'voucher_type_no') voucher_type_no

-- 正确：每列单独一行
SELECT
  '0000' batch_no,
  tttt.*,
  get_json_string(tttt.check_voucher_result, 'voucher_type_no') voucher_type_no
```

#### CASE语句的正确格式
```sql
-- 错误：WHEN和THEN在同一行，没有正确缩进
case when result.right_value is null and result.left_value is not null then JSON_OBJECT(...)

-- 正确：CASE单独一行，每个WHEN单独一行并缩进
CASE
  WHEN result.right_value is null
  and result.left_value is not null THEN JSON_OBJECT(
    'key1', value1,
    'key2', value2
  )
END
```

#### JSON_OBJECT的正确格式
```sql
-- 错误：参数在同一行或少数几行
JSON_OBJECT('check_result_no', 0, 'voucher_type_no', 0, 'left_subject_no', '')

-- 正确：每个键值对单独一行
JSON_OBJECT(
  'check_result_no', 0,
  'voucher_type_no', 0,
  'left_subject_no', ''
)
```

#### 子查询的正确格式
```sql
-- 错误：FROM和子查询在同一行
FROM (SELECT ...

-- 正确：FROM单独一行，括号后换行
FROM
  (
    SELECT
      ...
  ) alias
```

#### ORDER BY的正确格式
```sql
-- 错误：ORDER BY和列在同一行
order by tttt.right_key, tttt.left_key

-- 正确：ORDER BY单独一行，每个排序列单独一行
ORDER BY
  tttt.right_key,
  tttt.left_key,
  tttt.channel
```

### 11.3 修复优先级
1. **最高优先级**：确保不修改SQL内容（只修改空白字符）
2. **高优先级**：SELECT列、CASE语句、JSON_OBJECT的换行
3. **中优先级**：子查询括号位置、ORDER BY换行
4. **低优先级**：代码可读性优化

### 11.4 回归测试
修复sample_2问题后，必须确保：
- complex_test.sql 的格式化结果仍然正确
- sample_1.sql 的格式化结果仍然正确
- 没有引入新的格式化问题
