# Rendimiento-Universidades

Proyecto final de Herramientas Computacionales: ETL, modelo de datos, EDA y
medidas DAX para Power BI.

El proyecto conserva el análisis exploratorio de xAPI-Edu-Data y añade un
complemento oficial de la Universidad Nacional de Colombia, sede Medellín. Las
dos familias de datos se mantienen separadas porque describen poblaciones,
periodos y niveles de detalle distintos.

## Estado de los requerimientos

1. **ETL, modelo y EDA:** implementados para xAPI y para las fuentes oficiales.
2. **Promedio de notas por materia y semestre:** preparado con 1.977 registros
   oficiales de asignatura-periodo, correspondientes a 2015-2 y 2017-1.
3. **Deserción por facultad:** preparada con cinco facultades y dos cohortes
   institucionales, 2005-2 y 2006-1, observadas diez semestres después.
4. **DAX:** se incluyen medidas con COUNT, SUM, AVERAGE y CALCULATE para xAPI,
   y medidas de promedio publicado y tasa de deserción para el complemento.

La preparación de datos está terminada y verificada. Falta cargar las tablas y
medidas oficiales en el archivo de Power BI existente y construir las dos
páginas indicadas en [FUENTES_OFICIALES.md](powerbi/FUENTES_OFICIALES.md).

## Reproducir el ETL

Instalar dependencias y generar todos los CSV:

~~~powershell
python -m pip install -r requirements.txt
python etl/prepare_xapi.py
python etl/preparar_fuentes_oficiales.py
~~~

Para volver a descargar los tres PDF desde los sitios oficiales:

~~~powershell
python etl/preparar_fuentes_oficiales.py --descargar
~~~

Los resultados se escriben en powerbi/data. Las consultas M listas para copiar
en Power Query están en [consultas_oficiales](powerbi/consultas_oficiales/) y
las medidas están en [medidas.dax](powerbi/medidas.dax) y
[medidas_oficiales.dax](powerbi/medidas_oficiales.dax).

## Fuentes oficiales seleccionadas

- [Rendimiento académico UNAL Medellín 2015-2](https://planeacion.medellin.unal.edu.co/images/01%20Contenido%20Articulos/Estadisticas/Rendimiento%20Academico/InfRa2015-2.pdf)
- [Rendimiento académico UNAL Medellín 2017-1](https://planeacion.medellin.unal.edu.co/images/01%20Contenido%20Articulos/Estadisticas/Rendimiento%20Academico/InfRa2017-1.pdf)
- [Boletín estadístico UNAL Medellín 2010](https://planeacion.medellin.unal.edu.co/images/01%20Contenido%20Articulos/Estadisticas/Boletines/boletin2010.pdf)

Esta combinación es la más adecuada porque los informes de notas publican
promedio, inscritos, aprobados y reprobados por asignatura y periodo, mientras
el boletín publica matriculados iniciales, rezago, graduados y desertores netos
por facultad y cohorte. SNIES/SPADIES es una fuente oficial pertinente para
permanencia, pero sus bases públicas no resuelven el promedio de notas por
asignatura.

## Límites de interpretación

Los datos oficiales son históricos y agregados. No se pueden unir alumno por
alumno con las 480 observaciones de xAPI, ni sirven para atribuir causalidad
entre rendimiento y deserción. Los 63 promedios publicados como 0,00 quedan
marcados para revisión del tipo de calificación y se excluyen del campo usado
para análisis; el valor original permanece intacto.

La medida de notas muestra el promedio que publicó la universidad en cada
asignatura-periodo. No calcula un promedio global de promedios. La deserción
usa la definición neta por cohorte del boletín de 2010, no la metodología anual
vigente de SPADIES.

Más detalle sobre el modelo, las relaciones, los controles y los valores de
comprobación está en [FUENTES_OFICIALES.md](powerbi/FUENTES_OFICIALES.md).
