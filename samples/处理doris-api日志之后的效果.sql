with t_repay_record as (
  SELECT
    t.task_no,
    trr.gmt_create,
    sum(tdd.trans_amount) as amount
  FROM
    core_ms.t_repay_record trr
    join post_loan.t_duebill_detail t on t.op_flag != 'DELETE'
    and t.due_bill_no = trr.duebill_no
    and t.business_type = 'LAWSUIT'
    JOIN core_ms.t_deduction_detail tdd ON trr.repay_order_no = tdd.repay_order_no
    and tdd.`status` = 3
    JOIN core_ms.t_deduction td ON td.id = tdd.deduction_id
    and td.`status` in (3, 5)
  WHERE
    trr.op_flag != 'DELETE'
    AND trr.cancel_repay_id is null
    and trr.gmt_create >= '2026-06-30 23:59:59'
    and trr.gmt_create <= '2025-05-01 00:00:00'
  GROUP BY
    t.task_no,
    trr.gmt_create
  union all
  SELECT
    t.task_no,
    c.gmt_create,
    sum(- tdd.trans_amount) as amount
  FROM
    core_ms.t_repay_record trr
    join post_loan.t_duebill_detail t on t.op_flag != 'DELETE'
    and t.due_bill_no = trr.duebill_no
    and t.business_type = 'LAWSUIT'
    join core_ms.t_repay_record c on trr.id = c.cancel_repay_id
    JOIN core_ms.t_deduction_detail tdd ON trr.repay_order_no = tdd.repay_order_no
    and tdd.`status` = 3
    JOIN core_ms.t_deduction td ON td.id = tdd.deduction_id
    and td.`status` in (3, 5)
  WHERE
    trr.op_flag != 'DELETE'
    AND c.cancel_repay_id is not null
    and trr.gmt_create >= '2026-06-30 23:59:59'
    and trr.gmt_create <= '2025-05-01 00:00:00'
  GROUP BY
    t.task_no,
    c.gmt_create
)
select
  tltc.lawsuit_task_no,
  tltc.customer_name,
  tltc.customer_no,
  tltc.creditor_org,
  ifnull(sd.dict_name, tltc.lawsuit_stage) as lawsuit_stage,
  DATE_FORMAT(tltc.enter_lawsuit_date, '%Y-%m-%d %H:%i:%S') as enter_lawsuit_date,
  sum(trr.amount) as repayAmount,
  sum(er.amount) as repayAmountEnter,
  sum(cr.amount) as repayAmountLawsuit,
  sum(ir.amount) as repayAmountExecute
from
  post_loan.t_lawsuit_task_case tltc
  join t_repay_record trr on trr.task_no = tltc.lawsuit_task_no
  left join t_repay_record er on er.task_no = tltc.lawsuit_task_no
  and er.gmt_create >= tltc.enter_lawsuit_date
  left join (
    select
      tlci.lawsuit_task_no,
      min(tlci.lawsuit_date) as lawsuit_date
    from
      post_loan.t_lawsuit_case_info tlci
    where
      tlci.deleted = 0
      and tlci.op_flag != 'DELETE'
      and tlci.lawsuit_date is not null
    group by
      tlci.lawsuit_task_no
  ) tlci on tlci.lawsuit_task_no = tltc.lawsuit_task_no
  left join t_repay_record cr on cr.task_no = tltc.lawsuit_task_no
  and cr.gmt_create >= tlci.lawsuit_date
  left join (
    select
      tlci.lawsuit_task_no,
      min(tlci.register_date) as register_date,
      min(tlci.register_code) as register_code
    from
      post_loan.t_lawsuit_implement_info tlci
    where
      tlci.deleted = 0
      and tlci.op_flag != 'DELETE'
      and (
        tlci.register_date is not null
        or tlci.register_code is not null
      )
    group by
      tlci.lawsuit_task_no
  ) tlii on tlii.lawsuit_task_no = tltc.lawsuit_task_no
  left join t_repay_record ir on ir.task_no = tltc.lawsuit_task_no
  and ir.gmt_create >= tlii.register_date
  LEFT JOIN (
    SELECT
      sd1.dict_key,
      sd1.dict_name
    FROM
      xyd_config.s_dict sd1
      JOIN(
        SELECT
          CODE
        FROM
          xyd_config.s_dict
        WHERE
          dict_key in('lawsuit_status')
          and op_flag != 'DELETE'
      ) AS sd ON sd1.CODE LIKE CONCAT(sd.CODE, '%')
  ) sd ON sd.dict_key = tltc.lawsuit_stage
where
  tltc.op_flag != 'DELETE'
  and tltc.customer_name = '尤瑞'
  and tltc.customer_no = 'P1086543133'
  and tltc.lawsuit_stage in ('getReady', 'register', 'hearEndcase')
  and tltc.enter_lawsuit_date >= '2026-05-14 23:59:59'
  and tltc.enter_lawsuit_date <= '2026-05-13 00:00:00'
  and tlci.lawsuit_date >= '2026-06-30 23:59:59'
  and tlci.lawsuit_date <= '2025-05-01 00:00:00'
group by
  tltc.lawsuit_task_no,
  tltc.customer_name,
  tltc.customer_no,
  tltc.creditor_org,
  ifnull(sd.dict_name, tltc.lawsuit_stage),
  tltc.enter_lawsuit_date
order by
  tltc.enter_lawsuit_date desc
