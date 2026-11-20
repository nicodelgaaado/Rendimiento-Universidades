"""Independent audit of saved artifacts. Does not import/run the builder."""
import csv
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
database = HERE / 'rendimiento.sqlite3'
before = hashlib.sha256(database.read_bytes()).hexdigest()
db = sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)
report = {'tables': {}, 'checks': [], 'postgresql_server_tested': False}

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def rows_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def canonical(value, kind):
    if value is None or value == '':
        return None
    if kind == 'INTEGER' or kind.startswith('NUMERIC'):
        return Decimal(str(value))
    return value

tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
require(len(tables) == 10, 'Expected 10 tables')
manifest = json.loads((HERE / 'validation.json').read_text())
for table in tables:
    info = db.execute(f'PRAGMA table_info("{table}")').fetchall()
    columns = [r[1] for r in info]
    types = [r[2] for r in info]
    path = ROOT / 'powerbi/data' / f'{table}.csv'
    source = rows_csv(path)
    require(list(source[0]) == columns, f'Column mismatch: {table}')
    expected = Counter(tuple(canonical(r[c], t) for c, t in zip(columns, types)) for r in source)
    actual = Counter(tuple(canonical(v, t) for v, t in zip(r, types)) for r in db.execute(f'SELECT * FROM "{table}"'))
    require(expected == actual, f'Data mismatch: {table}')
    require(hashlib.sha256(path.read_bytes()).hexdigest() == manifest['tables'][table]['sha256'], f'Stale CSV hash: {table}')
    report['tables'][table] = len(source)
require(db.execute('PRAGMA integrity_check').fetchall() == [('ok',)], 'Integrity failure')
require(not db.execute('PRAGMA foreign_key_check').fetchall(), 'Orphan records')
report['checks'].append('All saved table values, duplicate multiplicities, column order and CSV hashes match; integrity and foreign keys pass')

eda = rows_csv(ROOT / 'powerbi/data/EDA_TemaSemestreRendimiento.csv')
expected = Counter((r['Tema'], r['CodigoSemestre'], r['CategoriaRendimiento'], int(r['Observaciones'])) for r in eda)
require(expected == Counter(db.execute('SELECT * FROM "EDA_TemaSemestreRendimiento"')), 'EDA mismatch')
require(db.execute('SELECT COUNT(*) FROM "HechosNotasOficiales" WHERE "PromedioNotaPublicado"=0 AND "PromedioNotaParaAnalisis" IS NULL').fetchone()[0] == 63, 'Zero grade handling')
report['checks'].append('EDA view matches CSV; 63 published zeros retain NULL analysis grades')

totals = db.execute('SELECT "PeriodoAcademico",SUM("Inscritos"),SUM("Aprobados"),SUM("Reprobados") FROM "HechosNotasOficiales" GROUP BY "PeriodoAcademico" ORDER BY 1').fetchall()
require(totals == [('2015-2',49607,41499,8108),('2017-1',49006,41524,7482)], 'Grade totals mismatch')
dropout = db.execute('SELECT "CohorteIngreso",SUM("MatriculadosIniciales"),SUM("DesertoresNetos") FROM "HechosDesercionOficial" GROUP BY "CohorteIngreso" ORDER BY 1').fetchall()
require(dropout == [('2005-2',1295,653),('2006-1',1404,586)], 'Dropout totals mismatch')
report['grade_totals'] = totals
report['dropout_totals'] = dropout

# Exercise the actual persisted constraints on an isolated in-memory copy.
copy = sqlite3.connect(':memory:')
db.backup(copy)
copy.execute('PRAGMA foreign_keys=ON')
invalid = {
    'duplicate primary key': 'INSERT INTO "DimensionTemas" SELECT * FROM "DimensionTemas" LIMIT 1',
    'orphan subject': 'UPDATE "HechosObservaciones" SET "IdTema"=999999 WHERE "IdObservacion"=1',
    'invalid performance category': 'UPDATE "HechosObservaciones" SET "CategoriaRendimiento"=\'X\' WHERE "IdObservacion"=1',
    'negative activity': 'UPDATE "HechosObservaciones" SET "VecesManoLevantada"=-1 WHERE "IdObservacion"=1',
    'grade outside scale': 'UPDATE "HechosNotasOficiales" SET "PromedioNotaPublicado"=6',
    'inconsistent grade counts': 'UPDATE "HechosNotasOficiales" SET "Inscritos"="Inscritos"+1',
    'zero incorrectly used in analysis': 'UPDATE "HechosNotasOficiales" SET "PromedioNotaParaAnalisis"=0 WHERE "PromedioNotaPublicado"=0',
    'inconsistent dropout counts': 'UPDATE "HechosDesercionOficial" SET "DesertoresNetos"="DesertoresNetos"+1',
    'mismatched follow-up period': 'UPDATE "HechosDesercionOficial" SET "PeriodoSeguimiento"=\'2099-1\'',
    'delete referenced dimension': 'DELETE FROM "DimensionTemas"',
    'missing required value': 'UPDATE "HechosObservaciones" SET "Genero"=NULL WHERE "IdObservacion"=1',
}
for label, sql in invalid.items():
    copy.execute('SAVEPOINT probe')
    try:
        copy.execute(sql)
    except sqlite3.IntegrityError:
        pass
    else:
        raise RuntimeError(f'Invalid mutation accepted: {label}')
    finally:
        copy.execute('ROLLBACK TO probe')
        copy.execute('RELEASE probe')
