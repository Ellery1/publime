SELECT
  tdi.product_no AS productNo,
  xc.NAME AS productName,
  yhxi.lastName AS name,
  yhxi.customer_no AS customerNo,
  yhxi.lastPhone AS phone,
  if (yhxi.lastGender = 1, '先生', '女士') AS sex,
  MIN (date_format (trs.sch_date, '%Y年%m月%d日')) AS originDate,
  SUM (trs.os_tot_amount) AS overdueAmount,
  COUNT (DISTINCT tdi.duebill_no) AS overdueNumber,
  SUM (
    CASE
      WHEN tdi.loan_mode IN ('0', '3', '4') THEN trs.os_tot_amount
      ELSE 0
    END
  ) AS xydOverdueAmount,
  COUNT (
    DISTINCT (
      CASE
        WHEN tdi.loan_mode IN ('0', '3', '4') THEN tdi.duebill_no
      END
    )
  ) AS xydOverdueNumber,
  SUM (
    CASE
      WHEN tdi.loan_mode IN ('1', '2')
      AND tdi.funder_no = 'E8044476340' THEN trs.os_tot_amount
      ELSE 0
    END
  ) AS fundOverdueAmount,
  COUNT (
    DISTINCT (
      CASE
        WHEN tdi.loan_mode IN ('1', '2')
        AND tdi.funder_no = 'E8044476340' THEN tdi.duebill_no
      END
    )
  ) AS fundOverdueNumber,
  cardOne.bank_name AS classOnebankName,
  RIGHT (cardOne.bank_card_number, 4) AS classOneBankCardLast4,
  MAX (tdi.duebill_no) AS jobId,
  MAX (trs.overdue_day) AS overdueDay,
  GROUP_CONCAT (tdi.duebill_no) as duebillNoList
FROM
  core_ms.t_duebill_info tdi
  INNER JOIN core_ms.t_repayment_schedule trs ON trs.duebill_no = tdi.duebill_no
  and trs.overdue_flag = 1
  and trs.setl_flag = 0
  and trs.op_flag != 'DELETE'
  INNER JOIN xyd_config.t_product xc ON xc.product_no = tdi.product_no
  and xc.op_flag != 'DELETE'
  INNER JOIN (
    SELECT
      uc.customer_no,
      if (uc.customer_type = 'person', up.name, up2.name) AS lastName,
      CAST (
        SUBSTRING (
          if (
            uc.customer_type = 'person',
            up.national_id,
            up2.national_id
          ),
          17,
          1
        ) AS UNSIGNED
      ) % 2 AS lastGender,
      if (uc.customer_type = 'person', up.phone, up2.phone) AS lastPhone
    FROM
      titan.u_customer uc
      LEFT JOIN titan.u_person up ON uc.customer_no = up.customer_no
      and up.op_flag != 'DELETE'
      LEFT JOIN titan.u_company ucom ON uc.customer_no = ucom.customer_no
      and ucom.op_flag != 'DELETE'
      LEFT JOIN titan.u_person up2 ON ucom.legal_user_no = up2.customer_no
      and up2.op_flag != 'DELETE'
    WHERE
      uc.op_flag != 'DELETE'
      AND uc.customer_no in ('P7569677040', 'P1311269173')
  ) yhxi ON tdi.customer_no = yhxi.customer_no
  and length (yhxi.lastGender) > 0
  INNER JOIN (
    SELECT
      t3.bank_name,
      t3.bank_card_number,
      t3.customer_no
    FROM
      titan.d_apply_bank_card t3
    WHERE
      t3.id IN (
        SELECT
          MAX (t2.id) AS idNew
        FROM
          titan.d_apply_bank_card t2
        WHERE
          t2.bank_card_number IN (
            SELECT
              t1.bind_pri_card
            FROM
              titan.d_apply_bank_card t1
              INNER JOIN (
                SELECT
                  customer_no,
                  MAX (id) AS id
                FROM
                  titan.d_apply_bank_card
                WHERE
                  op_flag != 'DELETE'
                  AND account_type = 'xi_shang'
                  AND product_no = 'SJD-BZHCP-JYD'
                  AND customer_no IN ('P7569677040', 'P1311269173')
                GROUP BY
                  customer_no
              ) t ON t1.id = t.id
            WHERE
              t1.op_flag != 'DELETE'
          )
          AND t2.op_flag != 'DELETE'
          AND t2.customer_no IN ('P7569677040', 'P1311269173')
          AND t2.product_no = 'SJD-BZHCP-JYD'
        GROUP BY
          t2.customer_no
      )
  ) cardOne ON tdi.customer_no = cardOne.customer_no
  LEFT JOIN (
    SELECT
      customer_no,
      MAX (complanint) complanint
    FROM
      post_loan.t_collection_task
    WHERE
      op_flag != 'DELETE'
    GROUP BY
      customer_no
  ) tct ON tct.customer_no = tdi.customer_no
WHERE
  tdi.op_flag != 'DELETE'
  AND (
    tct.complanint = 0
    or tct.complanint IS NULL
  )
  AND tdi.customer_no IN ('P7569677040', 'P1311269173')
  AND tdi.loan_mode IN (0, 3, 4, 1, 2)
  AND yhxi.lastPhone not in (SELECT tb.phone FROM post_loan.t_blacklist tb WHERE tb.op_flag != 'DELETE' AND tb.scene like '%ai_voice%' AND tb.deleted = 0)
  AND tdi.product_no = 'SJD-BZHCP-JYD'
GROUP BY
  tdi.product_no,
  xc.NAME,
  yhxi.lastName,
  yhxi.customer_no,
  yhxi.lastPhone,
  yhxi.lastGender,
  cardOne.bank_name,
  cardOne.bank_card_number
HAVING
  SUM (trs.os_tot_amount) >= 1.00
  AND SUM (trs.os_tot_amount) <= 111111.00