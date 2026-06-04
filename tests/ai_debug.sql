SELECT
  tltc.id,
  tltc.national_id as idNumber,
  tltc.lawsuit_task_no as lawsuitTaskNo,
  if(
    LEFT(tltc.customer_no, 1) = 'E',
    '企业',
    '个人'
  ) as customerType,
  tltc.customer_name as customerName,
  tltc.customer_no as customerNo,
  CASE
    tltc.creditor_org
    WHEN 'xyd' THEN '小雨点'
    WHEN 'rfy' THEN '润飞扬'
    ELSE ''
  END as creditorOrg,
  tltc.product_no as productName,
  CASE
    tltc.lawsuit_stage
    WHEN 'getReady' THEN '准备'
    WHEN 'register' THEN '审理-已立案未审理结案'
    WHEN 'hearEndcase' THEN '审理-已审理结案'
    WHEN 'rehear' THEN '审理-二审/再审'
    WHEN 'execution' THEN '执行-已执行未结案'
    WHEN 'executionEndcase' THEN '执行-已执行结案'
    WHEN 'return' THEN '退回'
    ELSE ''
  END as lawsuitStage,
  if(tdd.settleStatus >= 1, '否', '是') as settleStatus,
  tltc.case_status as lawsuitStatus,
  DATE_FORMAT(tltc.enter_lawsuit_date, '%Y-%m-%d %H:%i:%S') as enterTime,
  tdd.overdue_day as overdueDay,
  tdd.os_tot_amount as osTotAmount,
  tdd.os_principal as osPrincipal,
  tdd.os_interest as osInterest,
  tdd.os_overdue_interest as osOverdueInterest,
  tdd.osOtherFee as osOtherFee,
  tdd.osPenaltyFee as osPenaltyFee,
  DATE_FORMAT(tltc.petition_last_date, '%Y-%m-%d %H:%i:%S') as petitionDate,
  tltc.petition_total_amount as petitionTotAmount,
  tltc.petition_principal as petitionPrincipal,
  tltc.petition_interest as petitionInterest,
  tltc.petition_penalty as petitionOverdueInterest,
  tltc.petition_guarantee_fee as petitionOtherFee,
  tltc.petition_penalty_fee as petitionPenaltyFee,
  tlti.court_num as courtNum,
  DATE_FORMAT(tlci.lawsuit_date, '%Y-%m-%d') as caseStartDate,
  tlii.register_code as executeNum,
  DATE_FORMAT(tlii.register_date, '%Y-%m-%d') as executeStartDate,
  tdd.dueBill_no as duebillNo
FROM
  post_loan.t_lawsuit_task_case tltc
  JOIN (
    SELECT
      tdd.task_no,
      group_concat(tdd.due_bill_no) as dueBill_no,
      sum(if(tdd.settle_status='否', 1, 0)) as settleStatus,
      ifnull(max(trs.overdue_day), 0) as overdue_day,
      ifnull(sum(trs.os_tot_amount), 0) as os_tot_amount,
      ifnull(sum(trs.os_principal), 0) as os_principal,
      ifnull(sum(trs.os_interest), 0) as os_interest,
      ifnull(sum(trs.os_overdue_interest), 0) as os_overdue_interest,
      ifnull(sum(trs.osOtherFee), 0) as osOtherFee,
      ifnull(sum(trs.osPenaltyFee), 0) as osPenaltyFee
    FROM
      post_loan.t_duebill_detail tdd
      LEFT JOIN (
        SELECT
          trs.duebill_no,
          max(trs.overdue_day) as overdue_day,
          sum(trs.os_tot_amount) as os_tot_amount,
          sum(trs.os_principal) as os_principal,
          sum(trs.os_interest) as os_interest,
          sum(trs.os_overdue_interest) as os_overdue_interest,
          sum(tofd.os_amount) as osOtherFee,
          sum(tofd2.os_amount) as osPenaltyFee
        FROM
          core_ms.t_duebill_info tdi
          JOIN post_loan.t_duebill_detail tdd ON tdd.due_bill_no = tdi.duebill_no
          and tdd.op_flag != 'DELETE'
          JOIN core_ms.t_repayment_schedule trs ON trs.duebill_no = tdi.duebill_no
          and trs.op_flag != 'DELETE'
          and trs.overdue_flag = 1
          and trs.setl_flag = 0
          LEFT JOIN core_ms.t_other_fee_detail tofd ON tofd.duebill_no = trs.duebill_no
          and tofd.period = trs.period
          and tofd.charge_id = 11
          and tofd.op_flag != 'DELETE'
          LEFT JOIN core_ms.t_other_fee_detail tofd2 ON tofd2.duebill_no = trs.duebill_no
          and tofd2.period = trs.period
          and tofd2.charge_id = 12
          and tofd2.op_flag != 'DELETE'
        WHERE
          tdi.op_flag != 'DELETE'
        GROUP BY
          trs.duebill_no
      ) trs ON trs.duebill_no = tdd.due_bill_no
    WHERE
      tdd.op_flag != 'DELETE'
    GROUP BY
      tdd.task_no
  ) tdd ON tdd.task_no = tltc.lawsuit_task_no
  LEFT JOIN (
    SELECT
      tlci.lawsuit_task_no,
      min(tlci.lawsuit_date) as lawsuit_date
    FROM
      post_loan.t_lawsuit_case_info tlci
    WHERE
      tlci.deleted = 0
      AND tlci.op_flag != 'DELETE'
      AND tlci.lawsuit_date is not null
    GROUP BY
      tlci.lawsuit_task_no
  ) tlci ON tlci.lawsuit_task_no = tltc.lawsuit_task_no
  LEFT JOIN (
    SELECT
      tlci.lawsuit_task_no,
      min(tlci.court_num) as court_num
    FROM
      post_loan.t_lawsuit_trial_info tlci
    WHERE
      tlci.deleted = 0
      AND tlci.op_flag != 'DELETE'
      AND tlci.court_num is not null
      AND tlci.insrance_stage = '1'
    GROUP BY
      tlci.lawsuit_task_no
  ) tlti ON tlti.lawsuit_task_no = tltc.lawsuit_task_no
  LEFT JOIN (
    SELECT
      tlci.lawsuit_task_no,
      min(tlci.register_date) as register_date,
      min(tlci.register_code) as register_code
    FROM
      post_loan.t_lawsuit_implement_info tlci
    WHERE
      tlci.deleted = 0
      AND tlci.op_flag != 'DELETE'
      AND (
        tlci.register_date is not null
        or tlci.register_code is not null
      )
    GROUP BY
      tlci.lawsuit_task_no
  ) tlii ON tlii.lawsuit_task_no = tltc.lawsuit_task_no
WHERE
  tltc.op_flag != 'DELETE'
  AND tltc.system_source = 4.0
  AND tltc.lawsuit_task_no = 'LSXYDE5570341670001'
ORDER BY
  tltc.enter_lawsuit_date DESC