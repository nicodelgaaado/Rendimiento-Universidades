"""Compare the Azure SQL export field-for-field with the project CSV sources."""
from pathlib import Path
from collections import Counter
from decimal import Decimal
import csv
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / "powerbi" / "data"
INTEGER = set("IdTema IdSemestre IdObservacion AnioAcademico Semestre VecesManoLevantada RecursosVisitados AnunciosVistos ParticipacionesDiscusion Inscritos Aprobados Reprobados Repitentes PaginaArchivoFuente TablaFuente MatriculadosIniciales MatriculadosSeguimiento ReservasCupo Graduados GraduadosMatriculados DesertoresNetos TransferenciasSalida TransferenciasEntrada PaginaImpresaFuente".split())
DECIMAL = set("PromedioNotaPublicado PromedioNotaParaAnalisis DesviacionNotaPublicada PorcentajeReprobacionPublicado PorcentajeRepitenciaPublicado PorcentajeDesercionPublicado".split())
TABLES = ["DimensionTemas", "DimensionSemestres", "DimensionAsignaturasOficiales", "DimensionPeriodosNotas", "DimensionFacultadesOficiales", "DimensionCohortesDesercion", "DimensionFuentesOficiales", "HechosObservaciones", "HechosNotasOficiales", "HechosDesercionOficial"]

def value(v, column):
    if v is None or v == "": return None
    if column in INTEGER: return int(v)
    if column in DECIMAL: return Decimal(str(v))
    return str(v)

export = json.loads((HERE / "azure_sql_export.json").read_text(encoding="utf-8-sig"), parse_float=Decimal)
report = {"tables": {}, "checks": []}
for table in TABLES:
    with (DATA / f"{table}.csv").open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        columns = reader.fieldnames
        expected = Counter(tuple(value(row[c], c) for c in columns) for row in reader)
    actual_rows = export[table]
    assert not actual_rows or list(actual_rows[0]) == columns, f"Column mismatch: {table}"
    actual = Counter(tuple(value(row[c], c) for c in columns) for row in actual_rows)
    assert expected == actual, f"Data mismatch: {table}"
    report["tables"][table] = len(actual_rows)

with (DATA / "EDA_TemaSemestreRendimiento.csv").open(encoding="utf-8-sig", newline="") as source:
    expected_eda = Counter((r["Tema"], r["CodigoSemestre"], r["CategoriaRendimiento"], int(r["Observaciones"])) for r in csv.DictReader(source))
actual_eda = Counter((r["Tema"], r["CodigoSemestre"], r["CategoriaRendimiento"], int(r["Observaciones"])) for r in export["EDA_TemaSemestreRendimiento"])
assert expected_eda == actual_eda, "EDA view mismatch"
meta = export["_metadata"]
assert meta["tables_count"] == 10 and meta["views_count"] == 1
assert meta["primary_keys"] == 10 and meta["foreign_keys"] == 9
assert meta["check_constraints"] >= 1
assert meta["encryption_state"] == 3 and meta["connection_encrypted"] == "TRUE"
grades = export["HechosNotasOficiales"]
assert sum(r["PromedioNotaParaAnalisis"] is None for r in grades) == 63
grade_totals = {}
for row in grades:
    key = row["PeriodoAcademico"]
    total = grade_totals.setdefault(key, [0, 0, 0])
    for i, column in enumerate(("Inscritos", "Aprobados", "Reprobados")): total[i] += row[column]
assert grade_totals == {"2015-2": [49607, 41499, 8108], "2017-1": [49006, 41524, 7482]}
report["checks"] = ["all fields and duplicate multiplicities match CSV", "EDA view matches CSV", "10 PKs and 9 FKs present", "TDE active and connection encrypted", "63 analysis nulls and published totals match"]
report["metadata"] = meta
report["result"] = "PASS"
(HERE / "azure_sql_fact_check_results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
