"""load_to_snowflake.py — Bulk-load CSVs into RAW.* tables."""

import os
import time
from pathlib import Path

from dotenv import load_dotenv
import snowflake.connector


# Load .env
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# synthetic_data directory
DATA_DIR = Path(__file__).resolve().parent.parent / "synthetic_data"


CSV_FILES = [
    ("raw_patients.csv", "RAW.RAW_PATIENTS"),
    ("raw_encounters.csv", "RAW.RAW_ENCOUNTERS"),
    ("raw_observations.csv", "RAW.RAW_OBSERVATIONS"),
    ("raw_conditions.csv", "RAW.RAW_CONDITIONS"),
    ("raw_medications.csv", "RAW.RAW_MEDICATIONS"),
    ("raw_procedures.csv", "RAW.RAW_PROCEDURES"),
]


def conn():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.environ["SNOWFLAKE_ROLE"],
        warehouse="LOAD_WH_XS",
        database=os.environ["SNOWFLAKE_DATABASE"],
        schema="RAW",
    )


def get_load_columns(cur, target):
    """
    Get all target table columns except _LOADED_AT.
    These are the columns coming from the CSV file.
    """

    cur.execute(f"DESC TABLE {target}")

    rows = cur.fetchall()

    columns = []

    for row in rows:
        column_name = row[0]

        if column_name.upper() != "_LOADED_AT":
            columns.append(column_name)

    return columns


def main():
    c = conn()
    cur = c.cursor()

    print(f"connected to {os.environ['SNOWFLAKE_ACCOUNT']}")

    # Create stage
    cur.execute("CREATE STAGE IF NOT EXISTS RAW.LOAD_STAGE")

    # Create CSV file format
    cur.execute("""
        CREATE OR REPLACE FILE FORMAT RAW.CSV_FORMAT
            TYPE = 'CSV'
            FIELD_DELIMITER = ','
            SKIP_HEADER = 1
            FIELD_OPTIONALLY_ENCLOSED_BY = '"'
            NULL_IF = ('NULL', 'null', '')
            EMPTY_FIELD_AS_NULL = TRUE
            DATE_FORMAT = 'YYYY-MM-DD'
            TIMESTAMP_FORMAT = 'AUTO'
            ESCAPE_UNENCLOSED_FIELD = NONE
    """)

    for fname, target in CSV_FILES:

        path = DATA_DIR / fname

        if not path.exists():
            print(f"  skip {fname} - file not found")
            continue

        t0 = time.time()

        print(f"  loading {fname} -> {target}")

        # Get target columns excluding _LOADED_AT
        columns = get_load_columns(cur, target)

        print(f"  table columns used for CSV: {len(columns)}")

        # Empty target table
        cur.execute(f"TRUNCATE TABLE {target}")

        # Convert Windows path to file:// URI
        file_uri = path.resolve().as_uri()

        # Upload CSV to Snowflake stage
        cur.execute(
            f"PUT '{file_uri}' "
            f"@RAW.LOAD_STAGE "
            f"OVERWRITE=TRUE "
            f"AUTO_COMPRESS=TRUE"
        )

        # Build column list
        column_list = ", ".join(
            f'"{column}"' for column in columns
        )

        # Load CSV into the 22 actual CSV columns.
        # _LOADED_AT is omitted so its CURRENT_TIMESTAMP default is used.
        cur.execute(f"""
            COPY INTO {target} ({column_list})
            FROM @RAW.LOAD_STAGE
            FILE_FORMAT = (
                FORMAT_NAME = 'RAW.CSV_FORMAT'
            )
            PATTERN = '.*{fname}.*'
            ON_ERROR = 'ABORT_STATEMENT'
        """)

        # Verify row count
        cur.execute(f"SELECT COUNT(*) FROM {target}")

        rows = cur.fetchone()[0]

        print(
            f"  ✓ {fname:<28} "
            f"rows={rows:>10,}  "
            f"({time.time() - t0:.1f}s)"
        )

    cur.close()
    c.close()

    print("\nload complete.")
    print("Next: cd dbt && dbt deps && dbt seed && dbt run && dbt test")


if __name__ == "__main__":
    main()