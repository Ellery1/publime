WITH dict_lookup AS (
  SELECT
    d2.dict_key AS category,
    -- 父级(3位code)的 dict_key,用于区分字典类别
    d1.dict_key AS item_key,
    -- 子项 dict_key(存储的枚举值)
    d1.dict_name
  FROM
    xyd_config.s_dict d1
    JOIN (
      SELECT
        id,
        code,
        dict_key
      FROM
        xyd_config.s_dict
      WHERE
        LENGTH(code) = 3
        AND dict_key IN (
          'CustomerType',
          'loanModeV2',
          'recharge_source_type',
          'deduct_pay_channel',
          'repay_type_enum'
        )
        AND op_flag != 'DELETE'
    ) d2 ON LEFT(d1.code, 3) = d2.code -- 等值,可 hash join;等价于原 LIKE CONCAT(d2.code,'%')
    AND d1.id != d2.id
  WHERE
    d1.op_flag != 'DELETE'
),
accountName AS (
  SELECT
    account_no,
    any_value(account_name) AS account_name
  FROM
    (
      SELECT
        uc.customer_no AS account_no,
        uc.customer_name AS account_name
      FROM
        titan.u_customer uc
      WHERE
        uc.op_flag != 'DELETE'
      UNION ALL
      SELECT
        tr.customer_no AS account_no,
        tr.related_name AS account_name
      FROM
        titan.r_related tr
      WHERE
        tr.op_flag != 'DELETE'
      UNION ALL
      SELECT
        ac.company_no AS account_no,
        ac.full_name AS account_name
      FROM
        xyd_companion.admin_company ac
      WHERE
        ac.op_flag != 'DELETE'
    ) t
  GROUP BY
    account_no
),
duebill_base AS (
  SELECT
    tdi.duebill_no,
    tdi.customer_no,
    tdi.product_no,
    tdi.loan_mode,
    tdi.funder_no,
    tdi.affiliation,
    tdi.funder_mode,
    uc.customer_name,
    uc.customer_type,
    tp.NAME AS product_name
  FROM
    core_ms.t_duebill_info tdi
    LEFT JOIN titan.u_customer uc ON tdi.customer_no = uc.customer_no
    AND (
      uc.op_flag != 'DELETE'
      or uc.op_flag is null
    )
    LEFT JOIN xyd_config.t_product tp ON tdi.product_no = tp.product_no
    AND (
      tp.op_flag != 'DELETE'
      or tp.op_flag is null
    )
  WHERE
    tdi.op_flag != 'DELETE'
    AND tp.product_no = 'SJD-BZHCP-JYD'
    AND tdi.customer_no = 'P2593501210'
    AND uc.customer_name LIKE CONCAT('%', '馨融', '%')
    AND tdi.duebill_no = 'LN1779766116581LCA'
    AND tdi.loan_mode = 2
    AND tdi.funder_mode = '0'
    AND tdi.affiliation = 'xydsk'
),
deduct_detail AS (
  SELECT
    tdd.id,
    tdd.duebill_no,
    tdd.deduction_id,
    tdd.payment_order_no,
    tdd.amount,
    tdd.trans_amount,
    tdd.deduction_obj,
    tdd.amount_detail,
    tdd.`status`,
    tdd.message,
    tdd.transaction_date,
    tdd.repay_channel,
    tdd.account_no,
    tdd.gmt_create,
    tdd.refund_flag,
    CASE
      WHEN tdd.`status` = 3 THEN IFNULL(
        CAST(
          NULLIF(
            get_json_string(tdd.amount_detail, '$.principal'),
            ''
          ) AS DECIMAL(20, 2)
        ),
        0
      )
      ELSE CAST(0 AS DECIMAL(20, 2))
    END AS principal,
    CASE
      WHEN tdd.`status` = 3 THEN IFNULL(
        CAST(
          NULLIF(
            get_json_string(tdd.amount_detail, '$.interest'),
            ''
          ) AS DECIMAL(20, 2)
        ),
        0
      )
      ELSE CAST(0 AS DECIMAL(20, 2))
    END AS interest,
    CASE
      WHEN tdd.`status` = 3 THEN IFNULL(
        CAST(
          NULLIF(
            get_json_string(tdd.amount_detail, '$.overdueInterest'),
            ''
          ) AS DECIMAL(20, 2)
        ),
        0
      )
      ELSE CAST(0 AS DECIMAL(20, 2))
    END AS overdue_interest,
    CASE
      WHEN tdd.`status` = 3 THEN IFNULL(
        CAST(
          NULLIF(
            get_json_string(tdd.amount_detail, '$.compoundInterest'),
            ''
          ) AS DECIMAL(20, 2)
        ),
        0
      )
      ELSE CAST(0 AS DECIMAL(20, 2))
    END AS compound_interest
  FROM
    core_ms.t_deduction_detail tdd
  WHERE
    tdd.op_flag != 'DELETE'
)
SELECT
  tdd.duebill_no,
  tdi.customer_no,
  tdi.customer_name,
  tdi.customer_type,
  ct.dict_name AS customer_type_name,
  tdi.product_no,
  tdi.product_name,
  tdd.payment_order_no AS serial_number,
  DATE_FORMAT(td.cal_date, '%Y-%m-%d') cal_date,
  td.deduct_source,
  rst.dict_name AS deduct_source_name,
  td.repay_type,
  rt.dict_name AS repay_type_name,
  tdd.amount AS repay_amount,
  tdd.trans_amount AS deduction_amount,
  tdd.deduction_obj,
  tdd.amount_detail,
  IF(tdd.status = 4, 0, IF(td.status IN (3, 5), 1, 0)) AS account_success,
  IF(
    tdd.status = 4,
    '否',
    IF(td.status IN (3, 5), '是', '否')
  ) AS account_success_name,
  tdd.`status` AS deduction_status,
  CASE
    WHEN tdd.status = 1 THEN '初始化'
    WHEN tdd.status = 2 THEN '处理中'
    WHEN tdd.status = 3 THEN '成功'
    WHEN tdd.status = 4 THEN '失败'
    ELSE ''
  END AS deduction_status_name,
  IF(tdd.status = 4, tdd.message, '') AS deduction_message,
  IF(
    tdd.status = 4,
    tdd.message,
    IF(td.status IN (1, 2, 3, 5), '', '非足额还款，入账失败')
  ) AS account_message,
  DATE_FORMAT(tdd.transaction_date, '%Y-%m-%d') transaction_date,
  tdd.repay_channel,
  dpc.dict_name AS repay_channel_name,
  tdd.account_no,
  ac.account_name,
  tdi.loan_mode,
  lm.dict_name AS loan_mode_name,
  tdi.affiliation,
  IF(
    tdi.affiliation = 'xydsk',
    '小雨点数科',
    IF(tdi.affiliation = 'rfy', '润飞扬', '小雨点')
  ) AS affiliation_name,
  tdi.funder_no,
  DATE_FORMAT(tdd.gmt_create, '%Y-%m-%d %H:%i:%s') AS gmt_create,
  IFNULL(af.full_name, '重庆小雨点小额贷款有限公司') AS funderName,
  tdd.refund_flag,
  IF(tdd.refund_flag = 1, '是', '否') AS refund_flag_name,
  tdi.funder_mode,
  IF(td.status IN (3, 5), tdd.principal, 0) AS principal,
  IF(
    td.status IN (3, 5)
    AND tdd.deduction_obj = 'borrower',
    tdd.interest,
    0
  ) AS sch_interest,
  IF(
    td.status IN (3, 5)
    AND tdd.deduction_obj = 'borrower',
    tdd.overdue_interest,
    0
  ) AS overdue_amount,
  IF(
    td.status IN (3, 5)
    AND tdd.deduction_obj != 'borrower',
    tdd.interest,
    0
  ) AS subsidy_amount,
  IF(
    td.status IN (3, 5)
    AND tdd.deduction_obj = 'borrower',
    tdd.trans_amount - tdd.principal - tdd.interest - tdd.overdue_interest - tdd.compound_interest,
    0
  ) AS customer_repay_fee,
  IF(
    td.status IN (3, 5)
    AND tdd.deduction_obj != 'borrower',
    tdd.trans_amount - tdd.principal - tdd.interest - tdd.overdue_interest - tdd.compound_interest,
    0
  ) AS partner_fee,
  IF(
    td.status IN (3, 5)
    AND tdd.deduction_obj = 'borrower',
    tdd.compound_interest,
    0
  ) AS customer_repay_compound_interest
