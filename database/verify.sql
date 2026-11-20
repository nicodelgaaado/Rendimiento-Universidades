-- Expected: 480 observations, 1977 grades, 10 dropout facts, 63 null grades.
SELECT COUNT(*) AS observations FROM rendimiento."HechosObservaciones";
SELECT COUNT(*) AS grades FROM rendimiento."HechosNotasOficiales";
SELECT COUNT(*) AS dropout_facts FROM rendimiento."HechosDesercionOficial";
SELECT COUNT(*) AS null_analysis_grades
FROM rendimiento."HechosNotasOficiales" WHERE "PromedioNotaParaAnalisis" IS NULL;

-- 2015-2: 49607 / 41499 / 8108; 2017-1: 49006 / 41524 / 7482.
SELECT "PeriodoAcademico", SUM("Inscritos"), SUM("Aprobados"), SUM("Reprobados")
FROM rendimiento."HechosNotasOficiales"
GROUP BY "PeriodoAcademico" ORDER BY "PeriodoAcademico";

-- 2005-2: 1295 / 653; 2006-1: 1404 / 586.
SELECT "CohorteIngreso", SUM("MatriculadosIniciales"), SUM("DesertoresNetos")
FROM rendimiento."HechosDesercionOficial"
GROUP BY "CohorteIngreso" ORDER BY "CohorteIngreso";

-- Expected EDA observation sum: 480.
SELECT SUM("Observaciones") FROM rendimiento."EDA_TemaSemestreRendimiento";
