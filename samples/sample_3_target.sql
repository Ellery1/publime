SELECT
  tct.collection_task_no,
  tct.collection_type,
  tct.customer_no,
  tct.product_no,
  tct.parallel_type,
  tct.group_code,
  tct.group_name,
  if (tct.loan_status = 'SETTLE', '是', '否') as loanStatus,
  tct.gmt_update,
  xc.`NAME` AS product_name,
  uc.id_number,
  uc.customer_name,
  ua.province,
  ua.city,
  ua.district,
  IFNULL (overdueInfo.sch_tot_amount, 0) as sch_tot_amount,
  IFNULL (overdueInfo.sch_principal, 0) as sch_principal,
  IFNULL (overdueInfo.sch_interest, 0) as sch_interest,
  IFNULL (overdueInfo.os_tot_amount, 0) as os_tot_amount,
  IFNULL (overdueInfo.os_other_fee, 0) as os_other_fee,
  IFNULL (overdueInfo.os_overdue_interest, 0) as os_overdue_interest,
  IFNULL (overdueInfo.os_principal, 0) as os_principal,
  IFNULL (overdueInfo.os_interest, 0) as os_interest,
  IFNULL (overdueInfo.overdue_day, 0) as overdue_day,
  IFNULL (total.total_amount, 0) as total_amount,
  IFNULL (otherFeeDetail.osAmount, 0) as os_amount,
  tct.lawsuit,
  tct.lawsuit_reason,
  tct.last_record_name,
  tct.last_record_time,
  tct.bind_code,
  tct.bind_name,
  tct.complanint,
  tct.mark,
  DATE_FORMAT (tct.mark_time, '%Y-%m-%d') as markTime,
  tllr.send_status as lawyerLetterStatus,
  rr.related_name as relatedName,
  COALESCE (apb2.platform_name, apb1.platform_name) as firstLevelCoreCustomer
