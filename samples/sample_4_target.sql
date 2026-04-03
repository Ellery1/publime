SELECT
  DISTINCT trvr.product_no AS productNo,
  trvr.application_no as applicationNo,
  trvr.customer_name AS customerName,
  trvr.id_number as idNumber,
  trvr.phone as phone,
  trvr.store AS store,
  trvr.customer_manager AS customerManager,
  trvr.conclusion AS conclusion,
  trvr.reason_classify AS reasonClassify,
  trvr.promise_repayment AS promiseRepayment,
  trvr.task_onwer_name AS ownerName,
  trvr.created_by AS operateName,
  trvr.communicate_type as communicateType,
  trvr.task_detail as taskDetail,
  trvr.gmt_create AS operateTime,
  oca.related_name as relatedName,
  tdi.payment_amount as paymentAmount,
  trvr.duebill_no AS duebillNo,
  tdi2.loan_mode as loanMode,
  IFNULL (af.full_name, '重庆小雨点小额贷款有限公司') as funder,
  trvt.rule_name as ruleNames,
  trvts.batch_no as speicalBatchNo,
  trvr.other_exception as otherException,
  ode.business_owner_no as businessOwnerNo
FROM
  post_loan.t_return_visit_record trvr
  LEFT JOIN titan.o_credit_application oca ON oca.application_no = trvr.application_no
  and oca.op_flag != 'DELETE'
  LEFT JOIN (
    SELECT
      application_no,
      sum (payment_amount) payment_amount
    FROM
      core_ms.t_duebill_info
    WHERE
      op_flag != 'DELETE'
    GROUP BY
      application_no
  ) tdi ON tdi.application_no = trvr.application_no
  LEFT JOIN core_ms.t_duebill_info tdi2 ON tdi2.duebill_no = trvr.duebill_no
  and tdi2.op_flag != 'DELETE'
  LEFT JOIN post_loan.t_return_visit_task trvt ON trvt.visit_task_no = trvr.visit_task_no
  and trvt.op_flag != 'DELETE'
  LEFT JOIN xyd_companion.admin_funder af ON tdi2.funder_no = af.funder_no
  and af.state = 'ENABLE'
  and af.op_flag != 'DELETE'
  LEFT JOIN post_loan.t_return_visit_task_special trvts ON trvts.visit_task_no = trvr.visit_task_no
  and trvts.op_flag != 'DELETE'
  LEFT JOIN (
    SELECT
      distinct ode.drawdown_no,
      ifnull (sd.dict_name, ode.business_owner_no) as business_owner_no
    FROM
      titan.o_drawdown_ext ode
      LEFT JOIN (
        SELECT
          sd1.dict_key,
          sd1.dict_name
        FROM
          xyd_config.s_dict sd1
          JOIN (
            SELECT
              CODE
            FROM
              xyd_config.s_dict
            WHERE
              dict_key in ('product_line')
              AND op_flag != 'DELETE'
          ) AS sd ON sd1.CODE LIKE CONCAT (sd.CODE, '%')
      ) sd ON sd.dict_key = ode.business_owner_no
    WHERE
      ode.op_flag != 'DELETE'
  ) ode ON ode.drawdown_no = trvr.duebill_no
WHERE
  trvr.op_flag != 'DELETE'
  AND trvr.return_visit_type in ('LOAN', 'REPAYMENT', 'SPECIAL')
ORDER BY
  trvr.gmt_create DESC