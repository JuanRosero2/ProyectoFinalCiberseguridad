"""Genera los dos archivos Excel de demostración para la interfaz web.

- data/demo/mesas_demo_con_etiquetas.xlsx: incluye el ground truth (habilita la evaluación).
- data/demo/mesas_demo_sin_etiquetas.xlsx: sin ground truth (escenario realista).

Ambos contienen las hojas 'mesas', 'diccionario' y 'leeme'. Los datos son 100 % simulados.
"""

from pathlib import Path

import pandas as pd

from src.config import DATA_DIR, SEED
from src.generate_dataset import generar_dataset

DEMO_DIR: Path = DATA_DIR / "demo"
DEMO_CON_ETIQUETAS: Path = DEMO_DIR / "mesas_demo_con_etiquetas.xlsx"
DEMO_SIN_ETIQUETAS: Path = DEMO_DIR / "mesas_demo_sin_etiquetas.xlsx"

COLUMNAS_ETIQUETA = ["es_anomalia", "tipo_anomalia", "nota_simulacion"]

DESCARGO_ETICO = (
    "Todos los votos de este archivo son simulados. Los departamentos y municipios son reales de Colombia, pero "
    "los resultados, las mesas y los candidatos son ficticios: no representan ninguna elección real ni hacen "
    "afirmaciones sobre ella. Una alerta indica una inconsistencia que merece revisión, no una prueba de fraude."
)

DICCIONARIO = [
    ("mesa_id", "texto", "Identificador único de la mesa", "M00001"),
    ("departamento", "texto", "Departamento (real; los votos son simulados)", "Antioquia"),
    ("municipio", "texto", "Municipio (real; los votos son simulados)", "Medellín"),
    ("zona", "texto", "urbana / rural (corregimientos e inspecciones)", "urbana"),
    ("puesto", "texto", "Puesto de votación (agrupa ~20 mesas)", "Medellín · Puesto 01"),
    ("votantes_habilitados", "entero", "Ciudadanos habilitados para votar en la mesa (según el censo electoral)", "250"),
    ("votos_cand_A", "entero", "Votos por el Candidato A", "60"),
    ("votos_cand_B", "entero", "Votos por el Candidato B", "45"),
    ("votos_cand_C", "entero", "Votos por el Candidato C", "25"),
    ("votos_cand_D", "entero", "Votos por el Candidato D", "15"),
    ("votos_blanco", "entero", "Votos en blanco", "3"),
    ("votos_nulos", "entero", "Votos nulos", "4"),
    ("votos_no_marcados", "entero", "Tarjetas electorales no marcadas", "1"),
    ("total_votos_reportado", "entero", "Total escrito en el formulario E-14 (debería ser la suma de los 7 conteos)", "153"),
    ("hora_reporte", "fecha-hora", "Hora de transmisión del E-14 para el preconteo", "2026-09-13T17:05:00"),
    ("es_anomalia", "0/1", "SOLO versión con etiquetas: 1 si la mesa fue manipulada en la simulación", "0"),
    ("tipo_anomalia", "texto", "SOLO versión con etiquetas: tipo de anomalía inyectada o 'ninguna'", "ninguna"),
    ("nota_simulacion", "texto", "SOLO versión con etiquetas: 'extremo_legitimo' si es atípica pero legítima", ""),
]


def _escribir_excel(df: pd.DataFrame, ruta: Path, con_etiquetas: bool) -> None:
    diccionario = pd.DataFrame(DICCIONARIO, columns=["columna", "tipo", "descripcion", "ejemplo"])
    if not con_etiquetas:
        diccionario = diccionario[~diccionario["columna"].isin(COLUMNAS_ETIQUETA)]

    version = (
        "CON etiquetas: incluye la respuesta correcta (qué mesas fueron manipuladas) para poder "
        "medir la precisión de los detectores."
        if con_etiquetas
        else "SIN etiquetas: como en un caso real, no se sabe qué mesas fueron manipuladas."
    )
    leeme = pd.DataFrame({
        "contenido": [
            "Panel de integridad electoral — datos de demostración",
            DESCARGO_ETICO,
            f"Versión: {version}",
            "Hoja 'mesas': una fila por mesa (resultados de su formulario E-14). Hoja 'diccionario': descripción de las columnas.",
            f"Generado con semilla {SEED} (reproducible con: python -m src.generate_demo_excel).",
        ]
    })

    with pd.ExcelWriter(ruta, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="mesas", index=False)
        diccionario.to_excel(writer, sheet_name="diccionario", index=False)
        leeme.to_excel(writer, sheet_name="leeme", index=False)


def generar_excels_demo(df: pd.DataFrame | None = None) -> tuple[Path, Path]:
    """Escribe los dos Excel demo y devuelve sus rutas."""
    if df is None:
        df = generar_dataset(seed=SEED)
    DEMO_DIR.mkdir(parents=True, exist_ok=True)

    df_con = df.copy()
    df_con["nota_simulacion"] = df_con["nota_simulacion"].fillna("")
    _escribir_excel(df_con, DEMO_CON_ETIQUETAS, con_etiquetas=True)
    _escribir_excel(df.drop(columns=COLUMNAS_ETIQUETA), DEMO_SIN_ETIQUETAS, con_etiquetas=False)
    return DEMO_CON_ETIQUETAS, DEMO_SIN_ETIQUETAS


if __name__ == "__main__":
    rutas = generar_excels_demo()
    for r in rutas:
        print(f"Excel demo generado: {r}")
