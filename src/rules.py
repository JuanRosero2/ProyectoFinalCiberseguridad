"""Técnica 1: Detección basada en reglas deterministas y umbrales justificados.

Evalúa reglas de integridad física, aritmética y límites estadísticos sobre
las variables derivadas de las actas de votación, asignando puntajes de severidad.
"""

from typing import List
import numpy as np
import pandas as pd

from src.config import (
    PESO_R1_SOBRE_PARTICIPACION,
    PESO_R2_INCONSISTENCIA_ARITMETICA,
    PESO_R3_PARTICIPACION_EXTREMA,
    PESO_R4_VOTO_CONCENTRADO,
    PESO_R5_NULOS_EXCESIVOS,
    PESO_R6_NUMEROS_REDONDOS,
    PUNTAJE_ALTA,
    PUNTAJE_CRITICA,
    PUNTAJE_MEDIA,
    UMBRAL_R3_PARTICIPACION,
    UMBRAL_R4_MIN_VOTOS_VALIDOS,
    UMBRAL_R4_PCT_MAX,
    UMBRAL_R5_PCT_NULOS,
    UMBRAL_R6_FRAC_MULTIPLOS_10,
)
from src.features import agregar_features

REGLAS_COLUMNAS: List[str] = [
    "R1_sobre_participacion",
    "R2_inconsistencia_aritmetica",
    "R3_participacion_extrema",
    "R4_voto_concentrado",
    "R5_nulos_excesivos",
    "R6_numeros_redondos",
]


def aplicar_reglas(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica las 6 reglas simples sobre el DataFrame.

    Si no contiene las features derivadas necesarias, las calcula automáticamente.
    Retorna una copia del DataFrame con las columnas booleanas de cada regla,
    'puntaje_reglas', 'alerta_reglas' y 'severidad_reglas'.
    """
    columnas_necesarias = [
        "diferencia_aritmetica",
        "participacion",
        "pct_max_candidato",
        "votos_validos",
        "pct_nulos",
        "frac_multiplos_10",
    ]
    if not all(col in df.columns for col in columnas_necesarias):
        df_eval = agregar_features(df)
    else:
        df_eval = df.copy()

    # R1: Participación física imposible (> 100 % del censo)
    df_eval["R1_sobre_participacion"] = (
        df_eval["total_votos_reportado"] > df_eval["votantes_habilitados"]
    )

    # R2: Inconsistencia aritmética (total reportado != suma de los componentes)
    df_eval["R2_inconsistencia_aritmetica"] = df_eval["diferencia_aritmetica"] > 0

    # R3: Participación extrema (>= 95 % del censo)
    df_eval["R3_participacion_extrema"] = (
        df_eval["participacion"] >= UMBRAL_R3_PARTICIPACION
    )

    # R4: Voto unánime o ultra-concentrado (>= 90 % a un candidato con min 50 votos válidos)
    df_eval["R4_voto_concentrado"] = (
        (df_eval["pct_max_candidato"] >= UMBRAL_R4_PCT_MAX)
        & (df_eval["votos_validos"] >= UMBRAL_R4_MIN_VOTOS_VALIDOS)
    )

    # R5: Tasa de votos nulos excesiva (>= 12 %)
    df_eval["R5_nulos_excesivos"] = df_eval["pct_nulos"] >= UMBRAL_R5_PCT_NULOS

    # R6: Números redondos (los 4 candidatos reciben votos múltiplos de 10)
    df_eval["R6_numeros_redondos"] = (
        df_eval["frac_multiplos_10"] >= UMBRAL_R6_FRAC_MULTIPLOS_10
    )

    # Cálculo ponderado del puntaje
    df_eval["puntaje_reglas"] = (
        df_eval["R1_sobre_participacion"].astype(int) * PESO_R1_SOBRE_PARTICIPACION
        + df_eval["R2_inconsistencia_aritmetica"].astype(int) * PESO_R2_INCONSISTENCIA_ARITMETICA
        + df_eval["R3_participacion_extrema"].astype(int) * PESO_R3_PARTICIPACION_EXTREMA
        + df_eval["R4_voto_concentrado"].astype(int) * PESO_R4_VOTO_CONCENTRADO
        + df_eval["R5_nulos_excesivos"].astype(int) * PESO_R5_NULOS_EXCESIVOS
        + df_eval["R6_numeros_redondos"].astype(int) * PESO_R6_NUMEROS_REDONDOS
    )

    df_eval["alerta_reglas"] = df_eval["puntaje_reglas"] > 0

    # Categorización de severidad
    condiciones = [
        df_eval["puntaje_reglas"] >= PUNTAJE_CRITICA,
        df_eval["puntaje_reglas"] == PUNTAJE_ALTA,
        df_eval["puntaje_reglas"] == PUNTAJE_MEDIA,
    ]
    etiquetas = ["critica", "alta", "media"]
    df_eval["severidad_reglas"] = np.select(condiciones, etiquetas, default="sin alerta")

    return df_eval

