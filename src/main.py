"""Orquestador principal del pipeline de detección de anomalías electorales simuladas.

Ejecuta el flujo completo de punta a punta:
  1. Generación de dataset sintético (mesas normales, extremos legítimos y anomalías)
  2. Ingeniería de características y análisis exploratorio (EDA)
  3. Técnica 1: Detección basada en reglas simples y severidad
  4. Técnica 2: Detección no supervisada con Isolation Forest
  5. Combinación de técnicas y determinación de nivel de riesgo
  6. Evaluación cuantitativa completa contra Ground Truth
  7. Generación de las 5 visualizaciones analíticas
"""

import sys
import time
from pathlib import Path

import pandas as pd

from src.config import (
    DATA_PROCESSED_CSV,
    DATA_RAW_CSV,
    OUTPUTS_FIG_DIR,
    OUTPUTS_TAB_DIR,
    SEED,
)
from src.eda import ejecutar_eda
from src.evaluate import ejecutar_evaluacion
from src.features import agregar_features
from src.generate_dataset import generar_dataset
from src.isolation_forest import aplicar_isolation_forest
from src.rules import aplicar_reglas
from src.visualize import generar_todas_las_figuras
from src.generate_pdf_report import compilar_informe_pdf


def run_pipeline() -> None:
    """Ejecuta de manera secuencial y reproducible todas las etapas del proyecto."""
    inicio = time.time()
    print("========================================================================")
    print("INICIANDO PIPELINE: DETECCIÓN DE ANOMALÍAS EN PROCESO ELECTORAL SIMULADO")
    print(f"Semilla de reproducibilidad (SEED): {SEED}")
    print("========================================================================")

    # Paso 1: Generación de dataset
    print("\n[Paso 1/7] Generando dataset sintético (5.000 mesas)...")
    df_raw = generar_dataset(seed=SEED)
    DATA_RAW_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_raw.to_csv(DATA_RAW_CSV, index=False)
    print(f" -> Dataset guardado en: {DATA_RAW_CSV}")

    # Paso 2: Features y EDA
    print("\n[Paso 2/7] Calculando variables derivadas y ejecutando EDA...")
    df_feat = ejecutar_eda(df_raw)

    # Paso 3: Técnica 1 (Reglas simples)
    print("\n[Paso 3/7] Aplicando Técnica 1 (Reglas simples con severidad)...")
    df_reglas = aplicar_reglas(df_feat)
    alertas_reglas_tot = int(df_reglas["alerta_reglas"].sum())
    print(f" -> Mesas alertadas por reglas simples: {alertas_reglas_tot}")

    # Paso 4: Técnica 2 (Isolation Forest)
    print("\n[Paso 4/7] Aplicando Técnica 2 (Isolation Forest no supervisado)...")
    df_if, _, _ = aplicar_isolation_forest(df_reglas, seed=SEED)
    alertas_if_tot = int(df_if["alerta_if"].sum())
    print(f" -> Mesas alertadas por Isolation Forest: {alertas_if_tot}")

    # Paso 5: Evaluación y combinación
    print("\n[Paso 5/7] Evaluando contra Ground Truth y calculando riesgo...")
    df_final, tablas = ejecutar_evaluacion(df_if)

    # Paso 6: Visualizaciones
    print("\n[Paso 6/7] Generando las 5 visualizaciones analíticas oficiales...")
    generar_todas_las_figuras(df_final)

    # Paso 7: Informe PDF
    print("\n[Paso 7/7] Compilando informe final en PDF (reports/Informe_Final.pdf)...")
    compilar_informe_pdf()

    duracion = time.time() - inicio
    print("\n========================================================================")
    print("PIPELINE COMPLETADO EXITOSAMENTE")
    print("========================================================================")
    print(f"Tiempo total de ejecución: {duracion:.2f} segundos")
    print(f"Actas procesadas: {len(df_final)}")
    print(f"Mesas en riesgo ALTO: {(df_final['nivel_riesgo'] == 'alto').sum()}")
    print(f"Mesas en riesgo MEDIO: {(df_final['nivel_riesgo'] == 'medio').sum()}")
    print(f"Mesas en riesgo BAJO: {(df_final['nivel_riesgo'] == 'bajo').sum()}")
    print(f"Resultados procesados: {DATA_PROCESSED_CSV}")
    print(f"Tablas analíticas generadas: {OUTPUTS_TAB_DIR}")
    print(f"Figuras generadas: {OUTPUTS_FIG_DIR}")
    print("========================================================================")


if __name__ == "__main__":
    run_pipeline()
