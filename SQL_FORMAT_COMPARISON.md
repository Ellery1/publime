# SQL 格式化对比

## CREATE TABLE

### 之前（不符合预期）
```sql
CREATE TABLE employees ( id INT PRIMARY KEY AUTO_INCREMENT, first_name VARCHAR(50) NOT NULL, last_name VARCHAR(50) NOT NULL, email VARCHAR(100) UNIQUE, phone VARCHAR(20), hire_date DATE NOT NULL, salary DECIMAL(10, 2), department_id INT, manager_id INT );
```

### 现在（符合预期）✅
```sql
CREATE TABLE
employees (
  id INT PRIMARY KEY AUTO_INCREMENT,
  first_name VARCHAR(50) NOT NULL,
  last_name VARCHAR(50) NOT NULL,
  email VARCHAR(100) UNIQUE,
  phone VARCHAR(20),
  hire_date DATE NOT NULL,
  salary DECIMAL(10, 2),
  department_id INT,
  manager_id INT
);
```

**改进：**
- ✅ CREATE TABLE 后换行
- ✅ 表名单独一行
- ✅ 列定义缩进 2 个空格
- ✅ 每列一行，逗号在行尾

---

## INSERT INTO

### 之前（不符合预期）
```sql
INSERT INTO
departments (name, location, budget)
VALUES
('Engineering', 'San Francisco', 1000000.00),
('Sales', 'New York', 500000.00),
('Marketing', 'Los Angeles', 300000.00),
('HR', 'Chicago', 200000.00);
```

### 现在（符合预期）✅
```sql
INSERT INTO departments (name, location, budget)
VALUES
  ('Engineering', 'San Francisco', 1000000.00),
  ('Sales', 'New York', 500000.00),
  ('Marketing', 'Los Angeles', 300000.00),
  ('HR', 'Chicago', 200000.00);
```

**改进：**
- ✅ INSERT INTO 表名和列在同一行
- ✅ VALUES 换行
- ✅ 每行值缩进 2 个空格

---

## DELETE FROM

### 之前（不符合预期）
```sql
DELETEFROM employees WHERE hire_date < '2015-01-01';
```

### 现在（符合预期）✅
```sql
DELETE FROM employees
WHERE
  hire_date < '2015-01-01';
```

**改进：**
- ✅ DELETE FROM 保持空格（不是 DELETEFROM）
- ✅ WHERE 换行
- ✅ 条件缩进

---

## UPDATE

### 之前（不符合预期）
```sql
UPDATE
employees
SET
salary = salary * 1.10
WHERE
department_id = 1 AND hire_date < '2020-01-01';
```

### 现在（符合预期）✅
```sql
UPDATE employees
SET
  salary = salary * 1.10
WHERE
  department_id = 1
  AND hire_date < '2020-01-01';
```

**改进：**
- ✅ UPDATE 表名在同一行
- ✅ SET 换行，赋值语句缩进
- ✅ WHERE 换行，条件缩进
- ✅ AND 条件单独一行

---

## SELECT

### 之前（不符合预期）
```sql
SELECT*FROMemployees;
```

### 现在（符合预期）✅
```sql
SELECT
  *
FROM
  employees;
```

**改进：**
- ✅ SELECT 换行
- ✅ 列缩进
- ✅ FROM 换行
- ✅ 表名缩进

---

## 复杂 SELECT

### 之前（不符合预期）
```sql
SELECTe.first_name,e.last_name,e.email,e.salary,d.name AS department_nameFROMemployees eINNER JOIN departments d ON e.department_id = d.idWHEREd.name = 'Engineering'ORDER BYe.salary DESC;
```

### 现在（符合预期）✅
```sql
SELECT
  e.first_name,
  e.last_name,
  e.email,
  e.salary,
  d.name AS department_name
FROM
  employees e
  INNER JOIN departments d ON e.department_id = d.id
WHERE
  d.name = 'Engineering'
ORDER BY
  e.salary DESC;
```

**改进：**
- ✅ SELECT 换行
- ✅ 每列一行，缩进 2 个空格
- ✅ FROM 换行
- ✅ JOIN 缩进
- ✅ WHERE 换行，条件缩进
- ✅ ORDER BY 换行，排序字段缩进

---

## 总结

所有格式化规则都已按照用户预期实现：

1. ✅ CREATE TABLE - 表名单独一行，列定义缩进
2. ✅ INSERT INTO - 表名和列在同一行，VALUES 行缩进
3. ✅ DELETE FROM - 保持空格
4. ✅ UPDATE - 表名在同一行，SET 项缩进
5. ✅ SELECT - 列缩进，子句换行

**可以进行用户验收！**
