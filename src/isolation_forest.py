"""Técnica 2: Detección no supervisada de anomalías mediante Isolation Forest.

Aisla observaciones multivariadas atípicas sin recurrir a etiquetas (ground truth),
evaluando la longitud media de particiones aleatorias en el espacio de características.
"""

from typing import Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from src.config import (
    FEATURES_IF,
    IF_CONTAMINATION,
    IF_MAX_SAMPLES,
    IF_N_ESTIMATORS,
    SEED,
)
from src.features import agregar_features


def aplicar_isolation_forest(
    df: pd.DataFrame,
    contamination: float = IF_CONTAMINATION,
    seed: int = SEED,
) -> Tuple[pd.DataFrame, IsolationForest, StandardScaler]:
    """Entrena Isolation Forest sobre las features estandarizadas y genera scores y alertas.

    Parámetros:
        df: DataFrame con las actas electorales (con o sin variables derivadas ya agregadas).
        contamination: Proporción supuesta de actas anómalas a auditar.
        seed: Semilla para reproducibilidad.

    Retorna:
        Tuple[DataFrame con columnas 'score_if', 'alerta_if', 'ranking_if',
              modelo IsolationForest entrenado, scaler StandardScaler].
    """
    if not all(col in df.columns for col in FEATURES_IF):
        df_eval = agregar_features(df)
    else:
        df_eval = df.copy()

    X = df_eval[FEATURES_IF].copy()

    # Estandarización de características
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Entrenamiento del modelo Isolation Forest
    modelo = IsolationForest(
        n_estimators=IF_N_ESTIMATORS,
        contamination=contamination,
        max_samples=IF_MAX_SAMPLES,
        random_state=seed,
    )
    modelo.fit(X_scaled)

    # Invertir el score: por defecto score_samples da valores negativos más bajos para outliers;
    # al tomar el negativo (-score_samples), valores mayores corresponden a actas más anómalas.
    scores = -modelo.score_samples(X_scaled)
    predicciones = modelo.predict(X_scaled)  # -1 es anómalo, 1 es normal

    df_eval["score_if"] = scores
    df_eval["alerta_if"] = predicciones == -1

    # Ranking: 1 es la mesa más anómala (mayor score)
    df_eval["ranking_if"] = (
        df_eval["score_if"].rank(ascending=False, method="min").astype(int)
    )

    return df_eval, modelo, scaler

