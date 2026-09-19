"""dbt_test_dag — daily test suite including governance singular tests."""

from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator
from common import DEFAULT_ARGS


with DAG(
    dag_id="dbt_test_dag",
    default_args=DEFAULT_ARGS,
    schedule="30 3 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["dbt", "tests", "governance"],
) as dag:
    BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/dbt && dbt deps && dbt test",
    )
