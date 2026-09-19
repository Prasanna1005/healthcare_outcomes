# Healthcare Outcomes & PHI Governance Pipeline

**MSc Computer Science Capstone — Project 3**
**Stack:** Snowflake · dbt Core (with contracts) · Apache Airflow · Docker

## What This Is

An end-to-end analytics platform for a hospital network. Ingests synthetic FHIR-style patient records (Synthea-equivalent), encounters, conditions, observations, medications, and procedures into Snowflake. dbt transforms them through a medallion architecture into clinical analytics marts (readmission risk, length-of-stay analytics, condition prevalence) and governance marts (audit logs, query attribution).

The empirical research angle compares **column-level Snowflake Dynamic Data Masking + Row Access Policies + dbt contracts** (INTERVENTION) against **view-based PHI redaction** (BASELINE), measuring query latency overhead, governance-policy violations caught, developer-friction (LOC + test failures), and Snowflake credit cost across 20 paired runs.

## Quick Start

```bash
cp .env.example .env                              # edit Snowflake creds
docker compose up -d --build
bash scripts/run_snowflake_setup.sh               # 7 SQL scripts
docker compose exec dbt-runner python /workspace/data_generator/generate_all.py
docker compose exec dbt-runner python /workspace/data_generator/load_to_snowflake.py
docker compose exec dbt-runner bash -c "cd /workspace/dbt && dbt deps && dbt seed && dbt run && dbt test"
docker compose exec dbt-runner python /workspace/experiment/run_experiment.py
docker compose exec dbt-runner python /workspace/experiment/statistical_analysis.py
docker compose exec dbt-runner python /workspace/experiment/generate_charts.py
```

## Repository Layout

```
healthcare_outcomes/
├── README.md, .env.example, docker-compose.yml, Dockerfile.dbt, requirements.txt
├── snowflake/         (7 DDL scripts: warehouses, db, roles, monitors, raw, governance policies, meta)
├── data_generator/    Synthetic FHIR-style patient + encounter + observation generator
├── dbt/               medallion: staging → intermediate → marts/clinical + marts/governance
│   └── tests/singular/ Governance assertions (no PHI in marts, masking applied, etc.)
├── airflow/dags/      6 DAGs
├── experiment/        Governance-overhead comparison
├── notebook/          interactive analysis
├── scripts/           Snowflake setup helper
└── docs/              (rendered docs in the bundle's other DOCX files)
```

## Key Stats

| Metric | Value |
|---|---|
| Synthetic patients | 100,000 |
| Synthetic encounters | ~800,000 |
| Synthetic observations (vitals/labs) | ~5,000,000 |
| Synthetic conditions | ~400,000 |
| Synthetic medications | ~600,000 |
| dbt models | ~22 |
| Snowflake credits per full run | ~3-4 |

## Synthetic Data — HIPAA Safety

All data is generated synthetically. No real patient identifiers are used. Patient-level fields (name, MRN, date of birth, address) are Faker-generated and have no correspondence with any real person. The project is HIPAA-safe by construction.
