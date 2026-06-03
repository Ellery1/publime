SELECT
  a.agreement_no AS loanNo,
  a.agreement_file_id AS fileNo,
  b.`name` AS contractName,
  sd.dict_name AS contractType,
  a.agreement_type AS contractTypeCode,
  0 AS viewType,
  'pdf' AS fileType,
  creditNoFetch.agreement_no AS creditNo,
  tdi.loan_mode AS loanModel,
  case
    tdi.duebill_type
    when 5 then '借新还旧'
    else '新增'
  end AS loanType,
  MAX(CONVERT(d.file_id, SIGNED)) AS reportEvidenceFileNo
FROM
  esign.agreement_sign_result a
  INNER JOIN esign.config_agreement_template b ON a.template_code = b.`code`
  AND b.op_flag != 'DELETE'
  LEFT JOIN esign.esign_evidence_bing_relation d ON a.loan_number = d.contract_no
  AND a.template_code = d.template_code
  AND (
    d.sign_sn IS NULL
    OR a.sign_sn = d.sign_sn
  )
  AND d.op_flag != 'DELETE'
  LEFT JOIN (
    SELECT
      sd1.dict_key,
      sd1.dict_name
    FROM
      xyd_config.s_dict sd1
      INNER JOIN(
        SELECT
          CODE
        FROM
          xyd_config.s_dict
        WHERE
          dict_key = 'agreement_type'
          and op_flag != 'DELETE'
      ) AS sd ON sd1.CODE LIKE CONCAT(sd.CODE, '%')
  ) sd ON a.agreement_type = sd.dict_key
  LEFT JOIN (
    SELECT
      a.agreement_no,
      'LN20251010162446951480' as loan_number
    FROM
      esign.agreement_sign_result a
    WHERE
      a.loan_number = 'CA20251010162032717470'
      and a.agreement_type = 'credit_agreement'
      AND a.op_flag != 'DELETE'
      and a.effective = 1
      and a.valid = 1
    order by
      id desc
    limit
      1
  ) creditNoFetch on creditNoFetch.loan_number = a.loan_number
  LEFT JOIN core_ms.t_duebill_info tdi ON a.loan_number = tdi.duebill_no
  AND tdi.op_flag != 'DELETE'
WHERE
  a.loan_number = 'LN20251010162446951480'
  and a.agreement_type in (
    'withdrawal_apply',
    'withdrawal_loan_contract',
    'quota_notice',
    'credit_limit_ctr',
    'entrusted_grt_ctr',
    'entrusted_grt_ctr_no_reserve',
    'xydxd_entrusted_grt_ctr',
    'fdb',
    'max_guarantee_letter'
  )
  and a.effective = 1
  and a.valid = 1
  AND a.op_flag != 'DELETE'
GROUP BY
  a.agreement_no,
  a.agreement_file_id,
  b.`name`,
  sd.dict_name,
  a.agreement_type,
  creditNoFetch.agreement_no,
  tdi.loan_mode,
  tdi.duebill_type
UNION ALL
SELECT
  NULL AS loanNo,
  a.agreement_file_id AS fileNo,
  b.`name` AS contractName,
  sd.dict_name AS contractType,
  a.agreement_type AS contractTypeCode,
  0 AS viewType,
  'pdf' AS fileType,
  NULL AS creditNo,
  NULL AS loanModel,
  NULL AS loanType,
  MAX(CONVERT(d.file_id, SIGNED)) AS reportEvidenceFileNo
FROM
  esign.agreement_sign_result a
  INNER JOIN esign.config_agreement_template b ON a.template_code = b.`code`
  AND b.op_flag != 'DELETE'
  LEFT JOIN esign.esign_evidence_bing_relation d ON a.loan_number = d.contract_no
  AND a.template_code = d.template_code
  AND (
    d.sign_sn IS NULL
    OR a.sign_sn = d.sign_sn
  )
  AND d.op_flag != 'DELETE'
  LEFT JOIN (
    SELECT
      sd1.dict_key,
      sd1.dict_name
    FROM
      xyd_config.s_dict sd1
      INNER JOIN(
        SELECT
          CODE
        FROM
          xyd_config.s_dict
        WHERE
          dict_key = 'agreement_type'
          and op_flag != 'DELETE'
      ) AS sd ON sd1.CODE LIKE CONCAT(sd.CODE, '%')
  ) sd ON a.agreement_type = sd.dict_key
WHERE
  a.loan_number = 'CA20251010162032717470'
  and a.agreement_type = 'credit_agreement'
  and a.effective = 1
  and a.valid = 1
  AND a.op_flag != 'DELETE'
GROUP BY
  a.agreement_file_id,
  b.`name`,
  sd.dict_name,
  a.agreement_type
