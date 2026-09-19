-- Every audit check (except the INFO-only ones) must report PASS.
select audit_check, pass_or_fail, detail
  from {{ ref('mart_governance_audit') }}
 where pass_or_fail = 'FAIL'
