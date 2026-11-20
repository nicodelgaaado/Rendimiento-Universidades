param(
    [Parameter(Mandatory = $true)][string]$Server,
    [Parameter(Mandatory = $true)][string]$Database,
    [Parameter(Mandatory = $true)][string]$OutputFile
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$token = az account get-access-token --resource https://database.windows.net/ --query accessToken --output tsv
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($token)) { throw 'No Azure SQL token.' }
$connection = [System.Data.SqlClient.SqlConnection]::new()
$connection.ConnectionString = "Server=tcp:$Server,1433;Initial Catalog=$Database;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;Application Name=RendimientoDatabaseAudit"
$connection.AccessToken = $token.Trim()
$connection.Open()
try {
    $definitions = [ordered]@{
        DimensionTemas = 'IdTema'
        DimensionSemestres = 'IdSemestre'
        DimensionAsignaturasOficiales = 'CodigoAsignatura'
        DimensionPeriodosNotas = 'PeriodoAcademico'
        DimensionFacultadesOficiales = 'CodigoFacultad'
        DimensionCohortesDesercion = 'CohorteIngreso'
        DimensionFuentesOficiales = 'IdentificadorFuente'
        HechosObservaciones = 'IdObservacion'
        HechosNotasOficiales = 'CodigoAsignatura, PeriodoAcademico'
        HechosDesercionOficial = 'CodigoFacultad, CohorteIngreso'
        EDA_TemaSemestreRendimiento = 'Tema, CodigoSemestre, CategoriaRendimiento'
    }
    $result = [ordered]@{}
    foreach ($entry in $definitions.GetEnumerator()) {
        $command = $connection.CreateCommand()
        $command.CommandText = "SELECT * FROM [rendimiento].[$($entry.Key)] ORDER BY $($entry.Value)"
        $command.CommandTimeout = 120
        $reader = $command.ExecuteReader()
        $rows = [System.Collections.Generic.List[object]]::new()
        while ($reader.Read()) {
            $row = [ordered]@{}
            for ($i = 0; $i -lt $reader.FieldCount; $i++) {
                $value = $reader.GetValue($i)
                $row[$reader.GetName($i)] = if ($value -is [DBNull]) { $null } else { $value }
            }
            $rows.Add([pscustomobject]$row)
        }
        $reader.Close()
        $command.Dispose()
        $result[$entry.Key] = $rows
    }
    $meta = $connection.CreateCommand()
    $meta.CommandText = @'
SELECT
  (SELECT COUNT(*) FROM sys.tables WHERE schema_id = SCHEMA_ID(N'rendimiento')) AS tables_count,
  (SELECT COUNT(*) FROM sys.views WHERE schema_id = SCHEMA_ID(N'rendimiento')) AS views_count,
  (SELECT COUNT(*) FROM sys.key_constraints kc JOIN sys.tables t ON t.object_id=kc.parent_object_id WHERE t.schema_id=SCHEMA_ID(N'rendimiento') AND kc.type='PK') AS primary_keys,
  (SELECT COUNT(*) FROM sys.foreign_keys fk JOIN sys.tables t ON t.object_id=fk.parent_object_id WHERE t.schema_id=SCHEMA_ID(N'rendimiento')) AS foreign_keys,
  (SELECT COUNT(*) FROM sys.check_constraints cc JOIN sys.tables t ON t.object_id=cc.parent_object_id WHERE t.schema_id=SCHEMA_ID(N'rendimiento')) AS check_constraints,
  (SELECT encryption_state FROM sys.dm_database_encryption_keys WHERE database_id=DB_ID()) AS encryption_state,
  (SELECT encrypt_option FROM sys.dm_exec_connections WHERE session_id=@@SPID) AS connection_encrypted;
'@
    $reader = $meta.ExecuteReader()
    [void]$reader.Read()
    $metadata = [ordered]@{}
    for ($i = 0; $i -lt $reader.FieldCount; $i++) { $metadata[$reader.GetName($i)] = $reader.GetValue($i) }
    $reader.Close()
    $meta.Dispose()
    $result['_metadata'] = [pscustomobject]$metadata
    $result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputFile -Encoding UTF8
}
finally {
    $connection.Close()
    $connection.Dispose()
    $token = $null
}
