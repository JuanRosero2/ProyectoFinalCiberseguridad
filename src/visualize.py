"""Fase 6: Generación de las 5 visualizaciones analíticas oficiales del proyecto.

Cumple con la paleta de colores corporativa y requisitos estéticos:
  - Normal (gris #9E9E9E)
  - Solo Reglas (naranja #F28E2B)
  - Solo Isolation Forest (azul #4E79A7)
  - Ambas técnicas (rojo #E15759)
DPI = 200, exportadas en outputs/figures/.
"""

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.config import (
    COLOR_AMBAS,
    COLOR_NORMAL,
    COLOR_SOLO_IF,
    COLOR_SOLO_REGLAS,
    DATA_PROCESSED_CSV,
    DPI_FIGURAS,
    FIGSIZE_DEFAULT,
    OUTPUTS_FIG_DIR,
    OUTPUTS_TAB_DIR,
    UMBRAL_R3_PARTICIPACION,
)


def _configurar_estilo() -> None:
    """Configura parámetros generales de matplotlib/seaborn para tipografía y grillas limpias."""
    sns.set_theme(style="whitegrid", font="sans-serif")
    plt.rcParams["font.size"] = 11
    plt.rcParams["axes.titlesize"] = 13
    plt.rcParams["axes.titleweight"] = "bold"
    plt.rcParams["axes.labelsize"] = 11
    plt.rcParams["xtick.labelsize"] = 10
    plt.rcParams["ytick.labelsize"] = 10
    plt.rcParams["legend.fontsize"] = 10
    plt.rcParams["figure.titlesize"] = 14


def generar_figura_1(df: pd.DataFrame) -> Path:
    """Figura 1: Distribución de la participación electoral con líneas de umbral."""
    _configurar_estilo()
    fig, ax = plt.subplots(figsize=FIGSIZE_DEFAULT)

    # Histograma con bins=60
    sns.histplot(
        data=df,
        x="participacion",
        bins=60,
        color="#5A7D9A",
        edgecolor="white",
        alpha=0.85,
        ax=ax,
    )

    # Líneas verticales de umbrales
    ax.axvline(
        x=UMBRAL_R3_PARTICIPACION,
        color=COLOR_SOLO_REGLAS,
        linestyle="--",
        linewidth=2,
        label=f"Umbral R3: Participación extrema ({UMBRAL_R3_PARTICIPACION * 100:.0f} %)",
    )
    ax.axvline(
        x=1.00,
        color=COLOR_AMBAS,
        linestyle="-",
        linewidth=2.5,
        label="Umbral R1: Imposibilidad física (100 %)",
    )

    ax.set_title("Figura 1: Distribución de la Participación Electoral en las Actas", pad=12)
    ax.set_xlabel("Tasa de Participación (Total Votos / Votantes Habilitados)")
    ax.set_ylabel("Frecuencia (Cantidad de Mesas)")
    ax.legend(loc="upper right", frameon=True)
    ax.set_xlim(0.15, 1.35)

    ruta = OUTPUTS_FIG_DIR / "fig1_distribucion_participacion.png"
    plt.tight_layout()
    plt.savefig(ruta, dpi=DPI_FIGURAS)
    plt.close(fig)

    print(f"[Figura 1 guardada] {ruta.name}")
    print("  Interpretación: La mayoría de mesas está entre 40–75 %; hay una cola anómala a la derecha que supera el 95 % y el 100 % del padrón electoral.")
    return ruta


def generar_figura_2(df: pd.DataFrame) -> Path:
    """Figura 2: Huella electoral 2D (Participación vs Concentración de Voto)."""
    _configurar_estilo()
    fig, ax = plt.subplots(figsize=FIGSIZE_DEFAULT)

    # Clasificar categorías de detección
    cond_ambas = df["alerta_reglas"] & df["alerta_if"]
    cond_solo_reglas = df["alerta_reglas"] & (~df["alerta_if"])
    cond_solo_if = (~df["alerta_reglas"]) & df["alerta_if"]
    cond_normal = (~df["alerta_reglas"]) & (~df["alerta_if"])

    # Graficar por capas para asegurar visibilidad
    ax.scatter(
        df.loc[cond_normal, "participacion"],
        df.loc[cond_normal, "pct_max_candidato"] * 100,
        c=COLOR_NORMAL,
        alpha=0.35,
        s=16,
        label="Normal (sin alerta)",
    )
    ax.scatter(
        df.loc[cond_solo_if, "participacion"],
        df.loc[cond_solo_if, "pct_max_candidato"] * 100,
        c=COLOR_SOLO_IF,
        alpha=0.75,
        s=32,
        label="Solo Isolation Forest",
    )
    ax.scatter(
        df.loc[cond_solo_reglas, "participacion"],
        df.loc[cond_solo_reglas, "pct_max_candidato"] * 100,
        c=COLOR_SOLO_REGLAS,
        alpha=0.75,
        s=36,
        label="Solo Reglas simples",
    )
    ax.scatter(
        df.loc[cond_ambas, "participacion"],
        df.loc[cond_ambas, "pct_max_candidato"] * 100,
        c=COLOR_AMBAS,
        alpha=0.90,
        s=48,
        edgecolors="black",
        linewidths=0.5,
        label="Ambas técnicas (concordancia)",
    )

    ax.set_title("Figura 2: Huella Electoral 2D (Participación vs. Voto Máximo por Candidato)", pad=12)
    ax.set_xlabel("Tasa de Participación Electoral")
    ax.set_ylabel("Porcentaje del Candidato con Mayor Votación (%)")
    ax.legend(loc="lower left", frameon=True)
    ax.set_xlim(0.15, 1.35)
    ax.set_ylim(20, 105)

    ruta = OUTPUTS_FIG_DIR / "fig2_huella_electoral.png"
    plt.tight_layout()
    plt.savefig(ruta, dpi=DPI_FIGURAS)
    plt.close(fig)

    print(f"[Figura 2 guardada] {ruta.name}")
    print("  Interpretación: Huella electoral: las mesas sanas forman una nube central; las mesas anómalas e intervenidas se desplazan hacia el cuadrante superior derecho.")
    return ruta


