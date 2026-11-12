"""Análisis Exploratorio de Datos (EDA) del proceso electoral simulado.

Calcula variables derivadas, genera estadísticas descriptivas, resume resultados
nacionales y departamentales, e imprime observaciones clave que fundamentan
los umbrales de detección.
"""

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from src.config import (
    DATA_FEATURES_CSV,
    DATA_PROCESSED_DIR,
    DATA_RAW_CSV,
    OUTPUTS_TAB_DIR,
)
from src.features import agregar_features


def ejecutar_eda(df_input: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Ejecuta el análisis exploratorio y exporta las tablas requeridas."""
    if df_input is None:
        if not DATA_RAW_CSV.exists():
            from src.generate_dataset import generar_dataset
            df_input = generar_dataset()
            DATA_RAW_CSV.parent.mkdir(parents=True, exist_ok=True)
            df_input.to_csv(DATA_RAW_CSV, index=False)
        else:
            df_input = pd.read_csv(DATA_RAW_CSV)

    df_feat = agregar_features(df_input)

    OUTPUTS_TAB_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Estadísticas descriptivas de features numéricas clave
    features_numericas = [
        "votantes_habilitados",
        "total_votos_reportado",
        "suma_componentes",
        "diferencia_aritmetica",
        "participacion",
        "votos_validos",
        "pct_cand_A",
        "pct_cand_B",
        "pct_cand_C",
        "pct_cand_D",
        "pct_max_candidato",
        "pct_nulos",
        "pct_blanco",
        "frac_multiplos_10",
        "desv_participacion_municipal",
        "minutos_reporte",
    ]
    resumen_eda = df_feat[features_numericas].describe().T
    resumen_eda_path = OUTPUTS_TAB_DIR / "resumen_eda.csv"
    resumen_eda.to_csv(resumen_eda_path)

    # 2. Resultados nacionales agregados
    tot_A = int(df_feat["votos_cand_A"].sum())
    tot_B = int(df_feat["votos_cand_B"].sum())
    tot_C = int(df_feat["votos_cand_C"].sum())
    tot_D = int(df_feat["votos_cand_D"].sum())
    tot_bl = int(df_feat["votos_blanco"].sum())
    tot_nu = int(df_feat["votos_nulos"].sum())
    tot_nm = int(df_feat["votos_no_marcados"].sum())
    tot_rep = int(df_feat["total_votos_reportado"].sum())
    tot_val = tot_A + tot_B + tot_C + tot_D

    resultados_nacionales = pd.DataFrame([
        {"opcion": "Candidato A", "votos": tot_A, "pct_validos": (tot_A / tot_val) * 100, "pct_total": (tot_A / tot_rep) * 100},
        {"opcion": "Candidato B", "votos": tot_B, "pct_validos": (tot_B / tot_val) * 100, "pct_total": (tot_B / tot_rep) * 100},
        {"opcion": "Candidato C", "votos": tot_C, "pct_validos": (tot_C / tot_val) * 100, "pct_total": (tot_C / tot_rep) * 100},
        {"opcion": "Candidato D", "votos": tot_D, "pct_validos": (tot_D / tot_val) * 100, "pct_total": (tot_D / tot_rep) * 100},
        {"opcion": "Voto en Blanco", "votos": tot_bl, "pct_validos": np.nan, "pct_total": (tot_bl / tot_rep) * 100},
        {"opcion": "Votos Nulos", "votos": tot_nu, "pct_validos": np.nan, "pct_total": (tot_nu / tot_rep) * 100},
        {"opcion": "No Marcados", "votos": tot_nm, "pct_validos": np.nan, "pct_total": (tot_nm / tot_rep) * 100},
        {"opcion": "Total Reportado", "votos": tot_rep, "pct_validos": np.nan, "pct_total": 100.0},
    ])
    res_nac_path = OUTPUTS_TAB_DIR / "resultados_nacionales.csv"
    resultados_nacionales.to_csv(res_nac_path, index=False)

    # 3. Participación media y desviación por departamento y zona
    part_depto_zona = df_feat.groupby(["departamento", "zona"])["participacion"].agg(
        mesas="count",
        media="mean",
        desv="std",
        mediana="median",
        min="min",
        max="max"
    ).reset_index()
    part_depto_path = OUTPUTS_TAB_DIR / "participacion_por_departamento.csv"
    part_depto_zona.to_csv(part_depto_path, index=False)

    # 4. Guardar dataset procesado con features
    df_feat.to_csv(DATA_FEATURES_CSV, index=False)

    # 5. Imprimir hallazgos clave
    n_sobre_100 = int((df_feat["participacion"] > 1.0).sum())
    n_dif_arit = int((df_feat["diferencia_aritmetica"] > 0).sum())
    n_part_95 = int((df_feat["participacion"] >= 0.95).sum())
    n_conc_90 = int((df_feat["pct_max_candidato"] >= 0.90).sum())
    n_nulos_12 = int((df_feat["pct_nulos"] >= 0.12).sum())
    n_redondos_100 = int((df_feat["frac_multiplos_10"] == 1.0).sum())

    print("=================================================================")
    print("RESUMEN DEL ANÁLISIS EXPLORATORIO (EDA)")
    print("=================================================================")
    print(f"Total de actas analizadas: {len(df_feat)}")
    print(f"- Mesas con participación > 100 % (físicamente imposibles): {n_sobre_100}")
    print(f"- Mesas con diferencia aritmética entre reporte y suma: {n_dif_arit}")
    print(f"- Mesas con participación extrema (>= 95 %): {n_part_95}")
    print(f"- Mesas con concentración extrema de voto (pct_max >= 90 %): {n_conc_90}")
    print(f"- Mesas con tasa excesiva de votos nulos (pct_nulos >= 12 %): {n_nulos_12}")
    print(f"- Mesas con el 100 % de conteos de candidatos redondos: {n_redondos_100}")
    print(f"- Participación electoral nacional promedio: {df_feat['participacion'].mean() * 100:.2f} %")
    print(f"Tablas exportadas en: {OUTPUTS_TAB_DIR}")
    print(f"Features exportadas en: {DATA_FEATURES_CSV}")
    print("=================================================================")

    return df_feat


if __name__ == "__main__":
    ejecutar_eda()

