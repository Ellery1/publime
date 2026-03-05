# SQL格式化开发规范

## 问题背景

在开发SQL格式化功能时，我们遇到了以下问题：
1. 反复修改同一问题，浪费大量时间和token
2. 修复一个问题后，可能引入新的问题
3. 缺乏系统性的测试，导致回归问题

## 解决方案：测试驱动开发（TDD）

### 工作流程

#### 1. 发现问题时
- **不要立即修改代码**
- **先编写测试用例**，描述预期行为
- 运行测试，确认测试失败（证明问题存在）

#### 2. 修复问题时
- 编写最小化的代码修改
- 运行测试，确认测试通过
- 运行完整的测试套件，确保没有破坏其他功能

#### 3. 代码审查清单
- [ ] 是否有对应的测试用例？
- [ ] 测试是否覆盖了边界情况？
- [ ] 是否运行了完整的测试套件？
- [ ] 是否清理了调试代码和临时文件？

## 测试套件使用指南

### 运行所有测试
```bash
python test_sql_formatter_suite.py
```

### 运行特定测试类
```python
python -m unittest test_sql_formatter_suite.TestWindowFunctions
```

### 运行特定测试方法
```python
python -m unittest test_sql_formatter_suite.TestWindowFunctions.test_window_function_with_comment
```

## 测试分类

### 1. TestBasicSelect - 基础SELECT语句
- 简单SELECT
- 带WHERE的SELECT

### 2. TestWindowFunctions - 窗口函数
- 简单窗口函数
- 带PARTITION BY的窗口函数
- 带注释的窗口函数

### 3. TestComments - 注释处理
- 行内注释
- 列之间的注释
- 多行注释

### 4. TestCaseExpression - CASE表达式
- 简单CASE
- 复杂CASE

### 5. TestComplexScenarios - 复杂场景
- 从文件读取的复杂查询

### 6. TestRegressions - 回归测试
- 之前修复的问题，确保不再出现

## 添加新测试

当发现新问题时，按以下步骤操作：

### 示例：发现注释和窗口函数合并的问题

```python
class TestRegressions(unittest.TestCase):
    """回归测试"""
    
    def test_comment_not_merged_with_window_function(self):
        """回归测试：注释不应该和窗口函数合并到同一行"""
        sql = """SELECT id,
-- 计算用户排名
ROW_NUMBER() OVER (ORDER BY salary DESC) as rank
FROM users"""
        result = format_sql(sql)
        lines = result.split('\n')
        
        # 找到注释行
        for i, line in enumerate(lines):
            if '-- 计算用户排名' in line:
                # 注释行不应该包含窗口函数的关键部分
                self.assertNotIn('ROW_NUMBER()', line)
                self.assertNotIn('OVER(', line)
                # 下一行应该是窗口函数
                if i + 1 < len(lines):
                    self.assertIn('ROW_NUMBER()', lines[i + 1])
                break
```

## 代码质量要求

### 1. 函数长度
- 单个函数不超过100行
- 如果超过，需要拆分成多个小函数

### 2. 函数职责
- 每个函数只做一件事
- 函数名要清楚表达意图

### 3. 避免深层嵌套
- 最多3层缩进
- 使用早返回（early return）减少嵌套

### 4. 注释
- 复杂逻辑必须有注释
- 注释说明"为什么"，而不是"做什么"

## 调试规范

### 1. 禁止创建临时调试文件
- ❌ 不要创建 `debug_xxx.py`
- ✅ 使用测试用例来调试

### 2. 调试代码必须清理
- ❌ 不要在代码中保留 `print` 调试语句
- ✅ 使用日志系统或删除调试代码

### 3. 使用断点调试
- 使用IDE的断点功能
- 比print更高效

## 提交前检查清单

- [ ] 所有测试通过
- [ ] 没有临时调试文件
- [ ] 没有调试print语句
- [ ] 代码符合质量要求
- [ ] 添加了必要的测试用例

## 持续改进

### 每周回顾
- 统计失败的测试类型
- 分析问题根源
- 更新开发规范

### 月度重构
- 识别重复代码
- 提取公共函数
- 优化代码结构

## 成功指标

- 测试覆盖率 > 80%
- 回归问题数量 < 5%
- 新功能必须有测试
- 每次修改运行完整测试套件
