"""Ingeniería de variables derivadas (features) para el análisis exploratorio y detección.

IMPORTANTE: No utiliza ni referencia ninguna columna de ground truth
(es_anomalia, tipo_anomalia, nota_simulacion) para evitar data leakage.
"""

from typing import List
import numpy as np
import pandas as pd

from src.config import FECHA_HORA_CIERRE

COLUMNAS_CONTEO_CANDIDATOS: List[str] = [
    "votos_cand_A",
    "votos_cand_B",
    "votos_cand_C",
    "votos_cand_D",
]

COLUMNAS_7_CONTEOS: List[str] = COLUMNAS_CONTEO_CANDIDATOS + [
    "votos_blanco",
    "votos_nulos",
    "votos_no_marcados",
]


def agregar_features(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula y agrega variables derivadas al DataFrame sin tocar las columnas de ground truth.

    Retorna una copia del DataFrame con todas las columnas originales más las features.
    """
    df_feat = df.copy()

    # 1. Suma de componentes y diferencia aritmética
    df_feat["suma_componentes"] = df_feat[COLUMNAS_7_CONTEOS].sum(axis=1)
    df_feat["diferencia_aritmetica"] = (
        df_feat["total_votos_reportado"] - df_feat["suma_componentes"]
    ).abs()

    # 2. Participación (turnout)
    df_feat["participacion"] = df_feat["total_votos_reportado"] / df_feat["votantes_habilitados"]

    # 3. Votos válidos y porcentajes por candidato
    df_feat["votos_validos"] = df_feat[COLUMNAS_CONTEO_CANDIDATOS].sum(axis=1)
    denominador_validos = np.where(df_feat["votos_validos"] > 0, df_feat["votos_validos"], 1.0)

    df_feat["pct_cand_A"] = np.where(
        df_feat["votos_validos"] > 0,
        df_feat["votos_cand_A"] / denominador_validos,
        0.0
    )
    df_feat["pct_cand_B"] = np.where(
        df_feat["votos_validos"] > 0,
        df_feat["votos_cand_B"] / denominador_validos,
        0.0
    )
    df_feat["pct_cand_C"] = np.where(
        df_feat["votos_validos"] > 0,
        df_feat["votos_cand_C"] / denominador_validos,
        0.0
    )
    df_feat["pct_cand_D"] = np.where(
        df_feat["votos_validos"] > 0,
        df_feat["votos_cand_D"] / denominador_validos,
        0.0
    )

    df_feat["pct_max_candidato"] = df_feat[
        ["pct_cand_A", "pct_cand_B", "pct_cand_C", "pct_cand_D"]
    ].max(axis=1)

    # 4. Porcentajes de nulos y blancos respecto a la suma de componentes
    denominador_componentes = np.where(
        df_feat["suma_componentes"] > 0, df_feat["suma_componentes"], 1.0
    )
    df_feat["pct_nulos"] = df_feat["votos_nulos"] / denominador_componentes
    df_feat["pct_blanco"] = df_feat["votos_blanco"] / denominador_componentes

    # 5. Fracción de candidatos con votos múltiplos de 10 y > 0
    mult_10_matrix = np.column_stack([
        ((df_feat[col] > 0) & (df_feat[col] % 10 == 0)).astype(float)
        for col in COLUMNAS_CONTEO_CANDIDATOS
    ])
    df_feat["frac_multiplos_10"] = mult_10_matrix.mean(axis=1)

    # 6. Desviación respecto a la mediana municipal de participación
    mediana_municipal = df_feat.groupby("municipio")["participacion"].transform("median")
    df_feat["desv_participacion_municipal"] = df_feat["participacion"] - mediana_municipal

    # 7. Logaritmo natural de habilitados
    df_feat["log_habilitados"] = np.log(df_feat["votantes_habilitados"])

    # 8. Minutos transcurridos desde el cierre electoral (16:00)
    cierre_dt = pd.to_datetime(FECHA_HORA_CIERRE)
    reporte_dt = pd.to_datetime(df_feat["hora_reporte"])
    df_feat["minutos_reporte"] = (reporte_dt - cierre_dt).dt.total_seconds() / 60.0

    return df_feat

