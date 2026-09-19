"""extract_clinical_dag — daily ingest of clinical data."""

from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from common import DEFAULT_ARGS


def _extract():
    import subprocess
    r = subprocess.run(
        ["python", "/workspace/data_generator/load_to_snowflake.py"],
        capture_output=True, text=True, check=False
    )
    print(r.stdout); print(r.stderr)
    if r.returncode != 0:
        raise RuntimeError("extract failed")


with DAG(
    dag_id="extract_clinical_dag",
    default_args=DEFAULT_ARGS,
    description="Daily ingest of FHIR-equivalent clinical data into Snowflake RAW",
    schedule="0 1 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["extract", "clinical"],
) as dag:
    PythonOperator(task_id="load_all", python_callable=_extract)
