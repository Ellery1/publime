-- SQL 示例文件
-- 演示SQL语法高亮效果

-- 创建数据库
CREATE DATABASE IF NOT EXISTS company_db;
USE company_db;

-- 创建员工表
CREATE TABLE employees (
    id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    hire_date DATE NOT NULL,
    salary DECIMAL(10, 2),
    department_id INT,
    manager_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (manager_id) REFERENCES employees(id)
);

-- 创建部门表
CREATE TABLE departments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    budget DECIMAL(15, 2)
);

-- 插入部门数据
INSERT INTO departments (name, location, budget) VALUES
('Engineering', 'San Francisco', 1000000.00),
('Sales', 'New York', 500000.00),
('Marketing', 'Los Angeles', 300000.00),
('HR', 'Chicago', 200000.00);

-- 插入员工数据
INSERT INTO employees (first_name, last_name, email, phone, hire_date, salary, department_id) VALUES
('John', 'Doe', 'john.doe@company.com', '555-0101', '2020-01-15', 75000.00, 1),
('Jane', 'Smith', 'jane.smith@company.com', '555-0102', '2019-03-20', 85000.00, 1),
('Bob', 'Johnson', 'bob.johnson@company.com', '555-0103', '2021-06-10', 65000.00, 2),
('Alice', 'Williams', 'alice.williams@company.com', '555-0104', '2018-11-05', 95000.00, 1);

-- 查询所有员工
SELECT * FROM employees;

-- 查询特定部门的员工
SELECT 
    e.first_name,
    e.last_name,
    e.email,
    e.salary,
    d.name AS department_name
FROM employees e
INNER JOIN departments d ON e.department_id = d.id
WHERE d.name = 'Engineering'
ORDER BY e.salary DESC;

-- 计算每个部门的平均工资
SELECT 
    d.name AS department,
    COUNT(e.id) AS employee_count,
    AVG(e.salary) AS avg_salary,
    MIN(e.salary) AS min_salary,
    MAX(e.salary) AS max_salary
FROM departments d
LEFT JOIN employees e ON d.id = e.department_id
GROUP BY d.id, d.name
HAVING COUNT(e.id) > 0
ORDER BY avg_salary DESC;

-- 更新员工工资
UPDATE employees
SET salary = salary * 1.10
WHERE department_id = 1 AND hire_date < '2020-01-01';

-- 删除旧记录
DELETE FROM employees
WHERE hire_date < '2015-01-01';

-- 创建视图
CREATE VIEW employee_summary AS
SELECT 
    e.id,
    CONCAT(e.first_name, ' ', e.last_name) AS full_name,
    e.email,
    e.salary,
    d.name AS department,
    TIMESTAMPDIFF(YEAR, e.hire_date, CURDATE()) AS years_employed
FROM employees e
LEFT JOIN departments d ON e.department_id = d.id;

-- 查询视图
SELECT * FROM employee_summary
WHERE years_employed > 2;

-- 创建索引
CREATE INDEX idx_employee_email ON employees(email);
CREATE INDEX idx_employee_department ON employees(department_id);

-- 子查询示例
SELECT first_name, last_name, salary
FROM employees
WHERE salary > (
    SELECT AVG(salary)
    FROM employees
);

-- CASE语句
SELECT 
    first_name,
    last_name,
    salary,
    CASE
        WHEN salary < 60000 THEN 'Junior'
        WHEN salary BETWEEN 60000 AND 80000 THEN 'Mid-level'
        WHEN salary > 80000 THEN 'Senior'
        ELSE 'Unknown'
    END AS level
FROM employees;

-- 窗口函数
SELECT 
    first_name,
    last_name,
    department_id,
    salary,
    ROW_NUMBER() OVER (PARTITION BY department_id ORDER BY salary DESC) AS rank_in_dept,
    AVG(salary) OVER (PARTITION BY department_id) AS dept_avg_salary
FROM employees;