UNION ALL
  (
    SELECT
      NULL AS loanNo,
      tgfi.file_id AS fileNo,
      '代偿证明' AS contractName,
      '代偿证明' AS contractType,
      'DUEBILL_COMPENSATE_FILE' AS contractTypeCode,
      0 AS viewType,
      'pdf' AS fileType,
      NULL AS reportEvidenceFileNo,
      NULL AS creditNo,
      NULL AS loanModel,
      NULL AS loanType
    FROM
      core_ms.t_generated_file_info tgfi
    WHERE
      tgfi.business_id = 'LN20251010162446951480'
      and tgfi.file_type = 'DUEBILL_COMPENSATE_FILE'
      and tgfi.del_flag = 0
      AND tgfi.op_flag != 'DELETE'
    order by
      id
    limit
      1
  )
UNION ALL
  (
    SELECT
      NULL AS loanNo,
      tgfi.file_id AS fileNo,
      '结清证明' AS contractName,
      '结清证明' AS contractType,
      'CAPITAL_DUEBILL_CLEAR_FILE' AS contractTypeCode,
      0 AS viewType,
      'pdf' AS fileType,
      NULL AS reportEvidenceFileNo,
      NULL AS creditNo,
      NULL AS loanModel,
      NULL AS loanType
    FROM
      core_ms.t_generated_file_info tgfi
    WHERE
      tgfi.business_id = 'LN20251010162446951480'
      and tgfi.file_type = 'CAPITAL_DUEBILL_CLEAR_FILE'
      and tgfi.del_flag = 0
      AND tgfi.op_flag != 'DELETE'
    order by
      id
    limit
      1
  )
UNION ALL
  (
    SELECT
      NULL AS loanNo,
      tgfi.file_id AS fileNo,
      '债转证明' AS contractName,
      '债转证明' AS contractType,
      'DUEBILL_DEBT_TRANSFER_FILE' AS contractTypeCode,
      0 AS viewType,
      'pdf' AS fileType,
      NULL AS reportEvidenceFileNo,
      NULL AS creditNo,
      NULL AS loanModel,
      NULL AS loanType
    FROM
      core_ms.t_generated_file_info tgfi
    WHERE
      tgfi.business_id = 'LN20251010162446951480'
      and tgfi.file_type = 'DUEBILL_DEBT_TRANSFER_FILE'
      and tgfi.del_flag = 0
      AND tgfi.op_flag != 'DELETE'
    order by
      id
    limit
      1
  )
UNION ALL
  (
    SELECT
      tpcr.loan_number AS loanNo,
      tpcr.filesystem_id AS fileNo,
      '放款凭证' AS contractName,
      '放款凭证' AS contractType,
      'EXIST_FILE_LOAN_PROOF' AS contractTypeCode,
      0 AS viewType,
      'pdf' AS fileType,
      NULL AS reportEvidenceFileNo,
      NULL AS creditNo,
      NULL AS loanModel,
      NULL AS loanType
    FROM
      payments.t_payment_certificate_record tpcr
    WHERE
      tpcr.loan_number = 'LN1778748153904FW8'
      AND tpcr.filesystem_id is not null
      AND tpcr.op_flag != 'DELETE'
    order by
      tpcr.id
    limit
      1
  )
UNION ALL
SELECT
  NULL AS loanNo,
  NULL AS fileNo,
  '欠款明细表' AS contractName,
  '欠款明细表' AS contractType,
  'HEAR_APPLY_OVERDUE_DETAIL' AS contractTypeCode,
  1 AS viewType,
  'xlsx' AS fileType,
  NULL AS reportEvidenceFileNo,
  NULL AS creditNo,
  NULL AS loanModel,
  NULL AS loanType
UNION ALL
SELECT
  NULL AS loanNo,
  NULL AS fileNo,
  '还款计划表' AS contractName,
  '还款计划表' AS contractType,
  'HEAR_APPLY_REPAYMENT_PLAN' AS contractTypeCode,
  1 AS viewType,
  'xlsx' AS fileType,
  NULL AS reportEvidenceFileNo,
  NULL AS creditNo,
  NULL AS loanModel,
  NULL AS loanType
UNION ALL
SELECT
  NULL AS loanNo,
  NULL AS fileNo,
  '还款明细表' AS contractName,
  '还款明细表' AS contractType,
  'EXIST_FILE_REPAY_DETAIL' AS contractTypeCode,
  1 AS viewType,
  'xlsx' AS fileType,
  NULL AS reportEvidenceFileNo,
  NULL AS creditNo,
  NULL AS loanModel,
  NULL AS loanType
LIMIT
  0, 10001