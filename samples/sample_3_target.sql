SELECT
  count(0)
FROM
  (
    SELECT
      tdi.product_no AS productNo,
      -- 产品编号
      xc.NAME AS productName,
      -- 产品名称
      tdi.application_no AS applicationNo,
      -- 授信协议号
      tdi.customer_no AS customerNo,
      -- 客户编号
      uc.customer_name AS customerName,
      -- 客户名称
      tdi.order_no AS orderNo,
      -- 订单号
      tdi.duebill_no AS duebillNo,
      -- 贷款借据号
      tdi.contract_no AS contractNo,
      -- 贷款合同编号
      tdi.repay_mode as repayMode,
      -- 还款方式
      trs.sch_date AS schDate,
      -- 最近还款日
      sum(trs.os_tot_amount) AS payableTotalAmount,
      -- 应还总金额
      if(trs.setl_flag = 1, '是', '否') as setlFlag,
      -- 是否已还 1是，0否
      rvt.id as taskId,
      if(
        rvt.return_visit = 1,
        '是',
        if(rvt.return_visit = 0, '否', '-')
      ) as visited,
      rvt.task_status as taskStatus,
      -- 任务状态
      rvt.bind_name as ownerName,
      -- 任务所属者
      rvt.rule_name as ruleName,
      rvt.gmt_create as createTime,
      rvr.visit_task_no,
      rvr.gmt_create as lastRecodTime,
      rvr.created_by as lastTaskHolder,
      oca.funder_name as funder,
      tdi.loan_mode as loanMode,
      oca.phone
    FROM
      post_loan.t_return_visit_task rvt
      LEFT JOIN post_loan.t_blacklist tb ON rvt.customer_no = tb.customer_no
      and tb.op_flag != 'DELETE'
      and tb.scene like '%REPAYMENT_REMINDER%'
      and tb.deleted = 0
      LEFT JOIN core_ms.t_repayment_schedule trs ON rvt.duebill_no = trs.duebill_no
      INNER JOIN core_ms.`t_duebill_info` tdi ON rvt.duebill_no = tdi.duebill_no
      INNER JOIN xyd_config.t_product xc ON xc.product_no = tdi.product_no
      INNER JOIN titan.u_customer uc ON uc.customer_no = tdi.customer_no
      LEFT JOIN titan.o_credit_application oca ON rvt.application_no = oca.application_no
      and oca.op_flag != 'DELETE'
      LEFT JOIN (
        SELECT
          visit_task_no,
          gmt_create,
          created_by,
          op_flag
        FROM
          (
            SELECT
              row_number () OVER(
                PARTITION BY contract_no
                ORDER BY
                  gmt_update DESC
              ) AS row_num,
              visit_task_no,
              gmt_create,
              created_by,
              op_flag
            FROM
              post_loan.t_return_visit_record
          ) t
        WHERE
          t.row_num = 1
      ) AS rvr ON rvr.visit_task_no = rvt.visit_task_no
      and rvt.op_flag != 'DELETE'
    WHERE
      tdi.op_flag != 'DELETE'
      AND rvt.op_flag != 'DELETE'
      AND rvt.return_visit_type = 'REPAYMENT_REMINDER'
      AND uc.op_flag != 'DELETE'
      AND xc.op_flag != 'DELETE'
      AND trs.overdue_flag = 0
      AND trs.setl_flag = 0
      AND tb.id is null
      -- 还款日
      -- 客户名称
      -- 还款日是否首三期
      -- 当期还款总额
    GROUP BY
      tdi.product_no,
      xc.`NAME`,
      tdi.application_no,
      tdi.customer_no,
      uc.customer_name,
      tdi.order_no,
      tdi.duebill_no,
      tdi.contract_no,
      trs.sch_date,
      trs.setl_flag,
      rvt.id,
      rvt.return_visit,
      rvt.task_status,
      rvt.bind_name,
      rvt.rule_name,
      rvt.gmt_create,
      tdi.repay_mode,
      rvr.visit_task_no,
      rvr.gmt_create,
      rvr.created_by,
      oca.funder_name,
      tdi.loan_mode,
      oca.phone
    ORDER BY
      rvt.task_status,
      tdi.duebill_no
  ) tmp_count