"""Shared constants for the healthcare-outcomes DAGs."""

from datetime import timedelta

DBT_PROJECT_PATH  = "/opt/airflow/dbt"
DBT_PROFILES_PATH = "/opt/airflow/dbt"

DEFAULT_ARGS = {
    "owner": "msc-capstone",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=2),
}