FROM
  deduct_detail tdd
  INNER JOIN duebill_base tdi ON tdd.duebill_no = tdi.duebill_no
  INNER JOIN core_ms.t_deduction td ON tdd.deduction_id = td.id
  AND td.op_flag != 'DELETE'
  LEFT JOIN accountName ac ON tdd.account_no = ac.account_no
  LEFT JOIN xyd_companion.admin_funder af ON tdi.funder_no = af.funder_no
  AND af.op_flag != 'DELETE'
  LEFT JOIN dict_lookup ct ON ct.category = 'CustomerType'
  AND ct.item_key = tdi.customer_type
  LEFT JOIN dict_lookup lm ON lm.category = 'loanModeV2'
  AND lm.item_key = CAST(tdi.loan_mode AS STRING)
  LEFT JOIN dict_lookup rst ON rst.category = 'recharge_source_type'
  AND rst.item_key = CAST(td.deduct_source AS STRING)
  LEFT JOIN dict_lookup rt ON rt.category = 'repay_type_enum'
  AND rt.item_key = CAST(td.repay_type AS STRING)
  LEFT JOIN dict_lookup dpc ON dpc.category = 'deduct_pay_channel'
  AND dpc.item_key = tdd.repay_channel
WHERE
  1 = 1
  AND tdd.payment_order_no = '146d2e59c0984415b6dee0af275c6865'
  AND td.repay_type = 2
  AND (
    td.status IN (3, 5)
    AND tdd.status = 3
  )
  AND td.deduct_source = 17
  AND td.cal_date >= '2025-07-01'
  AND td.cal_date <= '2026-07-16'
  AND ac.account_name LIKE CONCAT('%', '刁馨', '%')
  AND tdd.status = 3
  AND tdd.transaction_date >= '2025-07-10'
  AND tdd.transaction_date < DATE_ADD('2026-07-24', INTERVAL 1 DAY)
  AND td.gmt_create >= '2025-07-02'
  AND td.gmt_create < DATE_ADD('2026-07-08', INTERVAL 1 DAY)
ORDER BY
  tdd.gmt_create DESC,
  td.serial_number,
  tdd.id
LIMIT
  0, 10;