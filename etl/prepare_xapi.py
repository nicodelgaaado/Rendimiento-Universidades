"""Prepare the xAPI education observations for Power BI without inventing students or grades.

Run: python etl/prepare_xapi.py
"""

from pathlib import Path
import json

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "dataset" / "xAPI-Edu-Data.csv"
OUT = ROOT / "powerbi" / "data"

RENAME = {
    "gender": "Gender",
    "NationalITy": "Nationality",
    "PlaceofBirth": "PlaceOfBirth",
    "StageID": "Stage",
    "GradeID": "SchoolGrade",
    "SectionID": "Section",
    "Topic": "Topic",
    "Semester": "SemesterCode",
    "Relation": "ParentRelation",
    "raisedhands": "RaisedHands",
    "VisITedResources": "VisitedResources",
    "AnnouncementsView": "AnnouncementsViewed",
    "Discussion": "DiscussionParticipation",
    "ParentAnsweringSurvey": "ParentAnsweredSurvey",
    "ParentschoolSatisfaction": "ParentSchoolSatisfaction",
    "StudentAbsenceDays": "AbsenceBand",
    "Class": "PerformanceClass",
}
NUMERIC = ["RaisedHands", "VisitedResources", "AnnouncementsViewed", "DiscussionParticipation"]

# Solo cambia los encabezados exportados; conserva todos los valores.
OUTPUT_COLUMNS = {
    "ObservationID": "IdObservacion",
    "Gender": "Genero",
    "Nationality": "Nacionalidad",
    "PlaceOfBirth": "LugarNacimiento",
    "Stage": "NivelEducativo",
    "SchoolGrade": "GradoEscolar",
    "Section": "Seccion",
    "ParentRelation": "ParentescoResponsable",
    "RaisedHands": "VecesManoLevantada",
    "VisitedResources": "RecursosVisitados",
    "AnnouncementsViewed": "AnunciosVistos",
    "DiscussionParticipation": "ParticipacionesDiscusion",
    "ParentAnsweredSurvey": "ResponsableRespondioEncuesta",
    "ParentSchoolSatisfaction": "SatisfaccionEscolarResponsable",
    "AbsenceBand": "CategoriaAusencias",
    "PerformanceClass": "CategoriaRendimiento",
    "TopicID": "IdTema",
    "Topic": "Tema",
    "SemesterKey": "IdSemestre",
    "SemesterCode": "CodigoSemestre",
    "SemesterLabel": "NombreSemestre",
    "Observations": "Observaciones",
}


def main() -> None:
    raw = pd.read_csv(SOURCE, dtype="string")
    if set(raw.columns) != set(RENAME):
        raise ValueError("Source columns changed; review the mapping before loading.")
    frame = raw.rename(columns=RENAME).copy()
    frame = frame[list(RENAME.values())]
    for col in frame.columns:
        frame[col] = frame[col].str.strip()
    if frame.isna().any().any() or frame.eq("").any().any():
        raise ValueError("Missing or empty source values need manual review.")
    for col in NUMERIC:
        values = pd.to_numeric(frame[col], errors="raise")
        if not values.mod(1).eq(0).all():
            raise ValueError(f"Non-integer activity count in {col}.")
        frame[col] = values.astype("int64")
        if not frame[col].between(0, 100).all():
            raise ValueError(f"Unexpected range in {col}.")
    expected = {
        "Gender": {"M", "F"},
        "SemesterCode": {"F", "S"},
        "PerformanceClass": {"L", "M", "H"},
        "AbsenceBand": {"Under-7", "Above-7"},
    }
    for col, allowed in expected.items():
        if not set(frame[col].unique()) <= allowed:
            raise ValueError(f"Unexpected category in {col}.")

    # Source rows have no student ID. Preserve even identical rows; they could be
    # distinct people. ObservationID identifies a row only, not a student.
    frame.insert(0, "ObservationID", range(1, len(frame) + 1))
    topics = pd.DataFrame({"Topic": sorted(frame["Topic"].unique())})
    topics.insert(0, "TopicID", range(1, len(topics) + 1))
    semesters = pd.DataFrame(
        {"SemesterCode": ["F", "S"], "SemesterLabel": ["First", "Second"], "SemesterSort": [1, 2]}
    )
    fact = frame.merge(topics, on="Topic", validate="many_to_one")
    fact = fact.drop(columns=["Topic"]).merge(
        semesters[["SemesterCode", "SemesterSort"]], on="SemesterCode", validate="many_to_one"
    )
    fact = fact.drop(columns=["SemesterCode"]).rename(columns={"SemesterSort": "SemesterKey"})
    semesters = semesters.rename(columns={"SemesterSort": "SemesterKey"})

    OUT.mkdir(parents=True, exist_ok=True)
    fact.rename(columns=OUTPUT_COLUMNS).to_csv(OUT / "HechosObservaciones.csv", index=False, encoding="utf-8-sig")
    topics.rename(columns=OUTPUT_COLUMNS).to_csv(OUT / "DimensionTemas.csv", index=False, encoding="utf-8-sig")
    semesters.rename(columns=OUTPUT_COLUMNS).to_csv(OUT / "DimensionSemestres.csv", index=False, encoding="utf-8-sig")

    counts = frame.groupby(["Topic", "SemesterCode", "PerformanceClass"]).size().reset_index(name="Observations")
    counts.rename(columns=OUTPUT_COLUMNS).to_csv(OUT / "EDA_TemaSemestreRendimiento.csv", index=False, encoding="utf-8-sig")
    summary = {
        "source_rows": len(raw),
        "output_observations": len(fact),
        "exact_duplicate_source_rows_preserved": int(raw.duplicated().sum()),
        "missing_cells": int(raw.isna().sum().sum()),
        "topic_count": len(topics),
        "semester_counts": frame["SemesterCode"].value_counts().sort_index().to_dict(),
        "performance_class_counts": frame["PerformanceClass"].value_counts().sort_index().to_dict(),
        "overall_low_class_rate": round(float(frame["PerformanceClass"].eq("L").mean()), 6),
        "mean_activity": {col: round(float(frame[col].mean()), 4) for col in NUMERIC},
        "unavailable_for_requirements": ["numeric_grade", "student_id", "faculty", "enrollment_status", "academic_year"],
    }
    (OUT / "EDA_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
