"""Extrae tablas publicadas por UNAL Medellin; no genera microdatos de alumnos.

python etl/preparar_fuentes_oficiales.py
python etl/preparar_fuentes_oficiales.py --descargar
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import urllib.request

import pandas as pd
from pypdf import PdfReader

RAIZ = Path(__file__).resolve().parents[1]
ORIGEN = RAIZ / "dataset" / "fuentes_oficiales"
SALIDA = RAIZ / "powerbi" / "data"
FUENTES = {
    "notas_2015_2": {
        "archivo": "InfRa2015-2.pdf",
        "url": "https://planeacion.medellin.unal.edu.co/images/01%20Contenido%20Articulos/Estadisticas/Rendimiento%20Academico/InfRa2015-2.pdf",
        "periodo": "2015-2", "filas": 990,
        "totales": [49607, 41499, 8108],
    },
    "notas_2017_1": {
        "archivo": "InfRa2017-1.pdf",
        "url": "https://planeacion.medellin.unal.edu.co/images/01%20Contenido%20Articulos/Estadisticas/Rendimiento%20Academico/InfRa2017-1.pdf",
        "periodo": "2017-1", "filas": 987,
        "totales": [49006, 41524, 7482],
    },
    "desercion_2010": {
        "archivo": "Boletin2010.pdf",
        "url": "https://planeacion.medellin.unal.edu.co/images/01%20Contenido%20Articulos/Estadisticas/Boletines/boletin2010.pdf",
    },
}


def exigir(condicion, mensaje):
    if not condicion:
        raise ValueError(mensaje)


def decimal(texto):
    return float(texto.replace(",", "."))


def extraer_notas(clave, fuente):
    lector = PdfReader(ORIGEN / fuente["archivo"])
    exigir("Tabla 19" in lector.pages[23].extract_text(), "Cambio de estructura de notas")
    filas = []
    for indice in range(23, len(lector.pages)):
        partes = []
        lector.pages[indice].extract_text(
            visitor_text=lambda texto, *_: partes.append(texto.strip()) if texto.strip() else None
        )
        posiciones = [i for i, t in enumerate(partes) if re.fullmatch(r"\d{7,8}", t)]
        usados = set()
        for i in posiciones:
            registro = [partes[i - 1]] + partes[i:i + 10]
            exigir(len(registro) == 11, f"Fila incompleta: {clave}, pagina {indice + 1}")
            exigir(all(re.fullmatch(r"\d+(?:,\d+)?", t) for t in registro[3:]), f"Numero invalido: {registro}")
            nombre, codigo, escuela = registro[:3]
            inscritos, promedio, desviacion, aprobados, reprobados, tasa, repitentes, repeticion = map(decimal, registro[3:])
            exigir(inscritos == aprobados + reprobados, f"Conteos inconsistentes: {codigo}")
            exigir(0 <= promedio <= 5 and inscritos > 0, f"Rango invalido: {codigo}")
            exigir(abs(tasa - reprobados / inscritos * 100) <= 0.051, f"Tasa inconsistente: {codigo}")
            exigir(abs(repeticion - repitentes / inscritos * 100) <= 0.051, f"Repitencia inconsistente: {codigo}")
            # Los ceros publicados se preservan. Sin tipo de calificacion,
            # no se presentan como ceros reales ni se imputan otras notas.
            filas.append({
                "CodigoAsignatura": codigo, "AsignaturaPublicada": nombre,
                "EscuelaPublicada": escuela, "PeriodoAcademico": fuente["periodo"],
                "Inscritos": int(inscritos), "PromedioNotaPublicado": promedio,
                "PromedioNotaParaAnalisis": promedio if promedio > 0 else None,
                "EstadoPromedio": "Disponible" if promedio > 0 else "Cero publicado: revisar tipo de calificacion",
                "DesviacionNotaPublicada": desviacion, "Aprobados": int(aprobados),
                "Reprobados": int(reprobados), "PorcentajeReprobacionPublicado": tasa,
                "Repitentes": int(repitentes), "PorcentajeRepitenciaPublicado": repeticion,
                "Institucion": "Universidad Nacional de Colombia", "Sede": "Medellín",
                "IdentificadorFuente": clave, "PaginaArchivoFuente": indice + 1,
                "TablaFuente": 19,
            })
            usados.update(range(i - 1, i + 10))
        # Despues del encabezado inicial toda celda debe formar parte de una fila.
        sobrantes = [t for i, t in enumerate(partes) if i not in usados and not (indice == 23 and i < 23)]
        exigir(not sobrantes, f"Celdas sin extraer en {clave}, pagina {indice + 1}: {sobrantes}")
    datos = pd.DataFrame(filas)
    exigir(len(datos) == fuente["filas"], f"Cantidad inesperada de asignaturas: {clave}")
    exigir(datos.CodigoAsignatura.is_unique, f"Asignaturas repetidas: {clave}")
    exigir(datos[["Inscritos", "Aprobados", "Reprobados"]].sum().tolist() == fuente["totales"], f"Totales no coinciden con tabla 1: {clave}")
    return datos


def extraer_desercion():
    lector = PdfReader(ORIGEN / FUENTES["desercion_2010"]["archivo"])
    filas = []
    comprobaciones = []
    # Totales de facultad publicados; no sumar las filas de programas y sus subtotales.
    facultades = ["Arquitectura", "Ciencias", "Ciencias Agropecuarias", "Ciencias Humanas y E.", "Minas"]
    for pagina, cohorte, corte, tabla, esperado in [(25, "2005-2", "2010-1", 12, (1295, 653)), (26, "2006-1", "2010-2", 13, (1404, 586))]:
        texto = lector.pages[pagina].extract_text()
        exigir(f"Tabla {tabla}" in texto and cohorte in texto, "Cambio de estructura de desercion")
        totales = {}
        for linea in texto.splitlines():
            if not linea.startswith("Total "):
                continue
            m = re.match(r"Total\s+(.+?)\s+(\d.*)$", linea.strip())
            if not m:
                continue
            nombre, cadena = m.groups()
            valores = cadena.split()
            exigir(len(valores) == 10, f"Fila de facultad incompleta: {linea}")
            numeros = list(map(decimal, valores))
            iniciales, matriculados, reserva, graduados, graduados_matriculados, desertores, tasa, transfiere, recibe, tasa_transferencia = numeros
            exigir(desertores == iniciales - matriculados - reserva - (graduados - graduados_matriculados), f"Formula de desercion no concilia: {nombre}")
            exigir(abs(tasa - 100 * desertores / iniciales) <= 0.051, f"Tasa publicada no concilia: {nombre}")
            totales[nombre] = numeros
            if nombre == "general":
                continue
            exigir(nombre in facultades, f"Facultad desconocida: {nombre}")
            filas.append({
                "CodigoFacultad": f"MED-{facultades.index(nombre) + 1:02d}",
                "FacultadPublicada": nombre, "CohorteIngreso": cohorte,
                "PeriodoSeguimiento": corte, "MatriculadosIniciales": int(iniciales),
                "MatriculadosSeguimiento": int(matriculados), "ReservasCupo": int(reserva),
                "Graduados": int(graduados), "GraduadosMatriculados": int(graduados_matriculados),
                "DesertoresNetos": int(desertores), "PorcentajeDesercionPublicado": tasa,
                "TransferenciasSalida": int(transfiere), "TransferenciasEntrada": int(recibe),
                "Institucion": "Universidad Nacional de Colombia", "Sede": "Medellín",
                "Metodologia": "Desercion neta por cohorte, boletin institucional 2010",
                "IdentificadorFuente": "desercion_2010", "PaginaArchivoFuente": pagina + 1,
                "PaginaImpresaFuente": pagina, "TablaFuente": tabla,
            })
        exigir(set(totales) == set(facultades) | {"general"}, f"Faltan facultades: {cohorte}")
        for columna in [0, 1, 2, 3, 4, 5, 7, 8]:
            exigir(sum(totales[f][columna] for f in facultades) == totales["general"][columna], f"Total no concilia: {cohorte}")
        exigir((int(totales["general"][0]), int(totales["general"][5])) == esperado, "Cambio de totales de cohorte")
        comprobaciones.append({"cohorte": cohorte, "corte": corte, "matriculados_iniciales": esperado[0], "desertores": esperado[1], "tasa_calculada": esperado[1] / esperado[0]})
    return pd.DataFrame(filas), comprobaciones


def guardar(datos, nombre):
    datos.to_csv(SALIDA / f"{nombre}.csv", index=False, encoding="utf-8-sig", float_format="%.6f")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--descargar", action="store_true", help="Descargar los PDF oficiales antes de extraer")
    args = parser.parse_args()
    ORIGEN.mkdir(parents=True, exist_ok=True)
    SALIDA.mkdir(parents=True, exist_ok=True)
    if args.descargar:
        for fuente in FUENTES.values():
            with urllib.request.urlopen(fuente["url"], timeout=60) as respuesta:
                contenido = respuesta.read()
            exigir(contenido.startswith(b"%PDF"), "La fuente no entrego un PDF")
            (ORIGEN / fuente["archivo"]).write_bytes(contenido)
    fuentes = []
    for clave, fuente in FUENTES.items():
        archivo = ORIGEN / fuente["archivo"]
        exigir(archivo.exists(), f"Falta {archivo.name}; ejecutar con --descargar")
        fuentes.append({"IdentificadorFuente": clave, "ArchivoFuente": fuente["archivo"], "DireccionFuente": fuente["url"], "HuellaSHA256": hashlib.sha256(archivo.read_bytes()).hexdigest()})
    notas = pd.concat([extraer_notas(k, f) for k, f in FUENTES.items() if k.startswith("notas_")], ignore_index=True)
    desercion, conciliacion = extraer_desercion()
    asignaturas = notas.sort_values("PeriodoAcademico").drop_duplicates("CodigoAsignatura", keep="last")[["CodigoAsignatura", "AsignaturaPublicada"]].rename(columns={"AsignaturaPublicada": "Asignatura"}).sort_values("CodigoAsignatura")
    periodos = pd.DataFrame({"PeriodoAcademico": sorted(notas.PeriodoAcademico.unique())})
    periodos["AnioAcademico"] = periodos.PeriodoAcademico.str[:4].astype(int)
    periodos["Semestre"] = periodos.PeriodoAcademico.str[-1].astype(int)
    facultades = desercion[["CodigoFacultad", "FacultadPublicada"]].drop_duplicates().rename(columns={"FacultadPublicada": "Facultad"})
    facultades["Facultad"] = facultades.Facultad.replace({"Ciencias Humanas y E.": "Ciencias Humanas y Económicas"})
    cohortes = desercion[["CohorteIngreso", "PeriodoSeguimiento"]].drop_duplicates()
    for datos, nombre in [(notas, "HechosNotasOficiales"), (desercion, "HechosDesercionOficial"), (asignaturas, "DimensionAsignaturasOficiales"), (periodos, "DimensionPeriodosNotas"), (facultades, "DimensionFacultadesOficiales"), (cohortes, "DimensionCohortesDesercion"), (pd.DataFrame(fuentes), "DimensionFuentesOficiales")]:
        guardar(datos, nombre)
    resumen = {
        "filas_notas": len(notas), "asignaturas_distintas": len(asignaturas),
        "periodos_notas": periodos.PeriodoAcademico.tolist(),
        "promedios_cero_pendientes_de_validacion": int(notas.PromedioNotaParaAnalisis.isna().sum()),
        "filas_desercion_facultad_cohorte": len(desercion),
        "cohortes_verificadas": conciliacion,
        "totales_notas": notas.groupby("PeriodoAcademico")[["Inscritos", "Aprobados", "Reprobados"]].sum().reset_index().to_dict(orient="records"),
        "fuentes": fuentes,
        "alcance": "Estadisticas historicas agregadas de UNAL Medellin; sin enlace individual con xAPI. No son microdatos ni indicadores actuales.",
    }
    (SALIDA / "VerificacionFuentesOficiales.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in resumen.items() if k != "fuentes"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
