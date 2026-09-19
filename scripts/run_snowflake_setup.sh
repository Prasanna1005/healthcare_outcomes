#!/usr/bin/env bash
# run_snowflake_setup.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if [ -f .env ]; then set -a; source .env; set +a; else echo "ERROR: .env not found"; exit 1; fi

ACCOUNT="${SNOWFLAKE_ACCOUNT:?}"
USER="${SNOWFLAKE_ACCOUNTADMIN_USER:-${SNOWFLAKE_USER}}"
PASSWORD="${SNOWFLAKE_ACCOUNTADMIN_PASSWORD:-${SNOWFLAKE_PASSWORD}}"

echo "running Snowflake setup against $ACCOUNT as $USER"

for f in snowflake/00_setup_warehouses.sql \
         snowflake/01_setup_database.sql \
         snowflake/02_setup_roles_grants.sql \
         snowflake/03_setup_resource_monitors.sql \
         snowflake/04_setup_raw_tables.sql \
         snowflake/05_setup_governance_policies.sql \
         snowflake/06_setup_baseline_views.sql \
         snowflake/07_setup_meta_tables.sql ; do
    echo
    echo "  → $f"
    SNOWSQL_PWD="$PASSWORD" snowsql \
        --accountname "$ACCOUNT" --username "$USER" \
        --filename  "$f" --option exit_on_error=true --option output_format=plain
done

echo
echo "✓ Snowflake setup complete"
