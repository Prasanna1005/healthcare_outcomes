"""experiment_dag — 20-paired-run governance overhead comparison."""

from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator
from common import DEFAULT_ARGS


with DAG(
    dag_id="experiment_dag",
    default_args=DEFAULT_ARGS,
    description="20-run paired comparison: view-based redaction (BASELINE) vs masking policies (INTERVENTION)",
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["experiment", "dissertation"],
) as dag:
    run    = BashOperator(task_id="run_experiment",       bash_command="python /workspace/experiment/run_experiment.py")
    stats  = BashOperator(task_id="statistical_analysis", bash_command="python /workspace/experiment/statistical_analysis.py")
    charts = BashOperator(task_id="generate_charts",      bash_command="python /workspace/experiment/generate_charts.py")
    run >> stats >> charts
