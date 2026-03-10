SELECT
  count(1)
FROM
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
    FROM
      (
        SELECT
          *
        FROM
          (
            SELECT
              a.duebill_no schduebill,
              sum(b.sch_interest) sumsch
            FROM
              core_ms.t_duebill_info a
              INNER JOIN core_ms.t_repayment_schedule b ON a.duebill_no = b.duebill_no
            WHERE
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
              AND a.op_flag != 'DELETE'
              AND b.op_flag != 'DELETE'
            GROUP BY
              a.duebill_no
          ) aa, ( SELECT a.duebill_no accduebill, sum(c.receivable_interest) sumacc FROM core_ms.t_duebill_info a INNER JOIN account_ms.c_accrual_detail c ON a.duebill_no = IF(c.duebill_no like '%-0%', LEFT (c.duebill_no, LENGTH(c.duebill_no) - 3), c.duebill_no) AND c.accrual_type != '4' WHERE ((a.clear_date > DATE_ADD(CURRENT_DATE(), INTERVAL -2 MONTH) AND a.clear_date < CURRENT_DATE() AND a.duebill_status = 3) OR (a.end_date > DATE_ADD(CURRENT_DATE(), INTERVAL -2 MONTH) AND a.end_date <= CURRENT_DATE() AND a.duebill_status != 3) ) AND a.op_flag != 'DELETE' AND c.op_flag != 'DELETE' GROUP BY a.duebill_no ) bb
        WHERE
          aa.schduebill = bb.accduebill
          AND aa.sumsch != bb.sumacc
      ) d
      INNER JOIN core_ms.t_duebill_info t ON d.schduebill = t.duebill_no
  ) f
WHERE
  NOT EXISTS(SELECT 1 FROM core_ms.t_buy_back_record e WHERE e.duebill_no = f.duebill_no AND e.gmt_create >= CURRENT_DATE AND e.business_status = 3);