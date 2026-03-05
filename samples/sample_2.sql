select batch_no, tttt.*, get_json_string(tttt.check_voucher_result,'voucher_type_no') voucher_type_no , get_json_string(tttt.check_voucher_result,'check_result_no') check_result_no
        ,get_json_string(tttt.check_voucher_result,'left_subject_no') left_subject_no,get_json_string(tttt.check_voucher_result,'right_subject_no') right_subject_no
        from (
        select result.*,
        case
        when result.right_value is null and result.left_value is not null  and get_json_string(result.left_value,'bizStatus') in ('1000','cancel')
        then JSON_OBJECT('check_result_no', 0, 'voucher_type_no', 0  ,'left_subject_no','','right_subject_no','')

        when result.right_value is not null and get_json_string(result.right_value,'tradeType') is not null  and get_json_string(result.right_value,'tradeType') ='CPAA'
        and get_json_string(result.right_value,'remark') ='充值' then JSON_OBJECT('check_result_no', 0, 'voucher_type_no', 9  ,'left_subject_no','','right_subject_no','')

        when result.right_value is not null and get_json_string(result.right_value,'tradeType') is not null  and get_json_string(result.right_value,'tradeType') ='CPUA'
        and get_json_string(result.right_value,'remark') like '内部转账%' then JSON_OBJECT('check_result_no', 0, 'voucher_type_no', 9  ,'left_subject_no','','right_subject_no','')

        when result.right_value is not null and get_json_string(result.right_value,'tradeType') is not null  and get_json_string(result.right_value,'tradeType') ='LCS'
        and get_json_string(result.right_value,'remark') ='充值' then JSON_OBJECT('check_result_no', 0, 'voucher_type_no', 9  ,'left_subject_no','','right_subject_no','')

        when result.right_value is not null and get_json_string(result.right_value,'tradeType') is not null  and get_json_string(result.right_value,'tradeType') ='WEB'
        and get_json_string(result.right_value,'remark') ='资金同名划转' then JSON_OBJECT('check_result_no', 0, 'voucher_type_no', 9  ,'left_subject_no','','right_subject_no','')

        when result.right_value is not null and get_json_string(result.right_value,'tradeType') is not null  and get_json_string(result.right_value,'tradeType') in('ISIR','HK')
        then JSON_OBJECT('check_result_no', 0, 'voucher_type_no', 9 ,'left_subject_no','','right_subject_no','' )

        when result.right_value is not null and get_json_string(result.right_value,'tradeType') is not null  and get_json_string(result.right_value,'tradeType') in('AINT','INT','JX')
        then JSON_OBJECT('check_result_no', 0, 'voucher_type_no', 8  ,'left_subject_no','','right_subject_no','')

        when result.right_value is not null and get_json_string(result.right_value,'tradeType') is not null  and get_json_string(result.right_value,'tradeType') ='FENC'
        and get_json_string(result.right_value,'dcFlag')='D'
        then JSON_OBJECT('check_result_no', 0, 'voucher_type_no', 6  ,'left_subject_no','1221990301','right_subject_no','10020108')

        when result.right_value is not null and get_json_string(result.right_value,'tradeType') is not null  and get_json_string(result.right_value,'tradeType') in('FENC')
        and get_json_string(result.right_value,'dcFlag')='C'
        then JSON_OBJECT('check_result_no', 0, 'voucher_type_no', 7,'left_subject_no','10020108','right_subject_no','1221990301' )

        when result.right_value is not null and get_json_string(result.right_value,'tradeType') is not null  and get_json_string(result.right_value,'tradeType') in('NPT1','NPBK','CPAA','CPAJ','CZTZ')
        and get_json_string(result.right_value,'dcFlag')='C'
        then JSON_OBJECT('check_result_no', 0, 'voucher_type_no', 2 ,'left_subject_no','10020108','right_subject_no','10020108' )

        when result.right_value is not null and get_json_string(result.right_value,'tradeType') is not null  and get_json_string(result.right_value,'tradeType') ='FEE'
        then JSON_OBJECT('check_result_no', 0, 'voucher_type_no', 10 ,'left_subject_no','','right_subject_no','')

        when result.left_value is not null and result.right_value is not null and get_json_string(result.right_value,'amount')=get_json_string(result.left_value,'amount')
        and DATE_FORMAT(result.trade_date,'%Y%m')=DATE_FORMAT(result.re_trade_date,'%Y%m') and get_json_string(result.right_value,'bizStatus')=get_json_string(result.left_value,'bizStatus')
        and get_json_string(result.right_value,'bizStatus')='0000'
        and get_json_string(result.left_value,'productNo') ='GYL-YLD-YSD'
        then JSON_OBJECT ( 'check_result_no', 0, 'voucher_type_no', 1 ,'left_subject_no','13030301','right_subject_no','10020108')

        when result.left_value is not null and result.right_value is not null and get_json_string(result.right_value,'amount')=get_json_string(result.left_value,'amount')
        and DATE_FORMAT(result.trade_date,'%Y%m')=DATE_FORMAT(result.re_trade_date,'%Y%m') and get_json_string(result.right_value,'bizStatus')=get_json_string(result.left_value,'bizStatus')
        and get_json_string(result.right_value,'bizStatus')='0000'
        and get_json_string(result.left_value,'productNo') !='GYL-YLD-YSD'
        then JSON_OBJECT ( 'check_result_no', 0, 'voucher_type_no', 1 ,'left_subject_no','13030101','right_subject_no','10020108')

        when result.left_value is not null and result.right_value is not null and get_json_string(result.right_value,'amount')=get_json_string(result.left_value,'amount')
        and DATE_FORMAT(result.trade_date,'%Y%m')>DATE_FORMAT(result.re_trade_date,'%Y%m')
        then JSON_OBJECT ( 'check_result_no', 1, 'voucher_type_no', 3 ,'left_subject_no','1221990605','right_subject_no','10020108')

        when result.left_value is not null and result.right_value is not null
        and (get_json_string(result.right_value,'amount')!=get_json_string(result.left_value,'amount') or get_json_string(result.right_value,'bizStatus')!=get_json_string(result.left_value,'bizStatus'))
        then JSON_OBJECT ( 'check_result_no', 2, 'voucher_type_no', 0 ,'left_subject_no','','right_subject_no','')

        else JSON_OBJECT('check_result_no', 2, 'voucher_type_no', 0 ,'left_subject_no','','right_subject_no','')
        end as check_voucher_result
        from
        (
        SELECT
        record.product_no,
        'zhaoshang_pay' channel,
        record.`trade_date`,
        record.`data_update_time`,
        case when record.left_key is not null and tt.right_key is not null then tt.right_key
        when record.left_key is not null and tt.right_key is null then record.left_key
        else null end as left_key,
        case when record.amount is null then null
        else
        JSON_OBJECT (
        'productNo',
        record.product_no,
        'amount',
        record.amount,
        'bizStatus',
        record.biz_status,
        'loanNumber',
        record.loan_number,
        'submitDate',
        record.submit_date,
        'data',record.left_data,
        'dataCreateTime',record.data_created_time,
        'loanType',1
        ) end AS left_value,
        tt.left_key left_key2,
        STR_TO_DATE(tt.re_trade_date,'%Y%m%d') re_trade_date,
        tt.right_key,
        CASE
        WHEN tt.right_key IS NULL THEN
        NULL ELSE JSON_OBJECT (
        'tradeType',
        tt.trade_type,
        'remark',
        tt.remark,
        'trsseq',
        tt.right_key,
        'amount',
        tt.amount,
        'loanNumber',
        tt.loan_number,
        'bizStatus',
        tt.business_status,
        'dcFlag',
        tt.dc_flag,
        'data',tt.right_data
        )
        END AS right_value
        FROM
        (

        SELECT case when trsref is null or trsref='' then t1.trsseq else trsref end as left_key, t1.trsdat re_trade_date, t1.trscod trade_type, abs(t1.trsamt) amount, t2.loan_number
        loan_number, t1.naryur remark ,
        t2.business_status,t1.trsseq right_key,t1.trsdir dc_flag,t1.right_data
        FROM (select *,
        JSON_OBJECT (
        'table_name','t_recon_zhaoshang_details',
        'eacnbr' ,eacnbr,
        'ccynbr' ,ccynbr,
        'ccytyp' ,ccytyp,
        'trsseq' ,trsseq,
        'trsdat' ,trsdat,
        'etytim' ,etytim,
        'trsdir' ,trsdir,
        'trsamt' ,trsamt,
        'onlbal' ,onlbal,
        'txtc2g' ,txtc2g,
        'txtcod' ,txtcod,
        'busref' ,busref,
        'trssts' ,trssts,
        'trsanl' ,trsanl,
        'busnbr' ,busnbr,
        'relacc' ,relacc,
        'relnam' ,relnam,
        'relbnk' ,relbnk,
        'reladr' ,reladr,
        'relbbk' ,relbbk,
        'trsref' ,trsref,
        'athflg' ,athflg,
        'busnam' ,busnam,
        'infflg' ,infflg,
        'naryur' ,naryur,
        'narext' ,narext,
        'reqnbr' ,reqnbr,
        'trscod' ,trscod,
        'vltdat' ,vltdat)
        right_data
        from payments.t_recon_zhaoshang_details  WHERE eacnbr='123907429910205'  and trscod in('AINT','CPAA','CPUA','ISIR','FENC','NPBK','NPT1','CPAJ') and DATE_FORMAT( trsdat, '%Y-%m-%d') >= '2025-07-01' AND DATE_FORMAT( trsdat, '%Y-%m-%d' ) <= '2025-07-01' and op_flag!='DELETE' ) t1 left JOIN payments.t_publish_pay_message t2
        ON t1.trsref = t2.sn and t2.sn is not null and t2.sn!=''



        ) tt

        FULL OUTER JOIN

        (
        SELECT
        *
        FROM
        (
        SELECT
        t1.product_no,
        t1.complete_time trade_date,
        t1.updated_at data_update_time,
        ifnull(t1.sn,t1.order_no) left_key,
        t1.amount,
        CASE

        WHEN t1.payment_status_id IN ( 3 ) THEN
        '0000'
        WHEN t1.payment_status_id IN ( 4 ) THEN
        '1000'
        WHEN t1.payment_status_id IN ( 5 ) THEN
        'cancel' ELSE '2000'
        END AS biz_status,
        t1.loan_number loan_number,
        t2.submit_date,
        CASE

        WHEN t2.payment_method_name IN ( 'lianlian pay', 'lianlian_outpay', 'zbank_pay_behalf', 'lianlianpay_morepyee' ) THEN
        'lianlian_pay'
        WHEN t2.payment_method_name = 'pingan_bank_pay' THEN
        'pingan_pay'
        WHEN t2.payment_method_name = 'zhaoshang_pay' THEN
        'zhaoshang_pay' ELSE payment_method_name
        END AS channel,
        t2.complete_time,
        DATE_FORMAT( t1.created_at, '%Y-%m-%d %H:%i:%s' ) data_created_time,
        JSON_OBJECT (
        'table_name','t_loan_payments',
        'req_sn' ,t1.req_sn,
        'sn' ,t1.sn,
        'scheduled_payment_id' ,t1.scheduled_payment_id,
        'payment_status_id' ,t1.payment_status_id,
        'amount' ,t1.amount,
        'loan_id' ,t1.loan_id,
        'clearance_date',DATE_FORMAT(t1.clearance_date,'%Y-%m-%d') ,
        'is_outgoing',t1.is_outgoing,
        'repayment_method_id' ,t1.repayment_method_id,
        'repayment_type_id' ,t1.repayment_type_id,
        'mer_id' ,t1.mer_id,
        'err_msg' ,t1.err_msg,
        'complete_time' ,DATE_FORMAT(t1.complete_time,'%Y-%m-%d') ,
        'is_cooperation',t1.is_cooperation,
        'repay_date' ,DATE_FORMAT(t1.repay_date,'%Y-%m-%d'),
        'payment_order_no',t1.payment_order_no,
        'account_id',t1.account_id ,
        'customer_id' ,t1.customer_id,
        'loan_number', t1.loan_number,
        'loan_status_id' ,t1.loan_status_id,
        'product_no', t1.product_no,
        'scheme_code', t1.scheme_code,
        'payment_scheme_code', t1.payment_scheme_code,
        'apr' ,t1.apr,
        'funding_success_date' ,DATE_FORMAT(t1.funding_success_date,'%Y-%m-%d') ,
        'order_no' ,t1.order_no,
        'yjf_contract_order_no',t1.yjf_contract_order_no,
        'late_fee_rule_id' ,t1.late_fee_rule_id,
        'cash_margin' ,t1.cash_margin,
        'installments' ,t1.installments,
        'i9_category', t1.i9_category,
        'contract_apr' ,t1.contract_apr,
        'report_apr_type' ,t1.report_apr_type,
        'really_apr' ,t1.really_apr,
        'credit_no',t1.credit_no
        )  left_data
        FROM
        (
        SELECT
        a.*,
        b.account_id,
        b.customer_id,
        b.loan_number,
        b.loan_status_id,
        b.product_no,
        b.scheme_code,
        b.payment_scheme_code,
        b.apr,
        b.funding_success_date,
        b.yjf_contract_order_no,
        b.late_fee_rule_id,
        b.cash_margin,
        b.installments,
        b.i9_category,
        b.contract_apr,
        b.report_apr_type,
        b.really_apr,
        b.credit_no,
        CONCAT( b.loan_number, '&amp;v1.0' ) order_no
        FROM
        alchemist.t_payments a
        LEFT JOIN alchemist.t_loans b ON a.loan_id = b.id
        WHERE
        a.is_outgoing = 1 and ((b.product_no not in ('2C','2C2') and a.created_at >= '2024-11-01 00:00:00') or a.created_at < '2024-11-01 00:00:00')
        ) t1
        LEFT JOIN payments.t_publish_pay_message t2 ON t1.sn = t2.sn
        WHERE
        DATE_FORMAT( t1.created_at, '%Y-%m-%d' ) >= '2025-07-01'
        AND DATE_FORMAT( t1.created_at, '%Y-%m-%d' ) <= '2025-07-01'
        AND t1.is_outgoing = 1 UNION ALL
        SELECT
        t1.product_no,
        t1.complete_time trade_date,
        t1.gmt_modify data_update_time,
        case when t2.sn is null or t2.sn='' then t1.loan_serial_number
        else t2.sn end as left_key,
        t1.amount,
        t1.biz_status,
        t1.duebill_no loan_number,
        t2.submit_date,
        t1.payment_channel_str channel,
        t1.complete_time,
        DATE_FORMAT( t1.gmt_create, '%Y-%m-%d %H:%i:%s' ) data_created_time,
        JSON_OBJECT(
        'table_name','t_payment_record',
        'serial_number',t1.serial_number,
        'loan_serial_number',t1.loan_serial_number,
        'contract_no' ,t1.contract_no,
        'product_no' ,t1.product_no,
        'duebill_no' ,t1.duebill_no,
        'customer_no' ,t1.customer_no,
        'order_no' ,t1.order_no,
        'application_no' ,t1.application_no,
        'payment_amount',t1.payment_amount,
        'clearance_date' ,DATE_FORMAT( t1.clearance_date, '%Y-%m-%d' ),
        'payment_status_id' ,t1.payment_status_id,
        'payment_channel' ,t1.payment_channel,
        'result_msg' ,t1.result_msg,
        'scheme_code' ,t1.scheme_code,
        'compensation_no',t1.compensation_no,
        'core_customer_no',t1.core_customer_no,
        'payee_customer_no' ,t1.payee_customer_no,
        'subsidy_interest_customer_no' ,t1.subsidy_interest_customer_no,
        'gur_type' ,t1.gur_type,
        'currency',t1.currency,
        'contract_rate' ,t1.contract_rate,
        'remark',t1.remark,
        'audit_time',DATE_FORMAT( t1.audit_time, '%Y-%m-%d' ),
        'payment_proof_remark' ,t1.payment_proof_remark,
        'complete_time',DATE_FORMAT( t1.complete_time, '%Y-%m-%d' ),
        'submit_date' ,DATE_FORMAT( t1.submit_date, '%Y-%m-%d' ),
        'affiliation' ,t1.affiliation,
        'funder_no' ,t1.funder_no,
        'transaction_date',DATE_FORMAT( t1.transaction_date, '%Y-%m-%d' ),
        'operator' ,t1.operator,
        'gmt_create' ,DATE_FORMAT( t1.gmt_create, '%Y-%m-%d' ),
        'gmt_modify' ,DATE_FORMAT( t1.gmt_modify, '%Y-%m-%d' ),
        'loan_mode' ,t1.loan_mode,
        'sub_payment_info' ,t1.sub_payment_info,
        'self_support' ,t1.self_support
        ) left_data
        FROM
        (
        SELECT
        a.*,
        CASE

        WHEN payment_channel IN ( 'zhaoshang_pay', 'zhaoshang_pay_public' ) THEN
        'zhaoshang_pay'
        WHEN payment_channel IN ( 'lianian_pay', 'lianlian_outpay', 'zbank_pay_behalf', 'lianlianpay_morepyee' ) THEN
        'lianlian_pay'
        WHEN payment_channel = 'xishang_pay' THEN
        'xs_pay' ELSE payment_channel
        END AS payment_channel_str,
        CASE

        WHEN payment_status_id IN ( 3 ) THEN
        '0000'
        WHEN payment_status_id IN ( 4 ) THEN
        '1000'
        WHEN payment_status_id IN ( 5 ) THEN
        'cancel' ELSE '2000'
        END AS biz_status,
        iFNULL( b.payment_amount, a.payment_amount ) amount
        FROM
        (select tpr.*,IFNULL(tbi.old_product_no,tpr.product_no) old_product_no from core_ms.t_payment_record  tpr left join core_ms.t_duebill_info tbi on tpr.duebill_no = tbi.duebill_no ) a
        LEFT JOIN ( SELECT payment_amount, duebill_no FROM core_ms.t_sub_duebill_info WHERE funder_no = 'XYD' ) b ON a.duebill_no = b.duebill_no
        where (a.gmt_create >= '2024-11-01 00:00:00' or (a.old_product_no not in ('2C','2C2') and a.gmt_create < '2024-11-01 00:00:00') )
        ) t1
        LEFT JOIN (
        SELECT
        *,
        CASE
        WHEN payment_method_name IN ( 'lianlian pay', 'lianlian_outpay', 'zbank_pay_behalf', 'lianlianpay_morepyee' ) THEN
        'lianlian_pay'
        WHEN payment_method_name = 'pingan_bank_pay' THEN
        'pingan_pay'
        WHEN payment_method_name = 'zhaoshang_pay' THEN
        'zhaoshang_pay' ELSE payment_method_name
        END AS payment_method_name_str
        FROM
        payments.t_publish_pay_message
        ) t2 ON t1.loan_serial_number=t2.order_no
        WHERE
        DATE_FORMAT( t1.gmt_create, '%Y-%m-%d' ) >='2025-07-01'
        AND DATE_FORMAT( t1.gmt_create, '%Y-%m-%d' ) <= '2025-07-01'
        ) record_tem
        WHERE
        channel = 'zhaoshang_pay'
        ) record
        ON record.left_key = tt.left_key
        ) result

        ) tttt order by tttt.right_key,tttt.left_key,tttt.channel limit 1,100
