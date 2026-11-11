// Crear como consulta llamada FuncionLeerCsvOficial.
(rutaArchivo as text, tipos as list) as table =>
let
    Origen = Csv.Document(
        File.Contents(rutaArchivo),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),
    VaciasANulo = Table.ReplaceValue(
        Encabezados,
        "",
        null,
        Replacer.ReplaceValue,
        Table.ColumnNames(Encabezados)
    ),
    Tipos = Table.TransformColumnTypes(VaciasANulo, tipos, "en-US")
in
    Tipos
