# Database package

This directory contains portable, reproducible database versions of the project
data. It supports local exploration with SQLite and cloud deployment to
PostgreSQL or Azure SQL Database.

## Included artifacts

| File | Purpose |
| --- | --- |
| `rendimiento.sqlite3` | Populated SQLite database for DB Browser for SQLite. |
| `postgresql.sql` | Transactional PostgreSQL schema and data import. |
| `azure_sql.sql` | Transactional Azure SQL schema and data import. |
| `build_database.py` | Rebuilds SQLite and PostgreSQL artifacts from `powerbi/data`. |
| `build_azure_sql.py` | Rebuilds the Azure SQL import from `powerbi/data`. |
| `fact_check.py` | Audits SQLite/PostgreSQL data, relationships and constraints. |
| `verify_azure_sql.py` | Compares an Azure SQL export field by field with the CSV files. |
| `invoke_azure_sql.ps1` | Executes a T-SQL file with a short-lived Microsoft Entra token. |
| `export_azure_sql.ps1` | Exports Azure SQL data for independent verification. |
| `azure_sql_constraint_probes.sql` | Tests eleven invalid mutations inside rolled-back transactions. |
| `consultas_azure_sql.md` | Ready-to-use analysis queries with explanations. |

Generated SQL files and the SQLite database contain only the public educational
data already present in this repository. No passwords, access tokens, tenant
identifiers, subscription identifiers, client IP addresses or private keys are
stored here.

## Rebuild locally

From the repository root:

```powershell
python database/build_database.py
python database/build_azure_sql.py
```

Both builders use Python's standard library. `build_database.py` validates every
field while loading SQLite, verifies foreign keys and integrity, reproduces the
EDA view, and checks the published grade and dropout totals.

Open `database/rendimiento.sqlite3` in DB Browser for SQLite and choose
**Browse Data**, or run:

```sql
SELECT * FROM HechosNotasOficiales LIMIT 100;
```

## PostgreSQL import

Import into a new database or schema:

```powershell
psql -X --set=ON_ERROR_STOP=on --file=database/postgresql.sql
psql -X --set=ON_ERROR_STOP=on --file=database/verify.sql
```

The import creates schema `rendimiento` and does not contain `DROP` or `DELETE`
statements. Use environment variables or a secret manager for credentials.

## Azure SQL deployment and verification

Provision an Azure SQL Database with Microsoft Entra authentication and a
firewall rule restricted to the deployment client. Then run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File database/invoke_azure_sql.ps1 `
  -Server '<server>.database.windows.net' `
  -Database '<database>' `
  -SqlFile database/azure_sql.sql
```

Export and verify the remote data:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File database/export_azure_sql.ps1 `
  -Server '<server>.database.windows.net' `
  -Database '<database>' `
  -OutputFile database/azure_sql_export.json

python database/verify_azure_sql.py
```

The scripts request short-lived tokens from Azure CLI and never persist them.
The export file, certificates, logs and temporary PostgreSQL clusters are
ignored. Use `azure_sql_diagnostic_*.json` as Azure Monitor diagnostic-settings
payloads. Run `azure_sql_constraint_probes.sql` with `invoke_azure_sql.ps1` to
confirm that keys, required values, ranges and cross-table relationships reject
invalid data.

## Data model

The package contains seven dimension tables, three fact tables and one EDA view:

- `HechosObservaciones`: 480 xAPI observations.
- `HechosNotasOficiales`: 1,977 official subject-period records.
- `HechosDesercionOficial`: 10 faculty-cohort records.
- `EDA_TemaSemestreRendimiento`: aggregate view over xAPI observations.

The xAPI and official UNAL populations remain separate because they describe
different populations and levels of detail. Observation IDs identify source
rows, not students. The 63 zero grades remain preserved in the published field
and are `NULL` in the analysis field.
