# Paquete de bases de datos

Este directorio contiene versiones portables y reproducibles de los datos del
proyecto. Permite explorar la información localmente con SQLite y desplegar el
mismo modelo en PostgreSQL o Azure SQL Database.

## Artefactos incluidos

| Archivo | Propósito |
| --- | --- |
| `rendimiento.sqlite3` | Base SQLite poblada para DB Browser for SQLite. |
| `postgresql.sql` | Esquema e importación de datos transaccional para PostgreSQL. |
| `azure_sql.sql` | Esquema e importación de datos transaccional para Azure SQL. |
| `build_database.py` | Regenera SQLite y los artefactos PostgreSQL desde `powerbi/data`. |
| `build_azure_sql.py` | Regenera la importación de Azure SQL desde `powerbi/data`. |
| `fact_check.py` | Audita datos, relaciones y restricciones de SQLite/PostgreSQL. |
| `verify_azure_sql.py` | Compara campo por campo una exportación de Azure SQL con los CSV. |
| `invoke_azure_sql.ps1` | Ejecuta un archivo T-SQL con un token temporal de Microsoft Entra. |
| `export_azure_sql.ps1` | Exporta los datos de Azure SQL para verificarlos independientemente. |
| `azure_sql_constraint_probes.sql` | Prueba once mutaciones inválidas dentro de transacciones revertidas. |
| `consultas_azure_sql.md` | Consultas de análisis listas para usar, con explicaciones. |

Los archivos SQL generados y la base SQLite contienen únicamente los datos
educativos públicos que ya están en el repositorio. Aquí no se almacenan
contraseñas, tokens de acceso, identificadores de tenant o suscripción,
direcciones IP de clientes ni claves privadas.

## Descargar y explorar SQLite

Descarga la base completa desde GitHub:

[Descargar `rendimiento.sqlite3`](rendimiento.sqlite3?raw=1)

Después, abre el archivo con [DB Browser for SQLite](https://sqlitebrowser.org/)
y selecciona la pestaña **Browse Data** para visualizar las tablas y sus
registros. También puedes ejecutar esta consulta desde **Execute SQL**:

```sql
SELECT * FROM HechosNotasOficiales LIMIT 100;
```

## Regeneración local

Desde la raíz del repositorio:

```powershell
python database/build_database.py
python database/build_azure_sql.py
```

Los dos generadores utilizan únicamente la biblioteca estándar de Python.
`build_database.py` valida cada campo durante la carga de SQLite, comprueba la
integridad y las claves foráneas, reproduce la vista EDA y verifica los totales
publicados de notas y deserción.

## Importación en PostgreSQL

Importa el modelo en una base o esquema nuevo:

```powershell
psql -X --set=ON_ERROR_STOP=on --file=database/postgresql.sql
psql -X --set=ON_ERROR_STOP=on --file=database/verify.sql
```

La importación crea el esquema `rendimiento` y no contiene instrucciones `DROP`
ni `DELETE`. Usa variables de entorno o un gestor de secretos para manejar las
credenciales.

## Despliegue y verificación en Azure SQL

Aprovisiona Azure SQL Database con autenticación de Microsoft Entra y una regla
de firewall restringida al cliente de despliegue. Después ejecuta:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File database/invoke_azure_sql.ps1 `
  -Server '<server>.database.windows.net' `
  -Database '<database>' `
  -SqlFile database/azure_sql.sql
```

Exporta y verifica los datos remotos:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File database/export_azure_sql.ps1 `
  -Server '<server>.database.windows.net' `
  -Database '<database>' `
  -OutputFile database/azure_sql_export.json

python database/verify_azure_sql.py
```

Los scripts solicitan tokens de corta duración mediante Azure CLI y nunca los
guardan. El archivo de exportación, los certificados, los registros y los
clústeres temporales de PostgreSQL están ignorados por Git. Los archivos
`azure_sql_diagnostic_*.json` sirven como cargas de configuración de diagnóstico
para Azure Monitor. Ejecuta `azure_sql_constraint_probes.sql` mediante
`invoke_azure_sql.ps1` para confirmar que las claves, los valores obligatorios,
los rangos y las relaciones entre tablas rechazan datos inválidos.

## Modelo de datos

El paquete contiene siete tablas de dimensiones, tres tablas de hechos y una
vista EDA:

- `HechosObservaciones`: 480 observaciones xAPI.
- `HechosNotasOficiales`: 1.977 registros oficiales de asignatura-periodo.
- `HechosDesercionOficial`: 10 registros de facultad-cohorte.
- `EDA_TemaSemestreRendimiento`: vista agregada de las observaciones xAPI.

Las poblaciones xAPI y oficial de la UNAL permanecen separadas porque describen
poblaciones y niveles de detalle diferentes. Los identificadores de observación
representan filas de origen, no estudiantes. Las 63 notas publicadas como cero
se conservan en el campo original y se representan como `NULL` en el campo de
análisis.
