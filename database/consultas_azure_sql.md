# Consultas para Azure SQL Database

Base de datos: `rendimiento-universidades`
Esquema: `rendimiento`

Ejecuta cada consulta por separado desde **Azure Portal → SQL database → Query editor → New query**.

## 1. Ver registros de notas

```sql
SELECT TOP (100) *
FROM [rendimiento].[HechosNotasOficiales]
ORDER BY [PeriodoAcademico], [CodigoAsignatura];
```

## 2. Totales académicos por periodo

```sql
SELECT
    [PeriodoAcademico],
    SUM([Inscritos]) AS Inscritos,
    SUM([Aprobados]) AS Aprobados,
    SUM([Reprobados]) AS Reprobados,
    CAST(
        100.0 * SUM([Reprobados]) / NULLIF(SUM([Inscritos]), 0)
        AS DECIMAL(6,2)
    ) AS PorcentajeReprobacion
FROM [rendimiento].[HechosNotasOficiales]
GROUP BY [PeriodoAcademico]
ORDER BY [PeriodoAcademico];
```

## 3. Materias con mayor promedio

```sql
SELECT TOP (20)
    [PeriodoAcademico],
    [CodigoAsignatura],
    [AsignaturaPublicada],
    [Inscritos],
    [PromedioNotaParaAnalisis]
FROM [rendimiento].[HechosNotasOficiales]
WHERE [PromedioNotaParaAnalisis] IS NOT NULL
ORDER BY [PromedioNotaParaAnalisis] DESC, [Inscritos] DESC;
```

## 4. Materias con mayor reprobación

```sql
SELECT TOP (20)
    [PeriodoAcademico],
    [AsignaturaPublicada],
    [Inscritos],
    [Reprobados],
    [PorcentajeReprobacionPublicado]
FROM [rendimiento].[HechosNotasOficiales]
WHERE [Inscritos] >= 20
ORDER BY [PorcentajeReprobacionPublicado] DESC;
```

## 5. Comparar una materia entre periodos

```sql
SELECT
    [CodigoAsignatura],
    MAX([AsignaturaPublicada]) AS Asignatura,
    MAX(CASE WHEN [PeriodoAcademico] = N'2015-2'
             THEN [PromedioNotaParaAnalisis] END) AS Promedio2015_2,
    MAX(CASE WHEN [PeriodoAcademico] = N'2017-1'
             THEN [PromedioNotaParaAnalisis] END) AS Promedio2017_1,
    MAX(CASE WHEN [PeriodoAcademico] = N'2017-1'
             THEN [PromedioNotaParaAnalisis] END)
    -
    MAX(CASE WHEN [PeriodoAcademico] = N'2015-2'
             THEN [PromedioNotaParaAnalisis] END) AS CambioPromedio
FROM [rendimiento].[HechosNotasOficiales]
WHERE [PromedioNotaParaAnalisis] IS NOT NULL
GROUP BY [CodigoAsignatura]
HAVING COUNT(DISTINCT [PeriodoAcademico]) = 2
ORDER BY CambioPromedio DESC;
```

## 6. Deserción total por cohorte

```sql
SELECT
    [CohorteIngreso],
    SUM([MatriculadosIniciales]) AS MatriculadosIniciales,
    SUM([DesertoresNetos]) AS Desertores,
    CAST(
        100.0 * SUM([DesertoresNetos])
        / NULLIF(SUM([MatriculadosIniciales]), 0)
        AS DECIMAL(6,2)
    ) AS PorcentajeDesercion
FROM [rendimiento].[HechosDesercionOficial]
GROUP BY [CohorteIngreso]
ORDER BY [CohorteIngreso];
```

## 7. Deserción por facultad

```sql
SELECT
    [CohorteIngreso],
    [FacultadPublicada],
    [MatriculadosIniciales],
    [DesertoresNetos],
    [PorcentajeDesercionPublicado]
FROM [rendimiento].[HechosDesercionOficial]
ORDER BY [CohorteIngreso], [PorcentajeDesercionPublicado] DESC;
```

## 8. Distribución del rendimiento xAPI

```sql
SELECT
    [CategoriaRendimiento],
    COUNT(*) AS Observaciones,
    CAST(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER ()
        AS DECIMAL(6,2)
    ) AS Porcentaje
FROM [rendimiento].[HechosObservaciones]
GROUP BY [CategoriaRendimiento]
ORDER BY [CategoriaRendimiento];
```

## 9. Actividad promedio según rendimiento

```sql
SELECT
    [CategoriaRendimiento],
    COUNT(*) AS Observaciones,
    CAST(AVG(1.0 * [VecesManoLevantada]) AS DECIMAL(6,2)) AS PromedioManoLevantada,
    CAST(AVG(1.0 * [RecursosVisitados]) AS DECIMAL(6,2)) AS PromedioRecursos,
    CAST(AVG(1.0 * [AnunciosVistos]) AS DECIMAL(6,2)) AS PromedioAnuncios,
    CAST(AVG(1.0 * [ParticipacionesDiscusion]) AS DECIMAL(6,2)) AS PromedioDiscusion
FROM [rendimiento].[HechosObservaciones]
GROUP BY [CategoriaRendimiento]
ORDER BY [CategoriaRendimiento];
```

## 10. Rendimiento por tema

```sql
SELECT
    t.[Tema],
    h.[CategoriaRendimiento],
    COUNT(*) AS Observaciones
FROM [rendimiento].[HechosObservaciones] AS h
JOIN [rendimiento].[DimensionTemas] AS t
    ON t.[IdTema] = h.[IdTema]
GROUP BY t.[Tema], h.[CategoriaRendimiento]
ORDER BY t.[Tema], h.[CategoriaRendimiento];
```

## 11. Ausencias frente al rendimiento

```sql
SELECT
    [CategoriaAusencias],
    [CategoriaRendimiento],
    COUNT(*) AS Observaciones
FROM [rendimiento].[HechosObservaciones]
GROUP BY [CategoriaAusencias], [CategoriaRendimiento]
ORDER BY [CategoriaAusencias], [CategoriaRendimiento];
```

## 12. Contar filas de todas las tablas

```sql
SELECT
    s.[name] AS Esquema,
    t.[name] AS Tabla,
    SUM(p.[rows]) AS Filas
FROM sys.tables AS t
JOIN sys.schemas AS s
    ON s.[schema_id] = t.[schema_id]
JOIN sys.partitions AS p
    ON p.[object_id] = t.[object_id]
   AND p.[index_id] IN (0, 1)
WHERE s.[name] = N'rendimiento'
GROUP BY s.[name], t.[name]
ORDER BY t.[name];
```
