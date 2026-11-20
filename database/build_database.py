"""Build a local SQLite database and a portable PostgreSQL SQL import.

Uses only Python's standard library. Run from any directory.
Existing project CSVs are the source of truth; no source files are modified.
"""
from pathlib import Path
import csv
from decimal import Decimal
import hashlib
import json
import sqlite3

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
DATA = ROOT / 'powerbi' / 'data'

# Explicit types: identifiers such as course codes must remain text.
INTEGERS = set('IdTema IdSemestre IdObservacion AnioAcademico Semestre '
    'VecesManoLevantada RecursosVisitados AnunciosVistos ParticipacionesDiscusion '
    'Inscritos Aprobados Reprobados Repitentes PaginaArchivoFuente TablaFuente '
    'MatriculadosIniciales MatriculadosSeguimiento ReservasCupo Graduados '
    'GraduadosMatriculados DesertoresNetos TransferenciasSalida TransferenciasEntrada '
    'PaginaImpresaFuente'.split())
DECIMALS = set('PromedioNotaPublicado PromedioNotaParaAnalisis DesviacionNotaPublicada '
    'PorcentajeReprobacionPublicado PorcentajeRepitenciaPublicado '
    'PorcentajeDesercionPublicado'.split())
TABLES = {
    'DimensionTemas': ['IdTema'],
    'DimensionSemestres': ['IdSemestre'],
    'DimensionAsignaturasOficiales': ['CodigoAsignatura'],
    'DimensionPeriodosNotas': ['PeriodoAcademico'],
    'DimensionFacultadesOficiales': ['CodigoFacultad'],
    'DimensionCohortesDesercion': ['CohorteIngreso'],
    'DimensionFuentesOficiales': ['IdentificadorFuente'],
    'HechosObservaciones': ['IdObservacion'],
    'HechosNotasOficiales': ['CodigoAsignatura', 'PeriodoAcademico'],
    'HechosDesercionOficial': ['CodigoFacultad', 'CohorteIngreso'],
}
RELATIONS = {
    'HechosObservaciones': [('IdTema', 'DimensionTemas', 'IdTema'),
                            ('IdSemestre', 'DimensionSemestres', 'IdSemestre')],
    'HechosNotasOficiales': [('CodigoAsignatura', 'DimensionAsignaturasOficiales', 'CodigoAsignatura'),
                            ('PeriodoAcademico', 'DimensionPeriodosNotas', 'PeriodoAcademico'),
                            ('IdentificadorFuente', 'DimensionFuentesOficiales', 'IdentificadorFuente')],
    'HechosDesercionOficial': [('CodigoFacultad', 'DimensionFacultadesOficiales', 'CodigoFacultad'),
                              ('CohorteIngreso', 'DimensionCohortesDesercion', 'CohorteIngreso'),
                              ('IdentificadorFuente', 'DimensionFuentesOficiales', 'IdentificadorFuente')],
}
CHECKS = {
    'DimensionSemestres': ['"IdSemestre" IN (1,2)', '"CodigoSemestre" IN (\'F\',\'S\')'],
    'DimensionPeriodosNotas': ['"Semestre" IN (1,2)'],
    'HechosObservaciones': ['"CategoriaRendimiento" IN (\'L\',\'M\',\'H\')'] +
        [f'"{c}" BETWEEN 0 AND 100' for c in ['VecesManoLevantada', 'RecursosVisitados', 'AnunciosVistos', 'ParticipacionesDiscusion']],
    'HechosNotasOficiales': ['"Inscritos" > 0', '"Inscritos" = "Aprobados" + "Reprobados"',
        '"PromedioNotaPublicado" BETWEEN 0 AND 5', '"DesviacionNotaPublicada" >= 0',
        '("PromedioNotaPublicado" = 0 AND "PromedioNotaParaAnalisis" IS NULL) OR '
        '("PromedioNotaPublicado" > 0 AND "PromedioNotaParaAnalisis" IS NOT NULL AND "PromedioNotaParaAnalisis" = "PromedioNotaPublicado")'],
    'HechosDesercionOficial': ['"MatriculadosIniciales" > 0',
        '"DesertoresNetos" = "MatriculadosIniciales" - "MatriculadosSeguimiento" - "ReservasCupo" - ("Graduados" - "GraduadosMatriculados")'],
}

