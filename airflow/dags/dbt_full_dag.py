"""dbt_full_dag — Cosmos-rendered dbt build."""

from datetime import datetime
import os
from cosmos import DbtDag, ProjectConfig, ProfileConfig, ExecutionConfig
from cosmos.profiles import SnowflakeUserPasswordProfileMapping

profile_config = ProfileConfig(
    profile_name="healthcare_outcomes",
    target_name="dev",
    profile_mapping=SnowflakeUserPasswordProfileMapping(
        conn_id="snowflake_default",
        profile_args={
            "account":   os.environ["SNOWFLAKE_ACCOUNT"],
            "user":      os.environ["SNOWFLAKE_USER"],
            "password":  os.environ["SNOWFLAKE_PASSWORD"],
            "role":      os.environ.get("SNOWFLAKE_ROLE", "DBT_ROLE"),
            "warehouse": os.environ.get("SNOWFLAKE_WAREHOUSE", "DBT_WH_XS"),
            "database":  os.environ.get("SNOWFLAKE_DATABASE", "HEALTHCARE_DB"),
            "schema":    "DBT",
        },
    ),
)

dbt_full_dag = DbtDag(
    dag_id="dbt_full_dag",
    schedule="0 3 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    project_config=ProjectConfig("/opt/airflow/dbt"),
    profile_config=profile_config,
    execution_config=ExecutionConfig(dbt_executable_path="/home/airflow/.local/bin/dbt"),
    operator_args={"install_deps": True, "full_refresh": False},
    default_args={"retries": 1},
    tags=["dbt", "transform"],
)
