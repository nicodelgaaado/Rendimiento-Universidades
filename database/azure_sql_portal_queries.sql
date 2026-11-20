-- List the deployed tables and their row counts.
SELECT
    s.name AS schema_name,
    t.name AS table_name,
    SUM(p.rows) AS row_count
FROM sys.tables AS t
JOIN sys.schemas AS s ON s.schema_id = t.schema_id
JOIN sys.partitions AS p ON p.object_id = t.object_id AND p.index_id IN (0, 1)
WHERE s.name = N'rendimiento'
GROUP BY s.name, t.name
ORDER BY t.name;

-- Preview records from the three fact tables.
SELECT TOP (100) * FROM [rendimiento].[HechosObservaciones] ORDER BY [IdObservacion];
SELECT TOP (100) * FROM [rendimiento].[HechosNotasOficiales] ORDER BY [PeriodoAcademico], [CodigoAsignatura];
SELECT TOP (100) * FROM [rendimiento].[HechosDesercionOficial] ORDER BY [CohorteIngreso], [CodigoFacultad];

-- Preview the computed EDA view.
SELECT TOP (100) *
FROM [rendimiento].[EDA_TemaSemestreRendimiento]
ORDER BY [Tema], [CodigoSemestre], [CategoriaRendimiento];
