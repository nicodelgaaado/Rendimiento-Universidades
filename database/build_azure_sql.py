"""Generate a transactional Azure SQL (T-SQL) import from verified project CSVs."""
from pathlib import Path
import csv
from decimal import Decimal

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
DATA = ROOT / "powerbi" / "data"
SCHEMA = "rendimiento"

INTEGERS = set("IdTema IdSemestre IdObservacion AnioAcademico Semestre VecesManoLevantada RecursosVisitados AnunciosVistos ParticipacionesDiscusion Inscritos Aprobados Reprobados Repitentes PaginaArchivoFuente TablaFuente MatriculadosIniciales MatriculadosSeguimiento ReservasCupo Graduados GraduadosMatriculados DesertoresNetos TransferenciasSalida TransferenciasEntrada PaginaImpresaFuente".split())
DECIMALS = set("PromedioNotaPublicado PromedioNotaParaAnalisis DesviacionNotaPublicada PorcentajeReprobacionPublicado PorcentajeRepitenciaPublicado PorcentajeDesercionPublicado".split())
KEY_TEXT = set("CodigoSemestre CodigoAsignatura PeriodoAcademico CodigoFacultad CohorteIngreso PeriodoSeguimiento IdentificadorFuente".split())
TABLES = {
    "DimensionTemas": ["IdTema"],
    "DimensionSemestres": ["IdSemestre"],
    "DimensionAsignaturasOficiales": ["CodigoAsignatura"],
    "DimensionPeriodosNotas": ["PeriodoAcademico"],
    "DimensionFacultadesOficiales": ["CodigoFacultad"],
    "DimensionCohortesDesercion": ["CohorteIngreso"],
    "DimensionFuentesOficiales": ["IdentificadorFuente"],
    "HechosObservaciones": ["IdObservacion"],
    "HechosNotasOficiales": ["CodigoAsignatura", "PeriodoAcademico"],
    "HechosDesercionOficial": ["CodigoFacultad", "CohorteIngreso"],
}
RELATIONS = {
    "HechosObservaciones": [("IdTema", "DimensionTemas", "IdTema"), ("IdSemestre", "DimensionSemestres", "IdSemestre")],
    "HechosNotasOficiales": [("CodigoAsignatura", "DimensionAsignaturasOficiales", "CodigoAsignatura"), ("PeriodoAcademico", "DimensionPeriodosNotas", "PeriodoAcademico"), ("IdentificadorFuente", "DimensionFuentesOficiales", "IdentificadorFuente")],
    "HechosDesercionOficial": [("CodigoFacultad", "DimensionFacultadesOficiales", "CodigoFacultad"), ("CohorteIngreso", "DimensionCohortesDesercion", "CohorteIngreso"), ("IdentificadorFuente", "DimensionFuentesOficiales", "IdentificadorFuente")],
}
CHECKS = {
    "DimensionSemestres": ["[IdSemestre] IN (1,2)", "[CodigoSemestre] IN (N'F',N'S')"],
    "DimensionPeriodosNotas": ["[Semestre] IN (1,2)"],
    "HechosObservaciones": ["[CategoriaRendimiento] IN (N'L',N'M',N'H')"] + [f"[{c}] BETWEEN 0 AND 100" for c in ["VecesManoLevantada", "RecursosVisitados", "AnunciosVistos", "ParticipacionesDiscusion"]],
    "HechosNotasOficiales": ["[Inscritos] > 0", "[Inscritos] = [Aprobados] + [Reprobados]", "[PromedioNotaPublicado] BETWEEN 0 AND 5", "[DesviacionNotaPublicada] >= 0", "([PromedioNotaPublicado] = 0 AND [PromedioNotaParaAnalisis] IS NULL) OR ([PromedioNotaPublicado] > 0 AND [PromedioNotaParaAnalisis] IS NOT NULL AND [PromedioNotaParaAnalisis] = [PromedioNotaPublicado])"],
    "HechosDesercionOficial": ["[MatriculadosIniciales] > 0", "[DesertoresNetos] = [MatriculadosIniciales] - [MatriculadosSeguimiento] - [ReservasCupo] - ([Graduados] - [GraduadosMatriculados])"],
}

def q(name): return "[" + name.replace("]", "]]" ) + "]"
def full(name): return f"{q(SCHEMA)}.{q(name)}"

def sql_type(column):
    if column in INTEGERS: return "INT"
    if column in DECIMALS: return "DECIMAL(12,6)"
    if column == "HuellaSHA256": return "CHAR(64)"
    if column in KEY_TEXT: return "NVARCHAR(100)"
    return "NVARCHAR(2048)"