FROM
  (
    SELECT
      tct.collection_task_no,
      tct.collection_type,
      tct.customer_no,
      tct.customer_name,
      tct.product_no,
      tct.parallel_type,
      tct.loan_status,
      tct.group_code,
      tct.group_name,
      max (tct.application_no) as application_no,
      group_concat (tct.duebill_no) as duebill_no,
      max (tct.collection_status) as collection_status,
      max (tct.gmt_update) as gmt_update,
      max (tct.lawsuit) as lawsuit,
      max (tct.lawsuit_reason) as lawsuit_reason,
      max (tct.last_record_name) as last_record_name,
      max (tct.last_record_time) as last_record_time,
      max (tct.bind_code) as bind_code,
      max (tct.bind_name) as bind_name,
      max (tct.complanint) as complanint,
      max (tct.case_keep) as case_keep,
      max (tct.mark) as mark,
      max (tct.mark_time) as mark_time
    FROM
      post_loan.t_collection_task tct
    WHERE
      tct.deleted = 0
      AND tct.op_flag != 'DELETE'
    GROUP BY
      tct.collection_task_no,
      tct.collection_type,
      tct.customer_no,
      tct.customer_name,
      tct.product_no,
      tct.parallel_type,
      tct.loan_status,
      tct.group_code,
      tct.group_name
  ) tct
  LEFT JOIN titan.u_address ua ON tct.customer_no = ua.customer_no
  and ua.addr_type = 'residential'
  and ua.op_flag != 'DELETE'
  LEFT JOIN (
    SELECT
      submit_param,
      customer_no,
      collection_task_no
    FROM
      post_loan.t_collection_task_customer_label
    WHERE
      id IN (SELECT MAX (id) FROM post_loan.t_collection_task_customer_label WHERE op_flag != 'DELETE' GROUP BY customer_no, collection_task_no)
  ) ctcl ON ctcl.collection_task_no = tct.collection_task_no
  and ctcl.customer_no = tct.customer_no
  LEFT JOIN titan.o_credit_application oca ON oca.application_no = tct.application_no
  and oca.op_flag != 'DELETE'
  LEFT JOIN titan.u_customer uc ON tct.customer_no = uc.customer_no
  and uc.op_flag != 'DELETE'
  LEFT JOIN xyd_config.t_product xc ON tct.product_no = xc.product_no
  and xc.op_flag != 'DELETE'
  LEFT JOIN (
    SELECT
      distinct tlt.collection_task_no,
      tlt.customer_no,
      tlt.application_no,
      tlt.lawsuit_status
    FROM
      post_loan.t_lawsuit_task tlt
    WHERE
      tlt.op_flag != 'DELETE'
  ) tlt ON tlt.collection_task_no = tct.collection_task_no
  and tlt.customer_no = tct.customer_no
  and tlt.application_no = tct.application_no
  LEFT JOIN titan.u_account_business uab ON uab.apply_no = tct.application_no
  and uab.op_flag != 'DELETE'
  LEFT JOIN (
    SELECT
      tdi.product_no,
      tdi.customer_no,
      sum (trsAll.os_tot_amount) AS sch_tot_amount,
      sum (trsAll.os_principal) AS sch_principal,
      sum (trsAll.os_interest) AS sch_interest,
      sum (trsOverdue.os_tot_amount) AS os_tot_amount,
      sum (trsOverdue.os_other_fee) AS os_other_fee,
      sum (trsOverdue.os_overdue_interest) AS os_overdue_interest,
      sum (trsOverdue.os_principal) AS os_principal,
      sum (trsOverdue.os_interest) AS os_interest,
      max (trsOverdue.overdue_day) AS overdue_day
    FROM
      core_ms.`t_duebill_info` tdi
      INNER JOIN (
        SELECT
          duebill_no,
          sum (os_tot_amount) AS os_tot_amount,
          sum (os_other_fee) AS os_other_fee,
          sum (os_overdue_interest) AS os_overdue_interest,
          sum (os_principal) AS os_principal,
          sum (os_interest) AS os_interest,
          max (overdue_day) AS overdue_day
        FROM
          core_ms.t_repayment_schedule
        WHERE
          op_flag != 'DELETE'
          AND overdue_flag = '1'
          AND setl_flag = 0
        GROUP BY
          duebill_no
      ) trsOverdue ON trsOverdue.duebill_no = tdi.duebill_no
      INNER JOIN (
        SELECT
          duebill_no,
          sum (os_principal) AS os_principal,
          sum (os_tot_amount) AS os_tot_amount,
          sum (os_interest) AS os_interest
        FROM
          core_ms.t_repayment_schedule
        WHERE
          op_flag != 'DELETE'
          AND setl_flag = 0
        GROUP BY
          duebill_no
      ) trsAll ON trsAll.duebill_no = trsOverdue.duebill_no
    WHERE
      tdi.op_flag != 'DELETE'
    GROUP BY
      tdi.product_no,
      tdi.customer_no
  ) overdueInfo ON tct.customer_no = overdueInfo.customer_no
  and overdueInfo.product_no = tct.product_no
  LEFT JOIN (
    SELECT
      tdi.customer_no,
      tdi.product_no,
      sum (tfd.os_amount) osAmount
    FROM
      core_ms.t_other_fee_detail tfd
      INNER JOIN core_ms.t_duebill_info tdi ON tfd.duebill_no = tdi.duebill_no
      and tfd.charge_id = 12
    WHERE
      tdi.op_flag != 'DELETE'
      AND tfd.op_flag != 'DELETE'
    GROUP BY
      tdi.customer_no,
      tdi.product_no
  ) otherFeeDetail ON tct.customer_no = otherFeeDetail.customer_no
  and tct.product_no = otherFeeDetail.product_no
  LEFT JOIN (
    SELECT
      tllr.collection_task_no,
      tllr.send_status
    FROM
      post_loan.t_lawyer_letter_record tllr
      JOIN (
        SELECT
          collection_task_no,
          max (id) id
        FROM
          post_loan.t_lawyer_letter_record
        WHERE
          collection_task_no IS NOT NULL
          AND op_flag != 'DELETE'
        GROUP BY
          collection_task_no
      ) temp ON temp.id = tllr.id
  ) tllr ON tllr.collection_task_no = tct.collection_task_no
  LEFT JOIN (
    SELECT
      tdi.customer_no,
      SUM (trr.repay_amount) as total_amount
    FROM
      core_ms.t_duebill_info tdi
      JOIN core_ms.t_repay_record trr ON tdi.duebill_no = trr.duebill_no
    WHERE
      (
        tdi.op_flag != 'DELETE'
        or tdi.op_flag IS NULL
      )
      AND (
        trr.op_flag != 'DELETE'
        or trr.op_flag IS NULL
      )
      AND trr.transaction_date = CURRENT_DATE ()
    GROUP BY
      tdi.customer_no
  ) total ON total.customer_no = tct.customer_no
  LEFT JOIN (
    SELECT
      sc.collection_task_no,
      t.riskGrade,
      sc.tag_loss,
      sc.tag_inertia_ovdue,
      sc.tag_fpd2,
      sc.tag_fpd15_his3m,
      sc.tag_fpd2_first
    FROM
      post_loan.t_collection_score_card sc
      JOIN (
        SELECT
          collection_task_no,
          max (risk_grade) riskGrade,
          max (id) id
        FROM
          post_loan.t_collection_score_card
        WHERE
          deleted = 0
          AND op_flag != 'DELETE'
          AND risk_grade != 9
        GROUP BY
          collection_task_no
      ) t ON t.id = sc.id
    WHERE
      sc.deleted = 0
      AND sc.op_flag != 'DELETE'
      AND sc.risk_grade != 9
  ) scoreCard ON tct.collection_task_no = scoreCard.collection_task_no
  LEFT JOIN (
    SELECT
      customer_no,
      related_name,
      outer_no
    FROM
      titan.r_related
    WHERE
      (
        op_flag != 'DELETE'
        or op_flag IS NULL
      )
    GROUP BY
      customer_no,
      related_name,
      outer_no
  ) rr ON rr.customer_no = oca.related_no
  LEFT JOIN (
    SELECT
      platform_basic_no,
      upper_platform_no,
      platform_name
    FROM
      xyd_companion.admin_platform_basic
    WHERE
      (
        op_flag != 'DELETE'
        or op_flag is null
      )
  ) apb1 ON rr.outer_no = apb1.platform_basic_no
  LEFT JOIN (
    SELECT
      platform_basic_no,
      upper_platform_no,
      platform_name
    FROM
      xyd_companion.admin_platform_basic
    WHERE
      (
        op_flag != 'DELETE'
        or op_flag is null
      )
  ) apb2 ON apb1.upper_platform_no = apb2.platform_basic_no
WHERE
  true
  AND tct.collection_type in ('OPERATE', 'OPERATE_OUTSOURE', 'OPERATE_LAWSUIT', 'OPERATE_OUTSOURE_LAWSUIT')
  AND tct.duebill_no like concat ('%', 'LN20240614020816612915', '%')
  AND tct.loan_status = 'OVERDUE'
ORDER BY
  tct.last_record_time DESC,
  tct.gmt_update DESC,
  tct.customer_no,
  tct.collection_task_no
LIMIT
  50