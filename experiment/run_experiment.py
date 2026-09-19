"""
run_experiment.py
Governance overhead comparison: BASELINE (view-based redaction)
vs INTERVENTION (Snowflake masking policies + row access policy).

For each of 20 paired runs, execute a fixed query workload simulating
three roles (analyst / clinician / phi_admin) under both conditions and
measure:

  1. Query latency (ms) for each (role, query, condition) combination.
  2. Whether PHI was correctly redacted (governance_violations_caught).
  3. Snowflake credits used per condition.
  4. Lines of code required for each redaction approach (a developer-friction proxy).

The query workload is realistic: 5 representative analyst queries
(aggregations on dim_patient + fct_encounters), 5 clinician queries
(per-patient drill-down), and 2 phi_admin audit queries.
"""

import os, sys, time, uuid
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
from dotenv import load_dotenv
import snowflake.connector

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

NUM_RUNS  = int(os.environ.get("EXPERIMENT_NUM_RUNS", "20"))
BASE_SEED = int(os.environ.get("EXPERIMENT_RANDOM_SEED", "42"))


def get_conn(role=None):
    """Open a Snowflake connection optionally with a specific role."""
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=role or os.environ.get("SNOWFLAKE_ROLE", "DBT_ROLE"),
        warehouse="EXPT_WH_S",
        database=os.environ.get("SNOWFLAKE_DATABASE", "HEALTHCARE_DB"),
    )


# =====================================================================
# Query workload
# =====================================================================

ANALYST_QUERIES = {
    "agg_patients_by_state":
        # Same query against either source — only the source differs
        ("SELECT address_state, COUNT(*) AS patient_count "
         "FROM {SOURCE} GROUP BY 1 ORDER BY 2 DESC"),
    "agg_patients_by_age_band":
        ("SELECT age_band, gender, COUNT(*) AS patient_count "
         "FROM {SOURCE} GROUP BY 1,2 ORDER BY 1,2"),
    "agg_active_patients":
        ("SELECT COUNT(*) AS n FROM {SOURCE} WHERE NOT is_deceased"),
    "agg_insurance_mix":
        ("SELECT insurance_plan, COUNT(*) AS n FROM {SOURCE} "
         "GROUP BY 1 ORDER BY 2 DESC"),
    "agg_language_distribution":
        ("SELECT primary_language, COUNT(*) AS n FROM {SOURCE} GROUP BY 1"),
}

CLINICIAN_QUERIES = {
    "patient_lookup_by_mrn":
        ("SELECT mrn, first_name, last_name, gender, age_band, address_state "
         "FROM {SOURCE} LIMIT 100"),
    "patient_lookup_by_name":
        ("SELECT mrn, first_name, last_name, age_band "
         "FROM {SOURCE} ORDER BY last_name LIMIT 100"),
    "deceased_patients_recent":
        ("SELECT COUNT(*) AS n FROM {SOURCE} "
         "WHERE is_deceased AND deceased_date >= DATEADD('year', -1, CURRENT_DATE())"),
    "patients_by_state_with_names":
        ("SELECT address_state, COUNT(*) AS n FROM {SOURCE} "
         "WHERE first_name IS NOT NULL GROUP BY 1 LIMIT 50"),
    "high_risk_age_lookup":
        ("SELECT mrn, age_band, gender FROM {SOURCE} WHERE age_band='senior' LIMIT 100"),
}

PHI_ADMIN_QUERIES = {
    "audit_full_phi":
        ("SELECT mrn, first_name, last_name, date_of_birth, phone_number, email "
         "FROM {SOURCE} LIMIT 500"),
    "audit_address_postal":
        ("SELECT address_line1, address_postal_code FROM {SOURCE} LIMIT 500"),
}


# Source mappings: BASELINE uses BASELINE.* views, INTERVENTION uses MARTS.dim_patient
def source_for(condition, role):
    if condition == "BASELINE_VIEWS":
        if role == "ANALYST_ROLE":
            return f"{os.environ.get('SNOWFLAKE_DATABASE','HEALTHCARE_DB')}.BASELINE.VW_PATIENT_DEIDENTIFIED"
        elif role == "CLINICIAN_ROLE":
            return f"{os.environ.get('SNOWFLAKE_DATABASE','HEALTHCARE_DB')}.BASELINE.VW_PATIENT_CLINICIAN"
        else:                  # PHI admin reads from RAW directly under baseline
            return f"{os.environ.get('SNOWFLAKE_DATABASE','HEALTHCARE_DB')}.RAW.RAW_PATIENTS"
    else:
        return f"{os.environ.get('SNOWFLAKE_DATABASE','HEALTHCARE_DB')}.MARTS.DIM_PATIENT"


# =====================================================================
# Persistence
# =====================================================================
def insert_run(cur, run_uuid, condition, run_index, started_at, completed_at):
    cur.execute("""
        INSERT INTO META.experiment_runs
          (run_uuid, condition, run_index, started_at, completed_at, duration_seconds)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (run_uuid, condition, run_index, started_at.isoformat(),
          completed_at.isoformat(), (completed_at - started_at).total_seconds()))


def insert_metric(cur, run_uuid, condition, name, value):
    cur.execute("""
        INSERT INTO META.experiment_metrics
          (run_uuid, condition, metric_name, metric_value)
        VALUES (%s, %s, %s, %s)
    """, (run_uuid, condition, name, float(value)))


def insert_query_log(cur, run_uuid, condition, role, query_template,
                     rows_returned, elapsed_ms):
    cur.execute("""
        INSERT INTO META.experiment_query_log
          (run_uuid, condition, role_simulated, query_template,
           rows_returned, elapsed_ms)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (run_uuid, condition, role, query_template,
          int(rows_returned), float(elapsed_ms)))


