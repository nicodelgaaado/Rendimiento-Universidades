# Consultas para Power Query

Crear primero un parámetro de texto llamado RutaDatosOficiales y pegar el
contenido de 00_RutaDatosOficiales.pq. Después crear una consulta en blanco
llamada FuncionLeerCsvOficial y pegar 01_FuncionLeerCsvOficial.pq.

Crear las siete consultas restantes con el mismo nombre del archivo .pq.
La función convierte las celdas vacías en null y aplica los tipos con cultura
en-US, porque los CSV usan punto decimal aunque Power BI esté en español.

Las consultas auxiliares RutaDatosOficiales y FuncionLeerCsvOficial deben
tener deshabilitada la opción **Habilitar carga**.
