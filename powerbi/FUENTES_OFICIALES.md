# Complemento oficial: Universidad Nacional de Colombia, sede Medellín

## Resultado y alcance

La extracción produce **1.977 filas de asignatura y semestre** (1.255 códigos distintos) y **10 filas de facultad y cohorte** (cinco facultades en dos cohortes). Se preservan los PDF originales y la procedencia de cada fila. Los resultados son históricos, agregados y exclusivos de Medellín. No describen a los alumnos de xAPI ni permiten unir personas entre fuentes.

La autorización para complementar con fuentes oficiales permite conservar el análisis xAPI y añadir dos páginas independientes en Power BI. Los periodos de notas son 2015-2 y 2017-1; las cohortes de deserción son 2005-2 y 2006-1, observadas en 2010-1 y 2010-2 respectivamente. No son periodos consecutivos de notas ni una comparación contemporánea entre notas y deserción.

## Fuentes y cambio respecto de la búsqueda inicial

| Identificador | Publicación oficial | Tabla y ubicación |
|---|---|---|
| `notas_2015_2` | [Indicadores de rendimiento académico 2015-2](https://planeacion.medellin.unal.edu.co/images/01%20Contenido%20Articulos/Estadisticas/Rendimiento%20Academico/InfRa2015-2.pdf) | Tabla 19, páginas 24–43 del PDF |
| `notas_2017_1` | [Indicadores de rendimiento académico 2017-1](https://planeacion.medellin.unal.edu.co/images/01%20Contenido%20Articulos/Estadisticas/Rendimiento%20Academico/InfRa2017-1.pdf) | Tabla 19, páginas 24–43 del PDF |
| `desercion_2010` | [Boletín estadístico 2010](https://planeacion.medellin.unal.edu.co/images/01%20Contenido%20Articulos/Estadisticas/Boletines/boletin2010.pdf) | Tablas 12 y 13, páginas 26 y 27 del PDF (impresas 25 y 26) |

Se comprobó la descarga de estos tres PDF. Los datos del tablero SPADIES de Bogotá inicialmente recomendado no se incorporan: sus descargas respondieron HTTP 404 y el portal institucional no respondió a tiempo. La alternativa seleccionada contiene los conteos necesarios para calcular deserción por facultad en la misma sede de los informes de notas. Su metodología es la institucional histórica por cohorte, **no la tasa anual actual de SPADIES**. Tampoco se utiliza deserción precoz de admitidos.

## Reproducir la extracción

```powershell
python -m pip install -r requirements.txt
python etl/preparar_fuentes_oficiales.py
```

Los PDF están en `dataset/fuentes_oficiales/`. Para volver a obtenerlos de sus URL oficiales antes de extraer:

```powershell
python etl/preparar_fuentes_oficiales.py --descargar
```

El script usa `pypdf` para extraer las celdas de los PDF y `pandas` para generar CSV UTF-8. Verifica cantidad de filas, códigos únicos, rangos, tasas de reprobación, sumas por semestre y los componentes de la deserción. Acepta códigos de asignatura de siete y ocho dígitos: `32016007` es un código publicado, no un error que se deba truncar. Cada fila conserva fuente, tabla y página. `DimensionFuentesOficiales.csv` incluye URL y SHA-256; `VerificacionFuentesOficiales.json` resume las conciliaciones.

## Requerimiento 1: promedio de notas por materia y semestre

`HechosNotasOficiales` contiene una fila por código de asignatura y periodo. `PromedioNotaPublicado` conserva literalmente el promedio del informe. `PromedioNotaParaAnalisis` conserva los valores positivos y deja vacíos los 63 promedios publicados como cero, hasta validar su tipo de calificación. Los informes incluyen asignaturas con evaluación alfanumérica; por ejemplo, Inglés II tiene promedio 0,00 pero alumnos aprobados. No se asume que todos los ceros sean notas reales ni se afirma que todos representen evaluación alfanumérica. Es una exclusión conservadora documentada; no es una imputación.

La dimensión de asignaturas usa el nombre de la observación más reciente de cada código. El nombre y la escuela originales de cada periodo permanecen en la tabla de hechos. No se inventa una facultad a partir de la escuela.

La medida `Promedio de notas oficial` muestra el promedio publicado en cada celda asignatura-periodo. Deja los totales vacíos: un promedio simple de promedios no representa la nota de todos los estudiantes. Tampoco se reconstruyen notas individuales desde el promedio redondeado. Si se exige calcular el promedio desde microdatos, sigue siendo necesario obtener las notas individuales; esta entrega responde al indicador con estadísticas oficiales publicadas.

## Requerimiento 2: deserción por facultad

`HechosDesercionOficial` contiene solo los totales de las cinco facultades de las tablas 12 y 13. Se excluyen las filas de programas y el total general para evitar doble conteo. Los nombres históricos se preservan en `FacultadPublicada`; en la dimensión se expande `Ciencias Humanas y E.` a `Ciencias Humanas y Económicas`.

El boletín define desertores netos como:

```text
Desertores = MatriculadosIniciales - MatriculadosSeguimiento
             - ReservasCupo - (Graduados - GraduadosMatriculados)
Tasa de deserción = Desertores / MatriculadosIniciales
```

Las reservas de cupo forman parte del rezago según la nota metodológica del informe. Se preservan las transferencias publicadas, pero no se vuelven a sumar o restar a una fórmula que no las incluye. Se conserva por separado el semestre de ingreso y el corte de seguimiento. La medida requiere seleccionar una cohorte y calcula la tasa agregando los conteos de las facultades visibles, no promediando sus porcentajes.

## Cargar en Power BI

Importar los siete CSV siguientes desde `powerbi/data/`. **Los números decimales del CSV usan punto**: utilizar las consultas de `powerbi/consultas_oficiales/` para fijar la conversión con cultura `en-US`, independientemente de que Power BI muestre coma decimal en español. Esas consultas especifican también qué identificadores son texto.

| Tabla | Grano / clave |
|---|---|
| `HechosNotasOficiales` | Asignatura y periodo académico |
| `DimensionAsignaturasOficiales` | `CodigoAsignatura` |
| `DimensionPeriodosNotas` | `PeriodoAcademico` |
| `HechosDesercionOficial` | Facultad y cohorte de ingreso |
| `DimensionFacultadesOficiales` | `CodigoFacultad` |
| `DimensionCohortesDesercion` | `CohorteIngreso` |
| `DimensionFuentesOficiales` | `IdentificadorFuente` |

Crear relaciones activas **1 a varios, dirección única**:

```text
DimensionAsignaturasOficiales[CodigoAsignatura] -> HechosNotasOficiales[CodigoAsignatura]
DimensionPeriodosNotas[PeriodoAcademico] -> HechosNotasOficiales[PeriodoAcademico]
DimensionFacultadesOficiales[CodigoFacultad] -> HechosDesercionOficial[CodigoFacultad]
DimensionCohortesDesercion[CohorteIngreso] -> HechosDesercionOficial[CohorteIngreso]
DimensionFuentesOficiales[IdentificadorFuente] -> HechosNotasOficiales[IdentificadorFuente]
DimensionFuentesOficiales[IdentificadorFuente] -> HechosDesercionOficial[IdentificadorFuente]
```

No conectar estas tablas con `HechosObservaciones`, `DimensionTemas` o `DimensionSemestres` de xAPI. Las etiquetas de semestre F/S no son claves de periodo institucional.

Copiar las medidas de `medidas_oficiales.dax`, una por una. Formatear `Tasa de deserción por facultad` como porcentaje con dos decimales y `Promedio de notas oficial` como decimal con dos decimales.

### Página: Notas oficiales UNAL Medellín

- Matriz: filas `DimensionAsignaturasOficiales[CodigoAsignatura]` y `[Asignatura]`, columnas `DimensionPeriodosNotas[PeriodoAcademico]`, valor `[Promedio de notas oficial]`.
- Tarjetas: `[Registros de asignatura oficiales]`, `[Registros de notas por revisar]`.
- Nota visible: «Promedios publicados por UNAL Medellín; 2015-2 y 2017-1. Los ceros requieren validar el tipo de calificación. No son microdatos».
- Comprobación: código 1000004, Cálculo Diferencial, 2,62 en 2015-2 y 2,58 en 2017-1.

### Página: Deserción por facultad UNAL Medellín

- Segmentación de selección única: `DimensionCohortesDesercion[CohorteIngreso]`.
- Mostrar `PeriodoSeguimiento` de esa dimensión en una tarjeta para identificar el corte.
- Barras: eje de categorías `DimensionFacultadesOficiales[Facultad]`, valor `[Tasa de deserción por facultad]`.
- Matriz auxiliar: facultad, `[Matriculados iniciales cohorte]`, `[Desertores netos cohorte]` y tasa.
- Nota visible: «Deserción neta por cohorte según boletín UNAL Medellín 2010. Cohortes 2005-2 y 2006-1; cortes 2010-1 y 2010-2».

## Verificación y resultados

| Control | Resultado |
|---|---|
| Asignatura-periodo, 2015-2 | 990 filas; 49.607 inscripciones = 41.499 aprobadas + 8.108 reprobadas |
| Asignatura-periodo, 2017-1 | 987 filas; 49.006 inscripciones = 41.524 aprobadas + 7.482 reprobadas |
| Cohorte 2005-2, corte 2010-1 | 653 / 1.295 = 50,424710 %; boletín redondea a 50,4 % |
| Cohorte 2006-1, corte 2010-2 | 586 / 1.404 = 41,737892 %; boletín redondea a 41,7 % |
| Facultad Ciencias, cohorte 2005-2 | 100 / 146 = 68,493151 %; boletín 68,5 % |
| Facultad Minas, cohorte 2006-1 | 247 / 755 = 32,715232 %; boletín 32,7 % |

Se revisaron visualmente las tablas de deserción y la primera página de notas; las sumas completas de notas se conciliaron con la tabla 1 de cada informe. Los PDF permiten auditar cada celda. No se atribuye causalidad entre las notas de 2015/2017 y las cohortes observadas en 2010.

Los CSV, consultas y medidas están preparados. El archivo `.pbix` existente debe incorporar estas tablas y visualizaciones para mostrar el complemento; la generación de CSV no equivale a haber actualizado ese archivo.
