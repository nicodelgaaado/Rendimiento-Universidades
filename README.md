# Rendimiento-Universidades

Proyecto Final - Herramientas Computacionales. Preparación de datos y modelo para Power BI.

1. Ejecutar `python etl/prepare_xapi.py` (requiere `pandas`).
2. Importar los tres CSV `HechosObservaciones.csv`, `DimensionTemas.csv` y `DimensionSemestres.csv` de `powerbi/data/` en Power BI.
3. Crear las relaciones y medidas según [MODELO_Y_EDA.md](powerbi/MODELO_Y_EDA.md).

**Límite de la fuente:** el dataset xAPI disponible no contiene notas numéricas, facultades ni seguimiento de matrículas. Por ello los requerimientos de promedio de notas y tasa de deserción necesitan datos adicionales. La documentación especifica los campos y las medidas para incorporarlos sin confundir la categoría `L/M/H` con una nota o una deserción.

## Pendiente: requerimientos analíticos 1 y 2

Los dos requerimientos asignados siguen pendientes de resolución por falta de datos en la fuente actual:

| Requerimiento | Datos disponibles | Datos faltantes y trabajo pendiente |
|---|---|---|
| **1. Promedio de notas por materia y semestre** | Tema, semestre y categoría de rendimiento `L/M/H`. | Obtener notas numéricas individuales con su materia y periodo académico; validar la escala y el grano de los registros; calcular el promedio y visualizarlo por materia y semestre. |
| **2. Tasa de deserción por facultad** | Categoría de ausencias y categoría de rendimiento. | Obtener identificador de estudiante, facultad, periodos e historial de matrícula y estados académicos; acordar la definición de deserción y su denominador; calcular la tasa por facultad con seguimiento suficiente. |

Las categorías `L/M/H` corresponden a intervalos de notas, pero no permiten recuperar las notas exactas. Las ausencias y el rendimiento bajo tampoco demuestran deserción. No se deben asignar notas inventadas ni presentar el porcentaje de rendimiento bajo como tasa de deserción.

### Próximo paso

Consultar con el profesor si se autoriza **complementar o cambiar el dataset** para obtener los campos faltantes, o **adaptar los requerimientos** a las variables disponibles. Esta decisión aún está pendiente; no hay una adaptación aprobada.

Una vez acordada la alternativa, actualizar el ETL y el modelo, implementar los indicadores correspondientes y validar sus resultados en Power BI. Las medidas de notas y deserción incluidas en `powerbi/medidas.dax` son plantillas que requieren tablas adicionales; no constituyen resultados calculados con el CSV actual.

### Trabajo que ya sirve como avance

El ETL, el modelo por tema y semestre y la exploración básica permiten analizar las 480 observaciones. Las medidas implementadas con `COUNT`, `SUM`, `AVERAGE` y `CALCULATE` describen cantidad de registros, actividad y rendimiento categórico. Este avance respalda la exploración y el uso de DAX, pero **no completa los requerimientos 1 y 2**.
