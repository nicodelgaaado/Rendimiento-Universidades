# Fuentes oficiales preservadas

Este directorio conserva únicamente los tres PDF usados por el ETL:

- InfRa2015-2.pdf: promedios por asignatura del periodo 2015-2.
- InfRa2017-1.pdf: promedios por asignatura del periodo 2017-1.
- Boletin2010.pdf: deserción neta por facultad de las cohortes 2005-2 y 2006-1.

Las URL, las huellas SHA-256 y la trazabilidad de cada fila quedan registradas
en powerbi/data/DimensionFuentesOficiales.csv. Para volver a descargarlos:

~~~powershell
python etl/preparar_fuentes_oficiales.py --descargar
~~~
