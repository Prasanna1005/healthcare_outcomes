"""generate_charts.py — 5 publication-quality charts."""

import os
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv
import snowflake.connector

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
OUT = Path(__file__).resolve().parent / "results" / "charts"
OUT.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid", context="paper", font_scale=1.05)
plt.rcParams.update({"figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight"})

BASELINE_COLOR     = "#7B8FA1"
INTERVENTION_COLOR = "#2E75B6"
KEY = ["mean_latency_ms", "p95_latency_ms", "credits_used", "loc_redaction"]


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
    cur.execute("""
        SELECT m.run_uuid, m.condition, m.metric_name, m.metric_value, r.run_index
          FROM META.experiment_metrics m
          JOIN META.experiment_runs    r USING (run_uuid, condition)
    """)
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


def plot_box(df):
    fig, ax = plt.subplots(figsize=(10, 5))
    sub = df[df["metric_name"].isin(KEY)].copy()
    sub["metric_name"] = pd.Categorical(sub["metric_name"], categories=KEY)
    sns.boxplot(data=sub, x="metric_name", y="metric_value", hue="condition",
                palette={"BASELINE_VIEWS": BASELINE_COLOR,
                         "INTERVENTION_POLICIES": INTERVENTION_COLOR}, ax=ax)
    ax.set_yscale("symlog")
    ax.set_title("Governance overhead: 20 paired runs", fontweight="bold")
    ax.set_xlabel(""); ax.set_ylabel("Value (symlog scale)")
    plt.xticks(rotation=20, ha="right")
    fig.savefig(OUT / "box_plot_metrics.png"); plt.close(fig)


def plot_latency_by_role(qlog):
    fig, ax = plt.subplots(figsize=(10, 5))
    sub = qlog.copy()
    sub["role_simulated"] = sub["role_simulated"].str.replace("_ROLE", "")
    sns.boxplot(data=sub, x="role_simulated", y="elapsed_ms", hue="condition",
                palette={"BASELINE_VIEWS": BASELINE_COLOR,
                         "INTERVENTION_POLICIES": INTERVENTION_COLOR}, ax=ax)
    ax.set_title("Query latency by simulated role", fontweight="bold")
    ax.set_xlabel("Simulated role"); ax.set_ylabel("Latency (ms)")
    fig.savefig(OUT / "latency_by_role.png"); plt.close(fig)


def plot_paired_p95(df):
    fig, ax = plt.subplots(figsize=(8, 5))
    sub = df[df["metric_name"] == "p95_latency_ms"].pivot_table(
        index="run_uuid", columns="condition", values="metric_value",
        aggfunc="first").dropna()
    for _, row in sub.iterrows():
        ax.plot([0, 1], [row["BASELINE_VIEWS"], row["INTERVENTION_POLICIES"]],
                color="gray", alpha=0.4, marker="o")
    ax.scatter([0]*len(sub), sub["BASELINE_VIEWS"],         color=BASELINE_COLOR,     s=60, zorder=3, label="View-based")
    ax.scatter([1]*len(sub), sub["INTERVENTION_POLICIES"],  color=INTERVENTION_COLOR, s=60, zorder=3, label="Policies")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Baseline (Views)", "Intervention (Policies)"])
    ax.set_ylabel("p95 latency (ms)")
    ax.set_title("Paired p95-latency differences across 20 runs", fontweight="bold")
    ax.legend(loc="best")
    fig.savefig(OUT / "paired_p95_latency.png"); plt.close(fig)


def plot_overhead_per_query(qlog):
    means = qlog.groupby(["role_simulated", "query_template", "condition"])["elapsed_ms"].mean().unstack()
    if "BASELINE_VIEWS" not in means.columns or "INTERVENTION_POLICIES" not in means.columns:
        return
    means["overhead_pct"] = (means["INTERVENTION_POLICIES"]
                             / means["BASELINE_VIEWS"].replace(0, np.nan) - 1) * 100
    means = means.reset_index()
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=means, x="query_template", y="overhead_pct",
                hue="role_simulated", ax=ax)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("Per-query latency overhead: Intervention vs Baseline", fontweight="bold")
    ax.set_xlabel(""); ax.set_ylabel("Overhead (%)")
    plt.xticks(rotation=30, ha="right")
    ax.legend(title="Role", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    fig.savefig(OUT / "overhead_per_query.png"); plt.close(fig)


def plot_summary_radar(df):
    metrics = ["mean_latency_ms", "p95_latency_ms", "credits_used", "loc_redaction"]
    means = df.groupby(["condition", "metric_name"])["metric_value"].mean().unstack(fill_value=0)
    # Normalise within each metric so they all fit on the same radar
    for m in metrics:
        if m in means.columns:
            mx = means[m].max()
            if mx > 0:
                means[m] = means[m] / mx
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]
    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw={"projection": "polar"})
    for cond, color in [("BASELINE_VIEWS", BASELINE_COLOR),
                        ("INTERVENTION_POLICIES", INTERVENTION_COLOR)]:
        if cond not in means.index: continue
        values = [means.loc[cond, m] if m in means.columns else 0 for m in metrics]
        values += values[:1]
        ax.plot(angles, values, color=color, linewidth=2,
                label=cond.replace("_", " ").title())
        ax.fill(angles, values, color=color, alpha=0.18)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([m.upper() for m in metrics])
    ax.set_ylim(0, 1.1)
    ax.set_title("Governance comparison — normalised radar", fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.30, 1.10))
    fig.savefig(OUT / "summary_radar.png"); plt.close(fig)


def main():
    df = fetch()
    qlog = fetch_query_log()
    if df.empty:
        print("no metrics — run run_experiment.py first"); return
    print(f"{df['run_uuid'].nunique()} runs, {df['metric_name'].nunique()} metrics, "
          f"{len(qlog):,} per-query rows")
    plot_box(df);                  print("  ✓ box_plot_metrics.png")
    if not qlog.empty:
        plot_latency_by_role(qlog); print("  ✓ latency_by_role.png")
        plot_overhead_per_query(qlog); print("  ✓ overhead_per_query.png")
    plot_paired_p95(df);           print("  ✓ paired_p95_latency.png")
    plot_summary_radar(df);        print("  ✓ summary_radar.png")
    print(f"\nall charts → {OUT}")


if __name__ == "__main__":
    main()
