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
    NIVELES_CONTAMINACION_SENSIBILIDAD,
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


ORDEN_RIESGO: Dict[str, int] = {"alto": 3, "medio": 2, "bajo": 1}

COLUMNAS_TOP_MESAS: List[str] = [
    "mesa_id", "departamento", "municipio", "zona",
    "total_votos_reportado", "votantes_habilitados", "participacion",
    "diferencia_aritmetica", "pct_max_candidato", "pct_nulos", "frac_multiplos_10",
    "nivel_riesgo", "severidad_reglas", "puntaje_reglas", "score_if",
    "alerta_reglas", "alerta_if",
]
COLUMNAS_ETIQUETA: List[str] = ["es_anomalia", "tipo_anomalia"]


def ordenar_por_prioridad(df: pd.DataFrame) -> pd.DataFrame:
    """Ordena las mesas por nivel de riesgo, luego puntaje de reglas y luego score IF (desc)."""
    df_ord = df.copy()
    df_ord["_peso_riesgo"] = df_ord["nivel_riesgo"].map(ORDEN_RIESGO)
    df_ord = df_ord.sort_values(
        by=["_peso_riesgo", "puntaje_reglas", "score_if"],
        ascending=[False, False, False],
    )
    return df_ord.drop(columns=["_peso_riesgo"])