report['rejected_invalid_mutations'] = list(invalid)

# Execute the actual export's shared SQL, removing only PG session/schema setup.
# This confirms export completeness, but is explicitly NOT a PostgreSQL test.
sql = (HERE / 'postgresql.sql').read_text(encoding='utf-8')
shared = '\n'.join(line for line in sql.splitlines() if not line.startswith(('SET LOCAL ', 'CREATE SCHEMA ')))
replay = sqlite3.connect(':memory:')
replay.execute('PRAGMA foreign_keys=ON')
replay.executescript(shared)
for table in tables + ['EDA_TemaSemestreRendimiento']:
    require(Counter(db.execute(f'SELECT * FROM "{table}"')) == Counter(replay.execute(f'SELECT * FROM "{table}"')), f'Export mismatch: {table}')
report['checks'].append('Actual SQL export replayed with PostgreSQL setup removed: all table and view rows match saved database')
for row in db.execute('SELECT "ArchivoFuente","HuellaSHA256" FROM "DimensionFuentesOficiales"'):
    path = ROOT / 'dataset/fuentes_oficiales' / row[0]
    require(hashlib.sha256(path.read_bytes()).hexdigest() == row[1], f'PDF hash mismatch: {row[0]}')
report['checks'].append('All 3 local source PDFs match stored provenance hashes')
if '--postgres' in sys.argv:
    command = [
        os.environ.get('FACT_CHECK_PSQL', 'C:/Program Files/PostgreSQL/18/bin/psql.exe'),
        '-X',
        '-h', os.environ.get('FACT_CHECK_PGHOST', '127.0.0.1'),
        '-p', os.environ.get('FACT_CHECK_PGPORT', '55439'),
        '-U', os.environ.get('FACT_CHECK_PGUSER', 'audit'),
        '-d', os.environ.get('FACT_CHECK_PGDATABASE', 'postgres'),
        '--set=ON_ERROR_STOP=on', '-t', '-A'
    ]
    for table in tables + ['EDA_TemaSemestreRendimiento']:
        result = subprocess.run(command + ['-c', f'SELECT row_to_json(t) FROM rendimiento."{table}" t'], check=True, capture_output=True)
        records = [json.loads(line, parse_float=Decimal) for line in result.stdout.decode('utf-8').splitlines() if line.strip()]
        cursor = db.execute(f'SELECT * FROM "{table}"')
        columns = [r[0] for r in cursor.description]
        expected = Counter(tuple(Decimal(str(v)) if isinstance(v, (int, float)) else v for v in row) for row in cursor)
        actual = Counter(tuple(record[c] for c in columns) for record in records)
        require(expected == actual, f'PostgreSQL data mismatch: {table}')
    for label, mutation in invalid.items():
        result = subprocess.run(command + ['-c', 'BEGIN; SET LOCAL search_path TO rendimiento; ' + mutation + '; ROLLBACK;'], capture_output=True)
        require(result.returncode != 0 and b'ERROR:' in result.stderr, f'PostgreSQL accepted invalid mutation: {label}')
    report['postgresql_server_tested'] = True
    report['checks'].append('PostgreSQL 18: original SQL import succeeded; every field in all tables/view matches; all 11 invalid mutations rejected')
db.close()
copy.close()
replay.close()
require(hashlib.sha256(database.read_bytes()).hexdigest() == before, 'Original database changed')
report['database_sha256'] = before
report['result'] = 'PASS (SQLite and PostgreSQL 18)' if report['postgresql_server_tested'] else 'PASS (local data and shared SQL); PostgreSQL server execution pending'
(HERE / 'fact_check_results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
