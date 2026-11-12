"""Fase 5: Evaluación rigurosa de resultados de detección de anomalías.

Calcula métricas globales de clasificación (Precisión, Recall, F1), matrices
de confusión, recall por tipo de anomalía, análisis de sensibilidad de
contaminación de Isolation Forest, falsos positivos sobre casos extremos
legítimos y análisis de errores.
"""

from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score

from src.config import (
    CANTIDADES_ANOMALIAS,
    DATA_PROCESSED_CSV,
    DATA_PROCESSED_DIR,
    DATA_RAW_CSV,
    FEATURES_IF,
    IF_CONTAMINATION,
    OUTPUTS_TAB_DIR,
    SEED,
)
from src.features import agregar_features
from src.isolation_forest import aplicar_isolation_forest
from src.rules import aplicar_reglas


def combinar_detectores(df: pd.DataFrame) -> pd.DataFrame:
    """Asigna el nivel de riesgo combinado a partir de las salidas de Reglas e Isolation Forest.

    Nivel de riesgo:
      - 'alto': Alerta de ambas técnicas O severidad de reglas 'critica' (R1 o R2).
      - 'medio': Alerta de solo una técnica (y sin severidad crítica).
      - 'bajo': Ninguna alerta generada.
    """
    df_comb = df.copy()

    cond_alto = (
        (df_comb["alerta_reglas"] & df_comb["alerta_if"])
        | (df_comb["severidad_reglas"] == "critica")
    )
    cond_medio = (
        (df_comb["alerta_reglas"] ^ df_comb["alerta_if"])
        & (~cond_alto)
    )

    condiciones = [cond_alto, cond_medio]
    etiquetas = ["alto", "medio"]
    df_comb["nivel_riesgo"] = np.select(condiciones, etiquetas, default="bajo")

    return df_comb


def evaluar_clasificador(y_true: pd.Series, y_pred: pd.Series, nombre: str) -> Dict[str, float]:
    """Calcula métricas de clasificación binaria completas."""
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    return {
        "detector": nombre,
        "mesas_alertadas": int(y_pred.sum()),
        "VP": int(tp),
        "FP": int(fp),
        "FN": int(fn),
        "VN": int(tn),
        "precision": float(prec),
        "recall": float(rec),
        "f1": float(f1),
    }