def quote(name):
    return '"' + name.replace('"', '""') + '"'

def literal(value):
    if value is None:
        return 'NULL'
    if isinstance(value, (int, Decimal)):
        return str(value)
    return "'" + value.replace("'", "''") + "'"

def read_table(name):
    with (DATA / f'{name}.csv').open(encoding='utf-8-sig', newline='') as source:
        reader = csv.DictReader(source)
        columns = reader.fieldnames
        rows = []
        for row in reader:
            values = []
            for column in columns:
                value = row[column]
                if value == '' and column == 'PromedioNotaParaAnalisis':
                    value = None
                elif value is None or value == '':
                    raise ValueError(f'Missing value: {name}.{column}')
                elif column in INTEGERS:
                    value = int(value)
                elif column in DECIMALS:
                    value = Decimal(value)
                    if not value.is_finite():
                        raise ValueError(f'Non-finite decimal: {name}.{column}')
                values.append(value)
            rows.append(values)
    return columns, rows

def table_sql(name, columns):
    parts = []
    column_checks = []
    for column in columns:
        kind = 'INTEGER' if column in INTEGERS else 'NUMERIC(12,6)' if column in DECIMALS else 'TEXT'
        nullable = '' if column == 'PromedioNotaParaAnalisis' else ' NOT NULL'
        parts.append(f'{quote(column)} {kind}{nullable}')
        if column in INTEGERS:
            column_checks.append(f'CHECK ({quote(column)} >= 0)')
        if column.startswith('Porcentaje'):
            column_checks.append(f'CHECK ({quote(column)} BETWEEN 0 AND 100)')
    parts.extend(column_checks)
    parts.append('PRIMARY KEY (' + ', '.join(map(quote, TABLES[name])) + ')')
    for column, target, key in RELATIONS.get(name, []):
        parts.append(f'FOREIGN KEY ({quote(column)}) REFERENCES {quote(target)} ({quote(key)})')
    if name == 'DimensionCohortesDesercion':
        parts.append('UNIQUE ("CohorteIngreso", "PeriodoSeguimiento")')
    if name == 'DimensionSemestres':
        parts.append('UNIQUE ("CodigoSemestre")')
    if name == 'HechosDesercionOficial':
        parts.append('FOREIGN KEY ("CohorteIngreso", "PeriodoSeguimiento") REFERENCES "DimensionCohortesDesercion" ("CohorteIngreso", "PeriodoSeguimiento")')
    parts.extend(f'CHECK ({check})' for check in CHECKS.get(name, []))
    return f'CREATE TABLE {quote(name)} (\n  ' + ',\n  '.join(parts) + '\n);'

VIEW = '''CREATE VIEW "EDA_TemaSemestreRendimiento" AS
SELECT t."Tema", s."CodigoSemestre", h."CategoriaRendimiento", COUNT(*) AS "Observaciones"
FROM "HechosObservaciones" h
JOIN "DimensionTemas" t ON t."IdTema" = h."IdTema"
JOIN "DimensionSemestres" s ON s."IdSemestre" = h."IdSemestre"
GROUP BY t."Tema", s."CodigoSemestre", h."CategoriaRendimiento";'''

