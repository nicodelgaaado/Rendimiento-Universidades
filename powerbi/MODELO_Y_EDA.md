# ETL, modelo y exploración para Power BI

## Alcance y límite de la fuente

El enunciado del Proyecto 2 pide (1) promedio de notas por materia y semestre y (2) tasa de deserción por facultad. El CSV `xAPI-Edu-Data.csv` contiene 480 observaciones, 12 temas (`Topic`), dos códigos de semestre (`F`, `S`) y una **categoría de rendimiento** (`Class`: L/M/H). No contiene nota numérica, facultad, programa universitario, ID de estudiante, año, ni historial de matrícula. Además `StageID` y `GradeID` describen niveles y grados escolares. Por tanto, esta fuente por sí sola **no permite calcular ninguno de los dos indicadores pedidos**. `Class` no es una nota y la categoría de ausencias no es deserción.

Precisión: según la [ficha del autor en Kaggle](https://www.kaggle.com/aljarah/xAPI-Edu-Data/metadata), `Class` se obtiene de la nota total: L = 0–69, M = 70–89 y H = 90–100. Son intervalos de notas, no valores individuales. Asignar puntos medios daría una estimación basada en un supuesto; no recuperaría el promedio real ni demuestra que la categoría represente la nota de cada materia. El archivo tiene 16 atributos más `Class`: 17 columnas.

## ETL reproducible

Ejecutar desde la raíz del repositorio: `python etl/prepare_xapi.py`. Requiere `pandas`. La extracción lee el CSV original; la transformación normaliza nombres de columnas, quita espacios marginales, valida nulos, categorías y rango de las cuatro variables de actividad. La carga escribe CSV con UTF-8 y BOM en `powerbi/data/` para importar mediante **Obtener datos > Texto/CSV**. El archivo original se mantiene intacto. `IdObservacion` identifica **filas**, no estudiantes. Las dos filas idénticas se preservan porque no hay ID con el que demostrar duplicación de una persona.

## Modelo semántico

Los archivos y encabezados exportados usan nomenclatura en español. Los valores se conservan: por ejemplo, `IT`, `Math`, `First`, `Second`, `M`, `F`, `L`, `Under-7` y `Above-7` permanecen como estaban. Las columnas del CSV original mantienen sus nombres originales; el cambio se aplica al exportar.

Si ya importaste las tablas con los nombres anteriores, vuelve a importar `HechosObservaciones.csv`, `DimensionTemas.csv` y `DimensionSemestres.csv` y usa las referencias actualizadas de `medidas.dax`. Sustituye las consultas anteriores para evitar mantener dos copias del modelo. Los CSV de EDA son resúmenes auxiliares y no forman parte de las relaciones del modelo.

| Tabla | Grano y clave | Relación |
|---|---|
| `HechosObservaciones` | Una fila por observación; `IdObservacion` | `IdTema` y `IdSemestre` son claves externas |
| `DimensionTemas` | Una fila por tema; `IdTema` | 1 a muchos hacia `HechosObservaciones` |
| `DimensionSemestres` | Una fila por código F/S; `IdSemestre` | 1 a muchos hacia `HechosObservaciones` |

En la vista Modelo, configurar filtros **de dimensión a hecho, dirección única**. Mostrar `DimensionTemas[Tema]` y `DimensionSemestres[NombreSemestre]` en visualizaciones. `IdSemestre` solo ordena F/S; **no representa un periodo cronológico** porque falta el año. Mantener `HechosObservaciones` separado de las tablas suplementarias descritas abajo: no existe una clave de estudiante para unir registros individuales.

## EDA del archivo disponible

Ver `powerbi/data/EDA_summary.json` y `EDA_TemaSemestreRendimiento.csv` (conteos por tema, semestre y clase). La distribución global permite explorar clases de rendimiento, actividad y ausencias. La proporción de clase L es un **indicador descriptivo**, no una tasa de reprobación ni de deserción. Dos filas idénticas se cuentan como observaciones separadas. No se puede seguir una cohorte entre F y S.

Comprobación del CSV: 480 filas; cero celdas vacías; 245 registros F y 235 S; clases L = 127, M = 211 y H = 142. Hay dos grupos de dos filas idénticas, es decir, dos repeticiones adicionales respecto de 478 combinaciones únicas. Se conserva la totalidad de las filas. El porcentaje global de clase L es 127 / 480 = 26,46 %.

Visuales exploratorios propuestos: barras apiladas de `CategoriaRendimiento` por `DimensionTemas[Tema]` y `DimensionSemestres[NombreSemestre]`; barras del porcentaje de clase L por tema; dispersión de `VecesManoLevantada` y `RecursosVisitados` coloreada por `CategoriaRendimiento`. En todos ellos, titular como *rendimiento categórico* o *actividad*.

## Datos adicionales necesarios para los requerimientos 1 y 2

Solicitar una fuente institucional con diccionario y periodo completo. Mínimo:

| Tabla externa | Campos mínimos | Grano |
|---|---|---|
| `HechosNotas` | `IdEstudiante`, `IdTema`, `IdPeriodo`, `NotaNumerica` | Una nota final por estudiante, materia y periodo; si hay intentos, definir regla de agregación |
| `HechosMatriculas` | `IdEstudiante`, `IdFacultad`, `IdPeriodo`, `ElegibleParaDesercion`, `IndicadorDesercion` | Una matrícula por estudiante, facultad y periodo |
| `DimensionPeriodos` | `IdPeriodo`, `AnioAcademico`, `CodigoSemestre`, `IdPeriodoSiguiente` | Un periodo académico con orden temporal real |
| `DimensionFacultades` | `IdFacultad`, `NombreFacultad` | Una facultad |

Validar claves únicas y foráneas, rango y escala de `NotaNumerica`, política de notas faltantes y que los periodos estén completos. Conectar `DimensionTemas` a `HechosNotas` **solo si existe una equivalencia verificada entre temas xAPI y materias institucionales**; en caso contrario crear `DimensionMaterias` propia y usar `IdMateria` en `HechosNotas`. Conectar `DimensionPeriodos` a `HechosNotas` y `HechosMatriculas`; `DimensionFacultades` a `HechosMatriculas` con relaciones 1 a muchos y dirección única. Si se necesitan notas por facultad, añadir `IdFacultad` a `HechosNotas` o una dimensión de programa con relación documentada. No asociar `DimensionSemestres` de xAPI con `DimensionPeriodos` por F/S solamente: mezclaría años distintos.

**Definición pendiente de acordar:** una ausencia de matrícula en el siguiente semestre no basta para adoptar el criterio colombiano de deserción. [SPADIES](https://mineducacion.gov.co/sistemasinfo/spadies/secciones/Ayuda/Preguntas-frecuentes/) distingue deserción de programa, institución y sistema, y utiliza dos o más periodos consecutivos sin matrícula. La definición de desertor del sistema excluye graduados y retiros disciplinarios. Una tasa por facultad requiere especificar además la atribución de cambios de programa o facultad; no es automáticamente uno de los indicadores oficiales.

Para una medida local basada en dos periodos, `IdPeriodo` en `HechosMatriculas` identifica el periodo base de matrícula t. Derivar `IndicadorDesercion` con seguimiento completo de t+1 y t+2 y la política institucional acordada. Marcar `ElegibleParaDesercion = FALSE` cuando no se observe esa ventana (incluidos los últimos dos periodos de una serie semestral completa) o falte seguimiento fiable. No inferir deserción a partir de `StudentAbsenceDays`. El denominador debe corresponder a la misma población y periodo base del numerador. Esta propuesta no implementa por sí sola la metodología oficial SPADIES.

## Medidas y visuales en Power BI

Copiar las medidas de `medidas.dax` a una tabla de medidas. Las cinco primeras funcionan con los CSV entregados y demuestran `COUNT`, `SUM`, `AVERAGE` y `CALCULATE`. Las siguientes solo funcionarán después de cargar las tablas externas. Configurar `Porcentaje rendimiento bajo` y `Tasa de deserción` como porcentaje; la escala de `Promedio de notas` debe coincidir con la fuente institucional.

`KEEPFILTERS` hace que el conteo de clase L respete los filtros de rendimiento existentes; sin él, `CALCULATE` sustituiría el filtro de esa columna, lo cual podía producir porcentajes incorrectos al seleccionar otra clase. Véase [Microsoft Learn](https://learn.microsoft.com/en-us/dax/keepfilters-function-dax). La tasa de deserción devuelve vacío cuando el contexto contiene varios periodos base: contar estudiantes distintos sobre varios periodos mezcla poblaciones y no produce una tasa semestral. Ocultar los indicadores booleanos de deserción de los segmentadores del informe para mantener el universo del denominador.

**Estado de entrega:** se ejecutó y verificó el ETL y se generaron CSV, resúmenes y esta propuesta de modelo. La exploración entregada es descriptiva básica. No se creó un archivo `.pbix`, ni se ejecutaron las medidas DAX en Power BI; requieren importación, relaciones, tipos de datos y validación en esa aplicación. Las medidas institucionales son plantillas y aún no producen resultados reales.

Para el requerimiento 1: matriz con `DimensionMaterias[NombreMateria]` (o `DimensionTemas[Tema]` si la equivalencia fue validada) en filas, `DimensionPeriodos[AnioAcademico]` y `DimensionPeriodos[CodigoSemestre]` en columnas, y `[Promedio de notas]` como valor. Para el requerimiento 2: barras de `DimensionFacultades[NombreFacultad]` con `[Tasa de deserción]`, filtradas por `DimensionPeriodos[IdPeriodo]`; mostrar además el numerador y denominador. No presentar visuales vacíos como resultados calculados.
