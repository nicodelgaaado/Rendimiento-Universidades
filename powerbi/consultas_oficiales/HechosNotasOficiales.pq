FuncionLeerCsvOficial(
    RutaDatosOficiales & "\HechosNotasOficiales.csv",
    {
        {"CodigoAsignatura", type text},
        {"AsignaturaPublicada", type text},
        {"EscuelaPublicada", type text},
        {"PeriodoAcademico", type text},
        {"Inscritos", Int64.Type},
        {"PromedioNotaPublicado", type number},
        {"PromedioNotaParaAnalisis", type number},
        {"EstadoPromedio", type text},
        {"DesviacionNotaPublicada", type number},
        {"Aprobados", Int64.Type},
        {"Reprobados", Int64.Type},
        {"PorcentajeReprobacionPublicado", type number},
        {"Repitentes", Int64.Type},
        {"PorcentajeRepitenciaPublicado", type number},
        {"Institucion", type text},
        {"Sede", type text},
        {"IdentificadorFuente", type text},
        {"PaginaArchivoFuente", Int64.Type},
        {"TablaFuente", Int64.Type}
    }
)
