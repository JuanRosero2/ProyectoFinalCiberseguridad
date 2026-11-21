"""Orquesta el análisis para la interfaz reutilizando las funciones de `src/`.

No contiene fórmulas, umbrales ni modelos propios: todo viene de `src/`. Las etiquetas
(ground truth) se separan ANTES de llamar a los detectores y solo se vuelven a unir para evaluar.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional

import pandas as pd

from src.config import FEATURES_IF, SEED
from src.eda import calcular_eda
from src.evaluate import (
    calcular_evaluacion,
    calcular_riesgo_por_municipio,
    combinar_detectores,
    ordenar_por_prioridad,
)
from src.features import agregar_features
from src.isolation_forest import aplicar_isolation_forest
from src.rules import aplicar_reglas

from app.carga import COLUMNAS_ETIQUETA

COLUMNAS_REGLAS = [
    "R1_sobre_participacion",
    "R2_inconsistencia_aritmetica",
    "R3_participacion_extrema",
    "R4_voto_concentrado",
    "R5_nulos_excesivos",
    "R6_numeros_redondos",
]


@dataclass
class ResultadosAnalisis:
    df: pd.DataFrame                       # Datos + features + reglas + IF + nivel de riesgo (+ etiquetas si hay)
    eda: Dict[str, object]
    umbral_if: float                       # Score mínimo marcado como anómalo por IF
    perfil_if: pd.DataFrame                # Media estandarizada de cada feature: alertadas vs no alertadas
    contamination: float
    tiene_etiquetas: bool
    evaluacion: Optional[Dict[str, pd.DataFrame]] = None
    extras: Dict[str, object] = field(default_factory=dict)


def _perfil_features_if(df: pd.DataFrame) -> pd.DataFrame:
    """Compara la media estandarizada (z) de cada feature entre mesas alertadas y no alertadas por IF."""
    X = df[FEATURES_IF]
    z = (X - X.mean()) / X.std(ddof=0).replace(0, 1)
    alertadas = z[df["alerta_if"]].mean()
    normales = z[~df["alerta_if"]].mean()
    perfil = pd.DataFrame({
        "feature": FEATURES_IF,
        "media_z_alertadas": alertadas.values,
        "media_z_no_alertadas": normales.values,
    })
    perfil["diferencia"] = perfil["media_z_alertadas"] - perfil["media_z_no_alertadas"]
    perfil["abs_diferencia"] = perfil["diferencia"].abs()
    return perfil.sort_values("abs_diferencia", ascending=False).reset_index(drop=True)


def analizar(df_validado: pd.DataFrame, contamination: float, tiene_etiquetas: bool) -> ResultadosAnalisis:
    """Ejecuta features → reglas → Isolation Forest → nivel de riesgo → EDA → (evaluación)."""
    # 1. Separar etiquetas: los detectores nunca las ven
    etiquetas = None
    if tiene_etiquetas:
        etiquetas = df_validado[["mesa_id", *[c for c in COLUMNAS_ETIQUETA if c in df_validado.columns]]].copy()
    df_sin_etiquetas = df_validado.drop(columns=[c for c in COLUMNAS_ETIQUETA if c in df_validado.columns])

    # 2. Pipeline de detección (idéntico a src/main.py)
    df_feat = agregar_features(df_sin_etiquetas)
    df_reglas = aplicar_reglas(df_feat)
    df_if, _, _ = aplicar_isolation_forest(df_reglas, contamination=contamination, seed=SEED)
    df_res = combinar_detectores(df_if)

    # 3. Variables de apoyo para la interfaz (no afectan la detección)
    df_res["mediana_participacion_municipio"] = df_res.groupby("municipio")["participacion"].transform("median")
    df_res["percentil_score_if"] = df_res["score_if"].rank(pct=True) * 100
    df_res["reglas_activadas"] = df_res[COLUMNAS_REGLAS].apply(
        lambda fila: ", ".join(c.split("_")[0] for c in COLUMNAS_REGLAS if fila[c]), axis=1
    )
    df_res["deteccion"] = "Sin alerta"
    df_res.loc[df_res["alerta_reglas"] & ~df_res["alerta_if"], "deteccion"] = "Solo reglas"
    df_res.loc[~df_res["alerta_reglas"] & df_res["alerta_if"], "deteccion"] = "Solo Isolation Forest"
    df_res.loc[df_res["alerta_reglas"] & df_res["alerta_if"], "deteccion"] = "Ambas técnicas"

    umbral_if = float(df_res.loc[df_res["alerta_if"], "score_if"].min()) if df_res["alerta_if"].any() else float("nan")
    perfil = _perfil_features_if(df_res)
    eda = calcular_eda(df_res)

    # 4. Evaluación (solo si hay etiquetas): se unen de nuevo por mesa_id
    evaluacion = None
    if etiquetas is not None:
        df_res = df_res.merge(etiquetas, on="mesa_id", how="left")
        evaluacion = calcular_evaluacion(df_res)

    df_res = ordenar_por_prioridad(df_res).reset_index(drop=True)
    df_res.insert(0, "prioridad", range(1, len(df_res) + 1))

    return ResultadosAnalisis(
        df=df_res,
        eda=eda,
        umbral_if=umbral_if,
        perfil_if=perfil,
        contamination=contamination,
        tiene_etiquetas=etiquetas is not None,
        evaluacion=evaluacion,
    )


def riesgo_municipal(res: ResultadosAnalisis, min_mesas: int) -> pd.DataFrame:
    """Riesgo por municipio con mínimo de mesas (evita porcentajes inflados en municipios pequeños)."""
    return calcular_riesgo_por_municipio(res.df, min_mesas=min_mesas)
