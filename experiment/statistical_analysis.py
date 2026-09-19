"""statistical_analysis.py — Wilcoxon, Cohen's d, bootstrapped CIs."""

import os, json
from pathlib import Path
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from scipy import stats
import snowflake.connector

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(exist_ok=True)


def get_conn():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.environ.get("SNOWFLAKE_ROLE", "DBT_ROLE"),
        warehouse="EXPT_WH_S",
        database=os.environ.get("SNOWFLAKE_DATABASE", "HEALTHCARE_DB"),
        schema="META",
    )


def fetch():
    c = get_conn(); cur = c.cursor()
    cur.execute("SELECT run_uuid, condition, metric_name, metric_value FROM META.experiment_metrics")
    cols = [d[0].lower() for d in cur.description]
    df = pd.DataFrame(cur.fetchall(), columns=cols)
    cur.close(); c.close()
    return df


def fetch_query_log():
    c = get_conn(); cur = c.cursor()
    cur.execute("SELECT * FROM META.experiment_query_log")
    cols = [d[0].lower() for d in cur.description]
    df = pd.DataFrame(cur.fetchall(), columns=cols)
    cur.close(); c.close()
    return df


def cohens_d_paired(x, y):
    diff = np.array(x) - np.array(y)
    return float(diff.mean() / (diff.std(ddof=1) + 1e-12))


def bootstrap_ci(diff, n_boot=10000, alpha=0.05, seed=42):
    rng = np.random.default_rng(seed)
    diff = np.array(diff); boots = np.empty(n_boot)
    for i in range(n_boot):
        sample = rng.choice(diff, size=len(diff), replace=True)
        boots[i] = sample.mean()
    return float(np.quantile(boots, alpha/2)), float(np.quantile(boots, 1-alpha/2))


def main():
    df = fetch()
    if df.empty:
        print("no metrics — run run_experiment.py first"); return

    print(f"  {df['run_uuid'].nunique()} runs, {df['metric_name'].nunique()} metrics\n")

    wide = df.pivot_table(index=["run_uuid", "metric_name"], columns="condition",
                          values="metric_value", aggfunc="first").reset_index()

    rows = []
    for metric in sorted(wide["metric_name"].unique()):
        sub = wide[wide["metric_name"] == metric].dropna(
            subset=["BASELINE_VIEWS", "INTERVENTION_POLICIES"])
        if len(sub) < 5: continue
        b = sub["BASELINE_VIEWS"].astype(float).values
        i = sub["INTERVENTION_POLICIES"].astype(float).values
        diff = i - b
        try:
            w_stat, w_p = stats.wilcoxon(i, b, zero_method="wilcox")
        except ValueError:
            w_stat, w_p = float("nan"), float("nan")
        d = cohens_d_paired(i, b)
        ci_low, ci_high = bootstrap_ci(diff)
        rows.append({
            "metric": metric, "n_pairs": len(sub),
            "baseline_mean":     float(b.mean()),
            "baseline_std":      float(b.std(ddof=1)),
            "intervention_mean": float(i.mean()),
            "intervention_std":  float(i.std(ddof=1)),
            "mean_diff":         float(diff.mean()),
            "diff_ci95_low":     ci_low,
            "diff_ci95_high":    ci_high,
            "wilcoxon_p_2sided": float(w_p) if not np.isnan(w_p) else None,
            "cohens_d":          d,
            "significant_at_0p05": (not np.isnan(w_p)) and (w_p < 0.05),
        })

    summary = pd.DataFrame(rows).sort_values("metric")
    summary.to_csv(OUT / "statistical_summary.csv", index=False)
    with open(OUT / "statistical_summary.json", "w") as f:
        json.dump(rows, f, indent=2, default=str)

    # Per-role-per-query analysis
    qlog = fetch_query_log()
    if not qlog.empty:
        per_role = qlog.groupby(["role_simulated", "condition"])["elapsed_ms"].agg(
            ["mean", "median", "std", "count"]).reset_index()
        per_role.to_csv(OUT / "per_role_latency.csv", index=False)
        per_query = qlog.groupby(["role_simulated", "query_template", "condition"])["elapsed_ms"].mean().reset_index()
        per_query_wide = per_query.pivot_table(
            index=["role_simulated", "query_template"], columns="condition",
            values="elapsed_ms", aggfunc="first").reset_index()
        per_query_wide["overhead_pct"] = (
            per_query_wide.get("INTERVENTION_POLICIES", 0)
            / per_query_wide.get("BASELINE_VIEWS", 1).replace(0, np.nan) - 1) * 100
        per_query_wide.to_csv(OUT / "per_query_latency.csv", index=False)

    print(f"wrote {len(summary)} metrics → {OUT}/statistical_summary.csv\n")
    pd.set_option("display.width", 220); pd.set_option("display.max_columns", None)
    print(summary[["metric", "baseline_mean", "intervention_mean",
                   "mean_diff", "wilcoxon_p_2sided", "cohens_d",
                   "significant_at_0p05"]].to_string(index=False))


if __name__ == "__main__":
    main()
