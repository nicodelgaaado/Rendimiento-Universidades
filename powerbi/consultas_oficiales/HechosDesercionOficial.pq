FuncionLeerCsvOficial(
    RutaDatosOficiales & "\HechosDesercionOficial.csv",
    {
        {"CodigoFacultad", type text},
        {"FacultadPublicada", type text},
        {"CohorteIngreso", type text},
        {"PeriodoSeguimiento", type text},
        {"MatriculadosIniciales", Int64.Type},
        {"MatriculadosSeguimiento", Int64.Type},
        {"ReservasCupo", Int64.Type},
        {"Graduados", Int64.Type},
        {"GraduadosMatriculados", Int64.Type},
        {"DesertoresNetos", Int64.Type},
        {"PorcentajeDesercionPublicado", type number},
        {"TransferenciasSalida", Int64.Type},
        {"TransferenciasEntrada", Int64.Type},
        {"Institucion", type text},
        {"Sede", type text},
        {"Metodologia", type text},
        {"IdentificadorFuente", type text},
        {"PaginaArchivoFuente", Int64.Type},
        {"PaginaImpresaFuente", Int64.Type},
        {"TablaFuente", Int64.Type}
    }
)
