param(
    [Parameter(Mandatory = $true)][string]$Server,
    [Parameter(Mandatory = $true)][string]$Database,
    [Parameter(Mandatory = $true)][string]$SqlFile
)

$ErrorActionPreference = 'Stop'
$token = az account get-access-token --resource https://database.windows.net/ --query accessToken --output tsv
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($token)) {
    throw 'Could not acquire an Azure SQL Microsoft Entra token.'
}

$connection = [System.Data.SqlClient.SqlConnection]::new()
$connection.ConnectionString = "Server=tcp:$Server,1433;Initial Catalog=$Database;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;Application Name=RendimientoDatabaseDeployment"
$connection.AccessToken = $token.Trim()
$connection.Open()
try {
    $sql = Get-Content -LiteralPath $SqlFile -Raw -Encoding UTF8
    $batches = [regex]::Split($sql, '(?im)^\s*GO\s*$')
    $executed = 0
    foreach ($batch in $batches) {
        if ([string]::IsNullOrWhiteSpace($batch)) { continue }
        $command = $connection.CreateCommand()
        $command.CommandText = $batch
        $command.CommandTimeout = 300
        [void]$command.ExecuteNonQuery()
        $command.Dispose()
        $executed++
    }
    $check = $connection.CreateCommand()
    $check.CommandText = @'
SELECT
    DB_NAME() AS database_name,
    (SELECT COUNT(*) FROM sys.objects WHERE schema_id = SCHEMA_ID(N'rendimiento') AND type IN ('U', 'V')) AS object_count,
    (SELECT encrypt_option FROM sys.dm_exec_connections WHERE session_id = @@SPID) AS encrypt_option
;
'@
    $reader = $check.ExecuteReader()
    if (-not $reader.Read()) { throw 'No deployed objects found in schema rendimiento.' }
    [pscustomobject]@{
        database = $reader.GetString(0)
        objects = $reader.GetInt32(1)
        encrypted = $reader.GetString(2)
        batches = $executed
    } | ConvertTo-Json
    $reader.Close()
    $check.Dispose()
}
finally {
    $connection.Close()
    $connection.Dispose()
    $token = $null
}