def generar_figura_3(df: pd.DataFrame) -> Path:
    """Figura 3: Distribución del score de anomalía de Isolation Forest (Normales vs Anómalas)."""
    _configurar_estilo()
    fig, ax = plt.subplots(figsize=FIGSIZE_DEFAULT)

    # Umbral empírico de IF correspondiente al top 4%
    umbral_if = float(df["score_if"].quantile(0.96))

    sns.kdeplot(
        data=df[df["es_anomalia"] == 0],
        x="score_if",
        color=COLOR_NORMAL,
        fill=True,
        alpha=0.45,
        linewidth=2,
        label="Mesas normales (Ground truth = 0)",
        ax=ax,
    )
    sns.kdeplot(
        data=df[df["es_anomalia"] == 1],
        x="score_if",
        color=COLOR_AMBAS,
        fill=True,
        alpha=0.45,
        linewidth=2,
        label="Mesas anómalas (Ground truth = 1)",
        ax=ax,
    )

    ax.axvline(
        x=umbral_if,
        color=COLOR_SOLO_IF,
        linestyle="--",
        linewidth=2,
        label=f"Umbral de corte IF (Percentil 96 = {umbral_if:.3f})",
    )

    ax.set_title("Figura 3: Distribución de Scores de Isolation Forest por Clase Real", pad=12)
    ax.set_xlabel("Score de Anomalía (-score_samples; mayor = más anómalo)")
    ax.set_ylabel("Densidad de Probabilidad Estimada (KDE)")
    ax.legend(loc="upper right", frameon=True)

    ruta = OUTPUTS_FIG_DIR / "fig3_score_isolation_forest.png"
    plt.tight_layout()
    plt.savefig(ruta, dpi=DPI_FIGURAS)
    plt.close(fig)

    print(f"[Figura 3 guardada] {ruta.name}")
    print("  Interpretación: Isolation Forest separa claramente la distribución de mesas anómalas hacia scores altos, aunque existe solapamiento en la zona intermedia (origen de falsos positivos y negativos).")
    return ruta


