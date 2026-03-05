-- 这是一个复杂的SQL查询示例
-- 用于测试语法高亮和格式化
/* 多行注释
   这个查询用于分析用户订单数据
   包含多个JOIN、子查询和窗口函数 */
SELECT
  u.user_id,
  u.username,
  u.email,
  COUNT(o.order_id) as total_orders,
  SUM(o.total_amount) as total_spent,
  AVG(o.total_amount) as avg_order_value,
  MAX(o.order_date) as last_order_date,
  -- 计算用户排名
  ROW_NUMBER() OVER(
    ORDER BY
      SUM(o.total_amount) DESC
  ) as spending_rank,
  DENSE_RANK() OVER(
    PARTITION BY u.country
    ORDER BY
      COUNT(o.order_id) DESC
  ) as country_rank
FROM
  users u
  LEFT JOIN orders o ON u.user_id = o.user_id
  INNER JOIN order_items oi ON o.order_id = oi.order_id
  LEFT JOIN products p ON oi.product_id = p.product_id
WHERE
  o.order_date BETWEEN '2024-01-01'
  AND '2024-12-31'
  AND o.status IN ('completed', 'shipped', 'delivered')
  AND u.is_active = 1
  -- 只统计活跃用户
GROUP BY
  u.user_id,
  u.username,
  u.email,
  u.country
HAVING
  COUNT(o.order_id) >= 5
  AND SUM(o.total_amount) > 1000
ORDER BY
  total_spent DESC,
  total_orders DESC
LIMIT
  100;
  -- 创建临时表存储结果
CREATE TEMPORARY TABLE IF NOT EXISTS top_customers AS WITH customer_stats AS(
  SELECT
    user_id,
    COUNT(DISTINCT order_id) as order_count,
    SUM(total_amount) as lifetime_value,
    DATEDIFF(NOW(), MAX(order_date)) as days_since_last_order
  FROM
    orders
  WHERE
    status != 'cancelled'
  GROUP BY
    user_id
),
ranked_customers AS(
  SELECT
    cs.*,
    NTILE(4) OVER(
      ORDER BY
        lifetime_value DESC
    ) as value_quartile,
    CASE
      WHEN days_since_last_order <= 30 THEN 'active'
      WHEN days_since_last_order <= 90 THEN 'at_risk'
      ELSE 'churned'
    END as customer_status
  FROM
    customer_stats cs
  WHERE
    order_count > 0
)
SELECT
  rc.*,
  u.username,
  u.email,
  u.registration_date
FROM
  ranked_customers rc
  JOIN users u ON rc.user_id = u.user_id
WHERE
  value_quartile IN (1, 2);
  /* 更新用户等级 */
UPDATE
  users
SET
  user_level =CASE
    WHEN user_id IN (
      SELECT
        user_id
      FROM
        top_customers
      WHERE
        value_quartile = 1
    ) THEN 'platinum'
    WHEN user_id IN (
      SELECT
        user_id
      FROM
        top_customers
      WHERE
        value_quartile = 2
    ) THEN 'gold'
    WHEN user_id IN (
      SELECT
        user_id
      FROM
        orders
      GROUP BY
        user_id
      HAVING
        COUNT(*) >= 10
    ) THEN 'silver'
    ELSE 'bronze'
  END,
  updated_at = NOW()
  -- 更新时间戳
WHERE
  is_active = 1;
  -- 删除过期数据
DELETE FROM
  order_logs
WHERE
  created_at < DATE_SUB(NOW(), INTERVAL 90 DAY)
  AND log_type = 'debug';
  /* 插入汇总数据 */
INSERT INTO
  daily_summary(
    summary_date,
    total_orders,
    total_revenue,
    avg_order_value,
    unique_customers
  )
SELECT
  DATE(order_date) as summary_date,
  COUNT(*) as total_orders,
  SUM(total_amount) as total_revenue,
  AVG(total_amount) as avg_order_value,
  COUNT(DISTINCT user_id) as unique_customers
FROM
  orders
WHERE
  order_date >= CURDATE() - INTERVAL 1 DAY
GROUP BY
  DATE(order_date) ON DUPLICATE KEY
UPDATE
  total_orders =
VALUES(total_orders),
  total_revenue =
VALUES(total_revenue),
  updated_at = NOW();