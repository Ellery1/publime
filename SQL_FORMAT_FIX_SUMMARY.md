# SQL格式化修复总结

## 问题描述
SQL格式化功能存在以下问题：
1. 注释没有被正确保留和格式化
2. 行内注释（如 `AND u.is_active=1 -- 只统计活跃用户`）被分离到单独的行
3. 独立注释行（如 `-- 计算用户排名`）的位置不正确
4. 多行注释（`/* */`）的内部换行没有被保留

## 解决方案

### 核心思路
1. **分离头部注释和SQL代码**：将文件开头的注释（多行和单行）与SQL语句分开处理
2. **保护注释**：在格式化之前，用占位符替换注释，防止被破坏
3. **独立注释行**：通过在注释标记前后添加逗号，让注释成为独立的"列"，从而在SELECT列表中正确定位
4. **恢复注释**：在格式化完成后，将占位符替换回原始注释

### 关键技术点

#### 1. 多行注释保护
```python
multiline_comments = []
def save_multiline_comment(match):
    multiline_comments.append(match.group(0))
    return f"__MLCOMMENT_{len(multiline_comments)-1}__"

text = re.sub(r'/\*.*?\*/', save_multiline_comment, text, flags=re.DOTALL)
```

#### 2. 窗口函数保护
```python
# 匹配 ROW_NUMBER() OVER (...) 等窗口函数
match = re.search(r'\b(ROW_NUMBER|RANK|DENSE_RANK|NTILE)\s*\(\s*\)\s*OVER\s*\(', result, re.IGNORECASE)
# 使用括号深度计数找到完整的窗口函数
```

#### 3. 单行注释保护（关键创新）
```python
for line in lines:
    if '--' in line:
        idx = line.find('--')
        before = line[:idx]
        comment = line[idx:]
        single_line_comments.append(comment)
        # 在注释标记前后添加逗号，让它成为独立的"列"
        processed_lines.append(before + f', __SLCOMMENT_{len(single_line_comments)-1}__ ,')
```

这样做的好处：
- 注释会被当作独立的"列"处理
- 在按逗号分割时，注释会成为单独的元素
- 可以精确控制注释的输出位置

#### 4. 处理空列
```python
# 分割列时，过滤掉空列
col = current.strip()
if col:  # 只添加非空列
    cols.append(col)
```

#### 5. WHERE子句中的注释处理
```python
# 移除多余的逗号（来自注释保护）
cond = re.sub(r',\s*__SLCOMMENT_', ' __SLCOMMENT_', cond)
cond = re.sub(r'__SLCOMMENT_(\d+)__\s*,', r'__SLCOMMENT_\1__', cond)

# 恢复单行注释
for j, comment in enumerate(single_line_comments):
    cond = cond.replace(f'__SLCOMMENT_{j}__', comment)

# 清理多余空格
cond = ' '.join(cond.split())
```

## 测试结果

### 输入SQL
```sql
-- 这是一个复杂的SQL查询示例
-- 用于测试语法高亮和格式化

/* 多行注释
这个查询用于分析用户订单数据
包含多个JOIN、子查询和窗口函数 */

SELECT u.user_id,u.username,u.email,COUNT(o.order_id) as total_orders,SUM(o.total_amount) as total_spent,AVG(o.total_amount) as avg_order_value,MAX(o.order_date) as last_order_date,-- 计算用户排名
ROW_NUMBER() OVER (ORDER BY SUM(o.total_amount) DESC) as spending_rank,DENSE_RANK() OVER (PARTITION BY u.country ORDER BY COUNT(o.order_id) DESC) as country_rank
FROM users u LEFT JOIN orders o ON u.user_id=o.user_id
INNER JOIN order_items oi ON o.order_id=oi.order_id
LEFT JOIN products p ON oi.product_id=p.product_id
WHERE o.order_date BETWEEN '2024-01-01' AND '2024-12-31'
AND o.status IN('completed','shipped','delivered')
AND u.is_active=1 -- 只统计活跃用户
GROUP BY u.user_id,u.username,u.email,u.country
HAVING COUNT(o.order_id)>=5 AND SUM(o.total_amount)>1000
ORDER BY total_spent DESC,total_orders DESC LIMIT 100;
```

### 输出SQL（完全匹配期望）
```sql
-- 这是一个复杂的SQL查询示例
-- 用于测试语法高亮和格式化

/* 多行注释
这个查询用于分析用户订单数据
包含多个JOIN、子查询和窗口函数 */

SELECT
  u.user_id,
  u.username,
  u.email,
  COUNT(o.order_id) AS total_orders,
  SUM(o.total_amount) AS total_spent,
  AVG(o.total_amount) AS avg_order_value,
  MAX(o.order_date) AS last_order_date,
  -- 计算用户排名
  ROW_NUMBER() OVER (ORDER BY SUM(o.total_amount) DESC) AS spending_rank,
  DENSE_RANK() OVER (PARTITION BY u.country ORDER BY COUNT(o.order_id) DESC) AS country_rank
FROM
  users u
  LEFT JOIN orders o ON u.user_id=o.user_id
  INNER JOIN order_items oi ON o.order_id=oi.order_id
  LEFT JOIN products p ON oi.product_id=p.product_id
WHERE
  o.order_date BETWEEN '2024-01-01'
  AND '2024-12-31'
  AND o.status IN('completed','shipped','delivered')
  AND u.is_active=1 -- 只统计活跃用户
GROUP BY
  u.user_id,
  u.username,
  u.email,
  u.country
HAVING
  COUNT(o.order_id)>=5
  AND SUM(o.total_amount)>1000
ORDER BY
  total_spent DESC,
  total_orders DESC
LIMIT 100;
```

## 修改的文件
- `ui/main_window.py` - 更新了 `format_sql()` 方法（约300行代码）
- `test_sql_format_v2.py` - 测试脚本（验证通过）

## 验证方法
运行测试脚本：
```bash
python test_sql_format_v2.py
```

输出：
```
✓ 测试通过！格式化结果与期望输出完全一致
```

## 总结
SQL格式化功能现在可以：
1. ✅ 正确保留和格式化多行注释（保留内部换行）
2. ✅ 正确处理独立注释行（在SELECT列表中的正确位置）
3. ✅ 正确处理行内注释（保持在同一行）
4. ✅ 正确保护窗口函数（不被格式化破坏）
5. ✅ 统一关键字大小写（SELECT, FROM, WHERE等）
6. ✅ 正确缩进各个子句（2个空格）
7. ✅ 每列/每项单独一行，带正确的逗号
8. ✅ AND/OR条件正确缩进

问题已完全解决！