def generar_figura_4(df: pd.DataFrame) -> Path:
    """Figura 4: Comparación de Recall por tipo de anomalía (Reglas vs Isolation Forest)."""
    _configurar_estilo()
    fig, ax = plt.subplots(figsize=FIGSIZE_DEFAULT)

    tabla_recall_path = OUTPUTS_TAB_DIR / "recall_por_tipo.csv"
    if tabla_recall_path.exists():
        df_rec = pd.read_csv(tabla_recall_path)
    else:
        from src.evaluate import ejecutar_evaluacion
        _, res = ejecutar_evaluacion(df)
        df_rec = res["recall_tipo"]

    nombres_formateados = {
        "sobre_participacion": "Sobre-participación\n(> 100 %)",
        "relleno_urnas": "Relleno de urnas\n(focalizado)",
        "voto_unanime": "Voto unánime\n(>= 92 %)",
        "inconsistencia_aritmetica": "Inconsistencia\naritmética",
        "numeros_redondos": "Números\nredondos",
        "nulos_excesivos": "Votos nulos\nexcesivos",
    }
    df_rec["etiqueta"] = df_rec["tipo_anomalia"].map(nombres_formateados)

    x = np.arange(len(df_rec))
    ancho = 0.35

    ax.bar(
        x - ancho / 2,
        df_rec["recall_reglas"] * 100,
        width=ancho,
        color=COLOR_SOLO_REGLAS,
        label="Reglas simples",
        edgecolor="black",
        linewidth=0.5,
    )
    ax.bar(
        x + ancho / 2,
        df_rec["recall_if"] * 100,
        width=ancho,
        color=COLOR_SOLO_IF,
        label="Isolation Forest",
        edgecolor="black",
        linewidth=0.5,
    )

    # Anotar valores sobre las barras
    for i in range(len(df_rec)):
        v_reg = df_rec["recall_reglas"].iloc[i] * 100
        v_if = df_rec["recall_if"].iloc[i] * 100
        ax.text(x[i] - ancho / 2, v_reg + 1.5, f"{v_reg:.0f}%", ha="center", fontsize=9)
        ax.text(x[i] + ancho / 2, v_if + 1.5, f"{v_if:.0f}%", ha="center", fontsize=9)

    ax.set_title("Figura 4: Recall por Tipo de Anomalía Inyectada (Reglas vs. Isolation Forest)", pad=12)
    ax.set_xlabel("Tipo de Anomalía de Integridad Electoral")
    ax.set_ylabel("Recall / Sensibilidad (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(df_rec["etiqueta"])
    ax.set_ylim(0, 115)
    ax.legend(loc="upper right", frameon=True)

    ruta = OUTPUTS_FIG_DIR / "fig4_recall_por_tipo.png"
    plt.tight_layout()
    plt.savefig(ruta, dpi=DPI_FIGURAS)
    plt.close(fig)

    print(f"[Figura 4 guardada] {ruta.name}")
    print("  Interpretación: Las técnicas son complementarias: las reglas atrapan con perfección violaciones deterministas; Isolation Forest detecta anomalías multivariadas complejas como el relleno de urnas.")
    return ruta


def generar_figura_5(df: pd.DataFrame) -> Path:
    """Figura 5: Concentración geográfica de mesas con riesgo alto (Top 15 municipios)."""
    _configurar_estilo()
    fig, ax = plt.subplots(figsize=FIGSIZE_DEFAULT)

    tabla_riesgo_path = OUTPUTS_TAB_DIR / "riesgo_por_municipio.csv"
    if tabla_riesgo_path.exists():
        df_riesgo = pd.read_csv(tabla_riesgo_path)
    else:
        from src.evaluate import ejecutar_evaluacion
        _, res = ejecutar_evaluacion(df)
        df_riesgo = res["riesgo_muni"]

    top_15 = df_riesgo.head(15).iloc[::-1]  # Invertir para gráfico horizontal

    barras = ax.barh(
        top_15["municipio"],
        top_15["pct_riesgo_alto"],
        color=COLOR_AMBAS,
        edgecolor="black",
        linewidth=0.5,
        alpha=0.85,
    )

    # Anotar valores en las barras
    for barra in barras:
        ancho = barra.get_width()
        ax.text(
            ancho + 0.3,
            barra.get_y() + barra.get_height() / 2,
            f"{ancho:.1f} %",
            va="center",
            fontsize=9,
        )

    ax.set_title("Figura 5: Top 15 Municipios por Concentración de Mesas en Riesgo Alto", pad=12)
    ax.set_xlabel("Porcentaje de Mesas con Nivel de Riesgo Alto (%)")
    ax.set_ylabel("Municipio")
    ax.set_xlim(0, max(top_15["pct_riesgo_alto"]) + 3)

    ruta = OUTPUTS_FIG_DIR / "fig5_riesgo_por_municipio.png"
    plt.tight_layout()
    plt.savefig(ruta, dpi=DPI_FIGURAS)
    plt.close(fig)

    print(f"[Figura 5 guardada] {ruta.name}")
    print("  Interpretación: Las alertas de riesgo alto se concentran marcadamente en municipios clave, permitiendo a los equipos de auditoría focalizar recursos en los focos geográficos de anomalías.")
    return ruta


def generar_todas_las_figuras(df_input: Optional[pd.DataFrame] = None) -> None:
    """Genera y exporta exactamente las 5 figuras requeridas."""
    OUTPUTS_FIG_DIR.mkdir(parents=True, exist_ok=True)

    if df_input is None:
        if not DATA_PROCESSED_CSV.exists():
            from src.evaluate import ejecutar_evaluacion
            from src.features import agregar_features
            from src.generate_dataset import generar_dataset
            from src.isolation_forest import aplicar_isolation_forest
            from src.rules import aplicar_reglas

            df_raw = generar_dataset()
            df_f = agregar_features(df_raw)
            df_r = aplicar_reglas(df_f)
            df_if, _, _ = aplicar_isolation_forest(df_r)
            df_input, _ = ejecutar_evaluacion(df_if)
        else:
            df_input = pd.read_csv(DATA_PROCESSED_CSV)

    print("=================================================================")
    print("GENERACIÓN DE LAS 5 VISUALIZACIONES OFICIALES")
    print("=================================================================")
    generar_figura_1(df_input)
    generar_figura_2(df_input)
    generar_figura_3(df_input)
    generar_figura_4(df_input)
    generar_figura_5(df_input)
    print("=================================================================")


if __name__ == "__main__":
    generar_todas_las_figuras()