def main():
    schema, inserts, manifest = [], [], {}
    conn = sqlite3.connect(':memory:')
    conn.execute('PRAGMA foreign_keys = ON')
    for name in TABLES:
        columns, rows = read_table(name)
        ddl = table_sql(name, columns)
        schema.append(ddl)
        conn.execute(ddl)
        prefix = f'INSERT INTO {quote(name)} (' + ', '.join(map(quote, columns)) + ') VALUES '
        for row in rows:
            sql = prefix + '(' + ', '.join(map(literal, row)) + ');'
            conn.execute(sql)
            inserts.append(sql)
        actual = conn.execute(f'SELECT * FROM {quote(name)}').fetchall()
        # Verify every field after loading, including nulls, accents and text codes.
        for expected, loaded in zip(rows, actual, strict=True):
            for a, b in zip(expected, loaded, strict=True):
                assert (abs(a - Decimal(str(b))) < Decimal('0.0000001')) if isinstance(a, Decimal) else a == b
        manifest[name] = {'rows': len(rows), 'sha256': hashlib.sha256((DATA / f'{name}.csv').read_bytes()).hexdigest()}
    for name, relations in RELATIONS.items():
        for column, _, _ in relations:
            ddl = f'CREATE INDEX {quote("ix_" + name + "_" + column)} ON {quote(name)} ({quote(column)});'
            schema.append(ddl)
            conn.execute(ddl)
    schema.append(VIEW)
    conn.execute(VIEW)
    with (DATA / 'EDA_TemaSemestreRendimiento.csv').open(encoding='utf-8-sig', newline='') as f:
        expected_eda = sorted((r['Tema'], r['CodigoSemestre'], r['CategoriaRendimiento'], int(r['Observaciones'])) for r in csv.DictReader(f))
    assert sorted(conn.execute('SELECT * FROM "EDA_TemaSemestreRendimiento"')) == expected_eda
    checks = json.loads((DATA / 'VerificacionFuentesOficiales.json').read_text(encoding='utf-8-sig'))
    assert manifest['HechosObservaciones']['rows'] == 480
    assert manifest['HechosNotasOficiales']['rows'] == checks['filas_notas']
    assert manifest['HechosDesercionOficial']['rows'] == checks['filas_desercion_facultad_cohorte']
    assert conn.execute('SELECT COUNT(*) FROM "HechosNotasOficiales" WHERE "PromedioNotaParaAnalisis" IS NULL').fetchone()[0] == checks['promedios_cero_pendientes_de_validacion']
    for r in checks['totales_notas']:
        assert conn.execute('SELECT SUM("Inscritos"), SUM("Aprobados"), SUM("Reprobados") FROM "HechosNotasOficiales" WHERE "PeriodoAcademico" = ?', (r['PeriodoAcademico'],)).fetchone() == tuple(r[k] for k in ['Inscritos', 'Aprobados', 'Reprobados'])
    for r in checks['cohortes_verificadas']:
        assert conn.execute('SELECT SUM("MatriculadosIniciales"), SUM("DesertoresNetos") FROM "HechosDesercionOficial" WHERE "CohorteIngreso" = ?', (r['cohorte'],)).fetchone() == (r['matriculados_iniciales'], r['desertores'])
    assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    assert not conn.execute('PRAGMA foreign_key_check').fetchall()
    conn.commit()
    # Only replace generated artifacts after successful validation.
    staging = OUT / 'rendimiento.building.sqlite3'
    with sqlite3.connect(staging) as destination:
        conn.backup(destination)
    destination.close()
    staging.replace(OUT / 'rendimiento.sqlite3')
    header = '-- Generated from powerbi/data; import into a NEW schema. No DROP or DELETE.\n'
    setup = "BEGIN;\nSET LOCAL standard_conforming_strings = on;\nSET LOCAL client_encoding = 'UTF8';\nCREATE SCHEMA rendimiento;\nSET LOCAL search_path TO rendimiento;\n"
    (OUT / 'postgresql.sql').write_text(header + setup + '\n\n'.join(schema) + '\n\n' + '\n'.join(inserts) + '\nCOMMIT;\n', encoding='utf-8')
    (OUT / 'validation.json').write_text(json.dumps({'tables': manifest, 'checks': ['all source fields round-trip', 'primary and foreign keys', 'SQLite integrity', 'EDA view equals source CSV', 'official totals and 63 null analysis grades'], 'postgresql_execution_tested': False}, indent=2), encoding='utf-8')
    conn.close()
    print(json.dumps({k: v['rows'] for k, v in manifest.items()}, indent=2))
    print('PASS: all fields, relationships, EDA, nulls and published totals verified.')

if __name__ == '__main__':
    main()
