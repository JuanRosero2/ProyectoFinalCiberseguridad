"""Construye en memoria el Excel de resultados que se descarga desde la interfaz."""

from datetime import datetime
from io import BytesIO

import pandas as pd

from src.config import (
    IF_N_ESTIMATORS,
    SEED,
    UMBRAL_R3_PARTICIPACION,
    UMBRAL_R4_MIN_VOTOS_VALIDOS,
    UMBRAL_R4_PCT_MAX,
    UMBRAL_R5_PCT_NULOS,
)
from src.evaluate import COLUMNAS_TOP_MESAS


def construir_excel(res, riesgo_muni: pd.DataFrame) -> bytes:
    """Devuelve los bytes de un .xlsx con resultados, priorización, riesgo municipal, métricas y parámetros."""
    parametros = pd.DataFrame([
        ("Fecha de generación", datetime.now().strftime("%Y-%m-%d %H:%M")),
        ("Semilla", SEED),
        ("Isolation Forest · contamination", res.contamination),
        ("Isolation Forest · n_estimators", IF_N_ESTIMATORS),
        ("Isolation Forest · umbral de score", round(res.umbral_if, 4)),
        ("R3 · participación mínima", UMBRAL_R3_PARTICIPACION),
        ("R4 · % mínimo del candidato más votado", UMBRAL_R4_PCT_MAX),
        ("R4 · votos válidos mínimos", UMBRAL_R4_MIN_VOTOS_VALIDOS),
        ("R5 · % mínimo de nulos", UMBRAL_R5_PCT_NULOS),
        ("Aviso", "Datos simulados. Una alerta indica una inconsistencia que merece revisión, no una prueba de fraude."),
    ], columns=["parametro", "valor"])

    cols_prior = ["prioridad", *COLUMNAS_TOP_MESAS, "reglas_activadas"]
    priorizadas = res.df[res.df["nivel_riesgo"] != "bajo"][cols_prior]

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        res.df.to_excel(writer, sheet_name="resultados_mesas", index=False)
        priorizadas.to_excel(writer, sheet_name="mesas_priorizadas", index=False)
        riesgo_muni.to_excel(writer, sheet_name="riesgo_municipio", index=False)
        if res.evaluacion is not None:
            res.evaluacion["metricas"].to_excel(writer, sheet_name="metricas", index=False)
            res.evaluacion["recall_tipo"].to_excel(writer, sheet_name="recall_por_tipo", index=False)
        parametros.to_excel(writer, sheet_name="parametros", index=False)
    return buffer.getvalue()
