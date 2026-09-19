"""governance_audit_dag — every 6 hours, refresh the governance audit mart."""

from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator
from common import DEFAULT_ARGS


with DAG(
    dag_id="governance_audit_dag",
    default_args=DEFAULT_ARGS,
    description="Every 6h: rebuild mart_governance_audit and persist results",
    schedule="0 */6 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["governance", "audit"],
) as dag:
    BashOperator(
        task_id="rebuild_audit",
        bash_command="cd /opt/airflow/dbt && dbt run --select mart_governance_audit",
    )