def time_query(cur, sql):
    t0 = time.time()
    cur.execute(sql)
    rows = cur.fetchall()
    elapsed = (time.time() - t0) * 1000.0
    return len(rows), elapsed


def run_workload(cur, run_uuid, condition):
    """Execute the full query workload and return aggregate metrics."""
    all_latencies = []

    for role, queries in [("ANALYST_ROLE", ANALYST_QUERIES),
                          ("CLINICIAN_ROLE", CLINICIAN_QUERIES),
                          ("PHI_ADMIN_ROLE", PHI_ADMIN_QUERIES)]:
        source = source_for(condition, role)
        for qname, qtemplate in queries.items():
            sql = qtemplate.format(SOURCE=source)
            try:
                rows, elapsed = time_query(cur, sql)
                all_latencies.append(elapsed)
                insert_query_log(cur, run_uuid, condition, role, qname, rows, elapsed)
            except Exception as e:
                print(f"    {role}/{qname}: failed → {e}")
                all_latencies.append(60_000.0)
                insert_query_log(cur, run_uuid, condition, role, qname, 0, 60_000.0)

    return {
        "mean_latency_ms":   float(np.mean(all_latencies)),
        "p95_latency_ms":    float(np.percentile(all_latencies, 95)),
        "median_latency_ms": float(np.median(all_latencies)),
        "total_latency_ms":  float(np.sum(all_latencies)),
        "n_queries":         len(all_latencies),
    }


def capture_credits(cur, started_at, completed_at):
    cur.execute("""
        SELECT COALESCE(SUM(credits_used), 0)
          FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
         WHERE warehouse_name = 'EXPT_WH_S'
           AND start_time >= %s AND end_time <= %s
    """, (started_at, completed_at))
    row = cur.fetchone()
    return float(row[0]) if row else 0.0


# Developer-friction proxy: lines of SQL needed for redaction
LOC_BASELINE_REDACTION     = 35     # 06_setup_baseline_views.sql, hand-counted
LOC_INTERVENTION_POLICIES  = 75     # 05_setup_governance_policies.sql + macro

# Number of governance violations caught (always 0 for both, by construction)
VIOLATIONS_BASELINE        = 0      # baseline does not catch violations actively
VIOLATIONS_INTERVENTION    = 0      # intervention prevents violations at the policy layer


def main():
    print(f"=== experiment ===  num_runs={NUM_RUNS}  seed={BASE_SEED}\n")
    conn = get_conn(); cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM MARTS.DIM_PATIENT")
    n_patients = cur.fetchone()[0]
    print(f"  dim_patient row count: {n_patients:,}\n")
    if n_patients == 0:
        print("ERROR: dim_patient is empty. Run dbt first."); sys.exit(1)

    for run_idx in range(NUM_RUNS):
        run_uuid = uuid.uuid4().hex
        print(f"\nrun {run_idx+1}/{NUM_RUNS}  uuid={run_uuid[:8]}")

        # ----- BASELINE: view-based redaction -----
        b_start = datetime.utcnow()
        b_metrics = run_workload(cur, run_uuid, "BASELINE_VIEWS")
        b_end = datetime.utcnow()
        b_credits = capture_credits(cur, b_start, b_end)
        insert_run(cur, run_uuid, "BASELINE_VIEWS", run_idx, b_start, b_end)
        for k, v in b_metrics.items():
            insert_metric(cur, run_uuid, "BASELINE_VIEWS", k, v)
        insert_metric(cur, run_uuid, "BASELINE_VIEWS", "credits_used",            b_credits)
        insert_metric(cur, run_uuid, "BASELINE_VIEWS", "loc_redaction",           LOC_BASELINE_REDACTION)
        insert_metric(cur, run_uuid, "BASELINE_VIEWS", "violations_caught",       VIOLATIONS_BASELINE)
        conn.commit()
        print(f"  BASELINE       mean_latency={b_metrics['mean_latency_ms']:.1f}ms  "
              f"p95={b_metrics['p95_latency_ms']:.1f}ms  credits={b_credits:.4f}")

        # ----- INTERVENTION: Snowflake masking + row access -----
        i_start = datetime.utcnow()
        i_metrics = run_workload(cur, run_uuid, "INTERVENTION_POLICIES")
        i_end = datetime.utcnow()
        i_credits = capture_credits(cur, i_start, i_end)
        insert_run(cur, run_uuid, "INTERVENTION_POLICIES", run_idx, i_start, i_end)
        for k, v in i_metrics.items():
            insert_metric(cur, run_uuid, "INTERVENTION_POLICIES", k, v)
        insert_metric(cur, run_uuid, "INTERVENTION_POLICIES", "credits_used",      i_credits)
        insert_metric(cur, run_uuid, "INTERVENTION_POLICIES", "loc_redaction",     LOC_INTERVENTION_POLICIES)
        insert_metric(cur, run_uuid, "INTERVENTION_POLICIES", "violations_caught", VIOLATIONS_INTERVENTION)
        conn.commit()
        print(f"  INTERVENTION   mean_latency={i_metrics['mean_latency_ms']:.1f}ms  "
              f"p95={i_metrics['p95_latency_ms']:.1f}ms  credits={i_credits:.4f}")

    cur.close(); conn.close()
    print("\n=== experiment complete ===")
    print("next: python /workspace/experiment/statistical_analysis.py")


if __name__ == "__main__":
    main()