def calcular_top_mesas(df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    """Top-n de mesas más sospechosas. No requiere etiquetas (las incluye solo si existen)."""
    cols = COLUMNAS_TOP_MESAS + [c for c in COLUMNAS_ETIQUETA if c in df.columns]
    top = ordenar_por_prioridad(df).head(n)[cols].copy()
    top.insert(0, "ranking", range(1, len(top) + 1))
    return top


def calcular_riesgo_por_municipio(df: pd.DataFrame, min_mesas: int = 0) -> pd.DataFrame:
    """Cantidad y porcentaje de mesas en riesgo alto por municipio. No requiere etiquetas.

    `min_mesas` excluye municipios con pocas mesas, cuyo porcentaje se infla con pocas alertas.
    """
    riesgo_muni = df.groupby("municipio").agg(
        departamento=("departamento", "first"),
        total_mesas=("mesa_id", "count"),
        mesas_riesgo_alto=("nivel_riesgo", lambda s: (s == "alto").sum()),
    ).reset_index()
    riesgo_muni["pct_riesgo_alto"] = (
        riesgo_muni["mesas_riesgo_alto"] / riesgo_muni["total_mesas"]
    ) * 100.0
    riesgo_muni = riesgo_muni.sort_values(by="pct_riesgo_alto", ascending=False)
    if min_mesas > 0:
        riesgo_muni = riesgo_muni[riesgo_muni["total_mesas"] >= min_mesas]
    return riesgo_muni


def calcular_evaluacion(df_proc: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Calcula todas las tablas de evaluación contra el ground truth, sin escribir en disco.

    Requiere las columnas 'es_anomalia', 'tipo_anomalia' y 'nota_simulacion'. Estas columnas
    solo se usan aquí, para medir; nunca como entrada de los detectores.
    """
    y_true = df_proc["es_anomalia"].astype(int)
    pred_reglas = df_proc["alerta_reglas"].astype(int)
    pred_if = df_proc["alerta_if"].astype(int)
    pred_union = (df_proc["alerta_reglas"] | df_proc["alerta_if"]).astype(int)
    pred_inter = (df_proc["alerta_reglas"] & df_proc["alerta_if"]).astype(int)

    # 1. Métricas globales de detectores
    metricas = [
        evaluar_clasificador(y_true, pred_reglas, "Reglas simples"),
        evaluar_clasificador(y_true, pred_if, "Isolation Forest"),
        evaluar_clasificador(y_true, pred_union, "Unión (Cualquiera)"),
        evaluar_clasificador(y_true, pred_inter, "Intersección (Ambas)"),
    ]
    df_metricas = pd.DataFrame(metricas)

    # 2. Recall por tipo de anomalía
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

    # 3. Falsos positivos sobre casos extremos legítimos
    extremos = df_proc[df_proc["nota_simulacion"] == "extremo_legitimo"]
    n_extremos = len(extremos)
    detectores_ext = {
        "Reglas simples": extremos["alerta_reglas"],
        "Isolation Forest": extremos["alerta_if"],
        "Unión (Cualquiera)": extremos["alerta_reglas"] | extremos["alerta_if"],
        "Intersección (Ambas)": extremos["alerta_reglas"] & extremos["alerta_if"],
    }
    df_fp_extremos = pd.DataFrame([
        {
            "detector": nombre,
            "total_extremos": n_extremos,
            "falsos_positivos": int(serie.sum()),
            "tasa_fp_extremos": float(serie.mean()) if n_extremos > 0 else 0.0,
        }
        for nombre, serie in detectores_ext.items()
    ])

    # 4. Sensibilidad a la contaminación de Isolation Forest
    filas_sens = []
    for c in NIVELES_CONTAMINACION_SENSIBILIDAD:
        df_sens, _, _ = aplicar_isolation_forest(df_proc, contamination=c, seed=SEED)
        res_c = evaluar_clasificador(y_true, df_sens["alerta_if"].astype(int), f"IF_cont_{c:.2f}")
        res_c["contamination"] = c
        filas_sens.append(res_c)
    df_sensibilidad = pd.DataFrame(filas_sens)

    # 5. Errores de la Unión (falsos positivos y falsos negativos)
    cols_err = [
        "mesa_id", "municipio", "zona", "votantes_habilitados", "participacion",
        "pct_max_candidato", "score_if", "tipo_anomalia", "nota_simulacion",
    ]
    falsos_positivos = df_proc[(y_true == 0) & (pred_union == 1)][cols_err]
    falsos_negativos = df_proc[(y_true == 1) & (pred_union == 0)][cols_err]

    return {
        "metricas": df_metricas,
        "recall_tipo": df_recall_tipo,
        "fp_extremos": df_fp_extremos,
        "sensibilidad": df_sensibilidad,
        "falsos_positivos": falsos_positivos,
        "falsos_negativos": falsos_negativos,
    }


def ejecutar_evaluacion(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """Ejecuta la evaluación completa, genera todas las tablas y exporta resultados."""
    OUTPUTS_TAB_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    df_proc = combinar_detectores(df)
    df_proc.to_csv(DATA_PROCESSED_CSV, index=False)

    ev = calcular_evaluacion(df_proc)
    top_15 = calcular_top_mesas(df_proc, n=15)
    riesgo_muni = calcular_riesgo_por_municipio(df_proc)

    ev["metricas"].to_csv(OUTPUTS_TAB_DIR / "metricas_detectores.csv", index=False)
    ev["recall_tipo"].to_csv(OUTPUTS_TAB_DIR / "recall_por_tipo.csv", index=False)
    ev["fp_extremos"].to_csv(OUTPUTS_TAB_DIR / "falsos_positivos_extremos.csv", index=False)
    ev["sensibilidad"].to_csv(OUTPUTS_TAB_DIR / "sensibilidad_contaminacion.csv", index=False)
    top_15.to_csv(OUTPUTS_TAB_DIR / "top_mesas_sospechosas.csv", index=False)
    riesgo_muni.to_csv(OUTPUTS_TAB_DIR / "riesgo_por_municipio.csv", index=False)

    print("=================================================================")
    print("EVALUACIÓN DE DETECTORES (GROUND TRUTH)")
    print("=================================================================")
    print(ev["metricas"][["detector", "mesas_alertadas", "VP", "FP", "precision", "recall", "f1"]].to_string(index=False))
    print("\nRecall por tipo de anomalía:")
    print(ev["recall_tipo"][["tipo_anomalia", "recall_reglas", "recall_if", "recall_union"]].to_string(index=False))
    print("\nFalsos positivos en casos extremos legítimos (40 mesas):")
    print(ev["fp_extremos"][["detector", "falsos_positivos", "tasa_fp_extremos"]].to_string(index=False))
    print("\nTop 5 municipios con mayor tasa de actas con riesgo alto:")
    print(riesgo_muni.head(5)[["municipio", "departamento", "total_mesas", "mesas_riesgo_alto", "pct_riesgo_alto"]].to_string(index=False))
    print("\nAnálisis de errores — 3 Falsos Positivos representativos (Unión):")
    print(ev["falsos_positivos"].head(3).to_string(index=False))
    print("\nAnálisis de errores — 3 Falsos Negativos representativos (Unión):")
    print(ev["falsos_negativos"].head(3).to_string(index=False))
    print("=================================================================")

    return df_proc, {
        "metricas": ev["metricas"],
        "recall_tipo": ev["recall_tipo"],
        "fp_extremos": ev["fp_extremos"],
        "sensibilidad": ev["sensibilidad"],
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
