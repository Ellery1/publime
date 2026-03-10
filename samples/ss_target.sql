SELECT
  count(1)
from
  (
    SELECT
      t.duebill_no,
      d.sumsch '还款计划总应收',
      d.sumacc '计提总额',
      d.sumsch - d.sumacc '差额',
      t.loan_mode,
      t.clear_date,
      t.settlement_date,
      t.end_date,
      t.payment_time
    from
      (
        SELECT
          *
        from
          (
            SELECT
              a.duebill_no schduebill,
              sum(b.sch_interest) sumsch
            FROM
              core_ms.t_duebill_info a
              inner join core_ms.t_repayment_schedule b on a.duebill_no = b.duebill_no
            where
              (
                (
                  a.clear_date > DATE_ADD(CURRENT_DATE(), INTERVAL -2 MONTH)
                  and a.clear_date < CURRENT_DATE()
                  and a.duebill_status = 3
                )
                or (
                  a.end_date > DATE_ADD(CURRENT_DATE(), INTERVAL -2 MONTH)
                  and a.end_date <= CURRENT_DATE()
                  and a.duebill_status != 3
                )
              )
              and a.op_flag != 'DELETE'
              and b.op_flag != 'DELETE'
            GROUP by
              a.duebill_no
          ) aa,
          (
            SELECT
              a.duebill_no accduebill,
              sum(c.receivable_interest) sumacc
            FROM
              core_ms.t_duebill_info a
              inner join account_ms.c_accrual_detail c on a.duebill_no = IF(
                c.duebill_no like '%-0%',
                LEFT(c.duebill_no, LENGTH(c.duebill_no) - 3),
                c.duebill_no
              )
              and c.accrual_type != '4'
            where
              (
                (
                  a.clear_date > DATE_ADD(CURRENT_DATE(), INTERVAL -2 MONTH)
                  and a.clear_date < CURRENT_DATE()
                  and a.duebill_status = 3
                )
                or (
                  a.end_date > DATE_ADD(CURRENT_DATE(), INTERVAL -2 MONTH)
                  and a.end_date <= CURRENT_DATE()
                  and a.duebill_status != 3
                )
              )
              and a.op_flag != 'DELETE'
              and c.op_flag != 'DELETE'
            GROUP by
              a.duebill_no
          ) bb
        where
          aa.schduebill = bb.accduebill
          and aa.sumsch != bb.sumacc
      ) d
      inner join core_ms.t_duebill_info t on d.schduebill = t.duebill_no
  ) f
WHERE
  NOT EXISTS (
    SELECT
      1
    FROM
      core_ms.t_buy_back_record e
    WHERE
      e.duebill_no = f.duebill_no
      and e.gmt_create >= CURRENT_DATE
      and e.business_status = 3
  );