def ejecutar_evaluacion(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """Ejecuta la evaluación completa, genera todas las tablas y exporta resultados."""
    OUTPUTS_TAB_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Asegurar combinación de detectores
    df_proc = combinar_detectores(df)
    df_proc.to_csv(DATA_PROCESSED_CSV, index=False)

    y_true = df_proc["es_anomalia"]
    pred_reglas = df_proc["alerta_reglas"].astype(int)
    pred_if = df_proc["alerta_if"].astype(int)
    pred_union = (df_proc["alerta_reglas"] | df_proc["alerta_if"]).astype(int)
    pred_inter = (df_proc["alerta_reglas"] & df_proc["alerta_if"]).astype(int)

    # 2. Métricas globales de detectores
    metricas = [
        evaluar_clasificador(y_true, pred_reglas, "Reglas simples"),
        evaluar_clasificador(y_true, pred_if, "Isolation Forest"),
        evaluar_clasificador(y_true, pred_union, "Unión (Cualquiera)"),
        evaluar_clasificador(y_true, pred_inter, "Intersección (Ambas)"),
    ]
    df_metricas = pd.DataFrame(metricas)
    df_metricas.to_csv(OUTPUTS_TAB_DIR / "metricas_detectores.csv", index=False)

    # 3. Recall por tipo de anomalía
    filas_tipo = []
    for tipo in CANTIDADES_ANOMALIAS.keys():
        sub_df = df_proc[df_proc["tipo_anomalia"] == tipo]
        total_tipo = len(sub_df)
        rec_reg = sub_df["alerta_reglas"].sum() / total_tipo if total_tipo > 0 else 0.0
        rec_if_val = sub_df["alerta_if"].sum() / total_tipo if total_tipo > 0 else 0.0
        rec_un = (sub_df["alerta_reglas"] | sub_df["alerta_if"]).sum() / total_tipo if total_tipo > 0 else 0.0
        rec_in = (sub_df["alerta_reglas"] & sub_df["alerta_if"]).sum() / total_tipo if total_tipo > 0 else 0.0

        filas_tipo.append({
            "tipo_anomalia": tipo,
            "total_inyectadas": total_tipo,
            "recall_reglas": float(rec_reg),
            "recall_if": float(rec_if_val),
            "recall_union": float(rec_un),
            "recall_interseccion": float(rec_in),
        })
    df_recall_tipo = pd.DataFrame(filas_tipo)
    df_recall_tipo.to_csv(OUTPUTS_TAB_DIR / "recall_por_tipo.csv", index=False)

    # 4. Falsos positivos sobre casos extremos legítimos (40 mesas)
    extremos = df_proc[df_proc["nota_simulacion"] == "extremo_legitimo"]
    n_extremos = len(extremos)
    fp_extremos = [
        {
            "detector": "Reglas simples",
            "total_extremos": n_extremos,
            "falsos_positivos": int(extremos["alerta_reglas"].sum()),
            "tasa_fp_extremos": float(extremos["alerta_reglas"].mean()),
        },
        {
            "detector": "Isolation Forest",
            "total_extremos": n_extremos,
            "falsos_positivos": int(extremos["alerta_if"].sum()),
            "tasa_fp_extremos": float(extremos["alerta_if"].mean()),
        },
        {
            "detector": "Unión (Cualquiera)",
            "total_extremos": n_extremos,
            "falsos_positivos": int((extremos["alerta_reglas"] | extremos["alerta_if"]).sum()),
            "tasa_fp_extremos": float((extremos["alerta_reglas"] | extremos["alerta_if"]).mean()),
        },
        {
            "detector": "Intersección (Ambas)",
            "total_extremos": n_extremos,
            "falsos_positivos": int((extremos["alerta_reglas"] & extremos["alerta_if"]).sum()),
            "tasa_fp_extremos": float((extremos["alerta_reglas"] & extremos["alerta_if"]).mean()),
        },
    ]
    df_fp_extremos = pd.DataFrame(fp_extremos)
    df_fp_extremos.to_csv(OUTPUTS_TAB_DIR / "falsos_positivos_extremos.csv", index=False)

    # 5. Análisis de sensibilidad a la contaminación en Isolation Forest
    niveles_contaminacion = [0.02, 0.04, 0.06, 0.08]
    filas_sens = []
    for c in niveles_contaminacion:
        df_sens, _, _ = aplicar_isolation_forest(df_proc, contamination=c, seed=SEED)
        res_c = evaluar_clasificador(y_true, df_sens["alerta_if"].astype(int), f"IF_cont_{c:.2f}")
        res_c["contamination"] = c
        filas_sens.append(res_c)
    df_sensibilidad = pd.DataFrame(filas_sens)
    df_sensibilidad.to_csv(OUTPUTS_TAB_DIR / "sensibilidad_contaminacion.csv", index=False)

    # 6. Top 15 mesas más sospechosas
    # Ordenar por: nivel_riesgo (alto > medio > bajo), luego puntaje_reglas desc, luego score_if desc
    orden_riesgo = {"alto": 3, "medio": 2, "bajo": 1}
    df_proc["_peso_riesgo"] = df_proc["nivel_riesgo"].map(orden_riesgo)

    cols_top = [
        "mesa_id", "departamento", "municipio", "zona",
        "total_votos_reportado", "votantes_habilitados", "participacion",
        "diferencia_aritmetica", "pct_max_candidato", "pct_nulos", "frac_multiplos_10",
        "nivel_riesgo", "severidad_reglas", "puntaje_reglas", "score_if",
        "alerta_reglas", "alerta_if", "es_anomalia", "tipo_anomalia"
    ]
    top_15 = (
        df_proc.sort_values(
            by=["_peso_riesgo", "puntaje_reglas", "score_if"],
            ascending=[False, False, False]
        )
        .head(15)[cols_top]
        .copy()
    )
    top_15.insert(0, "ranking", range(1, 16))
    top_15.to_csv(OUTPUTS_TAB_DIR / "top_mesas_sospechosas.csv", index=False)
    df_proc = df_proc.drop(columns=["_peso_riesgo"])

    # 7. Agregado geográfico: tasa de mesas de riesgo alto por municipio
    riesgo_muni = df_proc.groupby("municipio").agg(
        departamento=("departamento", "first"),
        total_mesas=("mesa_id", "count"),
        mesas_riesgo_alto=("nivel_riesgo", lambda s: (s == "alto").sum()),
    ).reset_index()
    riesgo_muni["pct_riesgo_alto"] = (
        riesgo_muni["mesas_riesgo_alto"] / riesgo_muni["total_mesas"]
    ) * 100.0
    riesgo_muni = riesgo_muni.sort_values(by="pct_riesgo_alto", ascending=False)
    riesgo_muni.to_csv(OUTPUTS_TAB_DIR / "riesgo_por_municipio.csv", index=False)

    # 8. Impresión de resumen y análisis de errores representativos
    print("=================================================================")
    print("EVALUACIÓN DE DETECTORES (GROUND TRUTH)")
    print("=================================================================")
    print(df_metricas[["detector", "mesas_alertadas", "VP", "FP", "precision", "recall", "f1"]].to_string(index=False))
    print("\nRecall por tipo de anomalía:")
    print(df_recall_tipo[["tipo_anomalia", "recall_reglas", "recall_if", "recall_union"]].to_string(index=False))
    print("\nFalsos positivos en casos extremos legítimos (40 mesas):")
    print(df_fp_extremos[["detector", "falsos_positivos", "tasa_fp_extremos"]].to_string(index=False))
    print("\nTop 5 municipios con mayor tasa de actas con riesgo alto:")
    print(riesgo_muni.head(5)[["municipio", "departamento", "total_mesas", "mesas_riesgo_alto", "pct_riesgo_alto"]].to_string(index=False))
    print("=================================================================")

    return df_proc, {
        "metricas": df_metricas,
        "recall_tipo": df_recall_tipo,
        "fp_extremos": df_fp_extremos,
        "sensibilidad": df_sensibilidad,
        "top_15": top_15,
        "riesgo_muni": riesgo_muni,
    }


if __name__ == "__main__":
    from src.features import agregar_features
    from src.generate_dataset import generar_dataset

    df_base = pd.read_csv(DATA_PROCESSED_CSV) if DATA_PROCESSED_CSV.exists() else None
    if df_base is None or "alerta_if" not in df_base.columns:
        df_raw = pd.read_csv(DATA_RAW_CSV) if DATA_RAW_CSV.exists() else generar_dataset()
        df_f = agregar_features(df_raw)
        df_r = aplicar_reglas(df_f)
        df_proc, _, _ = aplicar_isolation_forest(df_r)
    else:
        df_proc = df_base

    ejecutar_evaluacion(df_proc)