def literal(value, column):
    if value == "" and column == "PromedioNotaParaAnalisis": return "NULL"
    if column in INTEGERS:
        return str(int(value))
    if column in DECIMALS:
        number = Decimal(value)
        if not number.is_finite(): raise ValueError(f"Non-finite decimal in {column}")
        return format(number, "f")
    return "N'" + value.replace("'", "''") + "'"

def read(name):
    with (DATA / f"{name}.csv").open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        return reader.fieldnames, list(reader)

def create_table(name, columns):
    parts = []
    checks = []
    for column in columns:
        nullable = "NULL" if column == "PromedioNotaParaAnalisis" else "NOT NULL"
        parts.append(f"  {q(column)} {sql_type(column)} {nullable}")
        if column in INTEGERS: checks.append(f"{q(column)} >= 0")
        if column.startswith("Porcentaje"): checks.append(f"{q(column)} BETWEEN 0 AND 100")
    parts.append("  CONSTRAINT " + q(f"PK_{name}") + " PRIMARY KEY (" + ", ".join(map(q, TABLES[name])) + ")")
    for column, target, key in RELATIONS.get(name, []):
        parts.append(f"  CONSTRAINT {q('FK_' + name + '_' + column)} FOREIGN KEY ({q(column)}) REFERENCES {full(target)} ({q(key)})")
    if name == "DimensionCohortesDesercion": parts.append("  CONSTRAINT [UQ_CohorteSeguimiento] UNIQUE ([CohorteIngreso], [PeriodoSeguimiento])")
    if name == "DimensionSemestres": parts.append("  CONSTRAINT [UQ_CodigoSemestre] UNIQUE ([CodigoSemestre])")
    if name == "HechosDesercionOficial": parts.append("  CONSTRAINT [FK_Desercion_CohorteSeguimiento] FOREIGN KEY ([CohorteIngreso], [PeriodoSeguimiento]) REFERENCES [rendimiento].[DimensionCohortesDesercion] ([CohorteIngreso], [PeriodoSeguimiento])")
    parts.extend("  CHECK (" + check + ")" for check in checks + CHECKS.get(name, []))
    return f"CREATE TABLE {full(name)} (\n" + ",\n".join(parts) + "\n);"

def main():
    batches = ["SET NOCOUNT ON;\nSET XACT_ABORT ON;\nBEGIN TRANSACTION;", "IF SCHEMA_ID(N'rendimiento') IS NOT NULL THROW 51000, 'Schema rendimiento already exists', 1;\nEXEC(N'CREATE SCHEMA [rendimiento]');"]
    loaded = {}
    for name in TABLES:
        columns, rows = read(name)
        loaded[name] = (columns, rows)
        batches.append(create_table(name, columns))
        colsql = ", ".join(map(q, columns))
        for start in range(0, len(rows), 500):
            values = []
            for row in rows[start:start + 500]:
                values.append("(" + ", ".join(literal(row[c], c) for c in columns) + ")")
            batches.append(f"INSERT INTO {full(name)} ({colsql}) VALUES\n" + ",\n".join(values) + ";")
    for name, relations in RELATIONS.items():
        for column, _, _ in relations:
            batches.append(f"CREATE INDEX {q('IX_' + name + '_' + column)} ON {full(name)} ({q(column)});")
    batches.append("""CREATE VIEW [rendimiento].[EDA_TemaSemestreRendimiento] AS
SELECT t.[Tema], s.[CodigoSemestre], h.[CategoriaRendimiento], COUNT(*) AS [Observaciones]
FROM [rendimiento].[HechosObservaciones] AS h
JOIN [rendimiento].[DimensionTemas] AS t ON t.[IdTema] = h.[IdTema]
JOIN [rendimiento].[DimensionSemestres] AS s ON s.[IdSemestre] = h.[IdSemestre]
GROUP BY t.[Tema], s.[CodigoSemestre], h.[CategoriaRendimiento];""")
    batches.append("CREATE ROLE [rendimiento_reader];\nGRANT SELECT ON SCHEMA::[rendimiento] TO [rendimiento_reader];")
    for name, (_, rows) in loaded.items():
        batches.append(f"IF (SELECT COUNT_BIG(*) FROM {full(name)}) <> {len(rows)} THROW 51001, 'Unexpected row count in {name}', 1;")
    batches.append("COMMIT TRANSACTION;")
    (OUT / "azure_sql.sql").write_text("\nGO\n".join(batches) + "\nGO\n", encoding="utf-8")
    print({name: len(rows) for name, (_, rows) in loaded.items()})

if __name__ == "__main__":
    main()
