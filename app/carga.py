"""Lectura y validación del archivo de actas (Excel o CSV) cargado en la interfaz."""

from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import List, Union

import pandas as pd

COLUMNAS_CONTEOS: List[str] = [
    "votos_cand_A", "votos_cand_B", "votos_cand_C", "votos_cand_D",
    "votos_blanco", "votos_nulos", "votos_no_marcados",
]
COLUMNAS_NUMERICAS: List[str] = ["votantes_habilitados", *COLUMNAS_CONTEOS, "total_votos_reportado"]
COLUMNAS_TEXTO: List[str] = ["mesa_id", "departamento", "municipio", "zona"]
COLUMNAS_OBLIGATORIAS: List[str] = [*COLUMNAS_TEXTO, *COLUMNAS_NUMERICAS]
COLUMNAS_OPCIONALES: List[str] = ["puesto", "hora_reporte"]
COLUMNAS_ETIQUETA: List[str] = ["es_anomalia", "tipo_anomalia", "nota_simulacion"]

MAX_FILAS: int = 50_000  # Límite razonable para una demo local


@dataclass
class ResultadoValidacion:
    ok: bool
    chequeos: List[tuple] = field(default_factory=list)  # (descripción, aprobado: bool)
    errores: List[str] = field(default_factory=list)
    avisos: List[str] = field(default_factory=list)
    tiene_etiquetas: bool = False


def leer_archivo(origen: Union[str, Path, BytesIO], nombre: str = "") -> pd.DataFrame:
    """Lee un .xlsx (hoja 'mesas' si existe, si no la primera) o un .csv."""
    nombre = (nombre or str(origen)).lower()
    if nombre.endswith(".csv"):
        return pd.read_csv(origen)
    hojas = pd.ExcelFile(origen)
    hoja = "mesas" if "mesas" in hojas.sheet_names else hojas.sheet_names[0]
    return hojas.parse(hoja)


def validar_y_preparar(df: pd.DataFrame) -> tuple[pd.DataFrame, ResultadoValidacion]:
    """Valida el esquema y deja el DataFrame listo para el análisis.

    Retorna el DataFrame limpio (copia) y el resultado de la validación. Si `ok` es False,
    el análisis no debe ejecutarse.
    """
    res = ResultadoValidacion(ok=True)
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    def chequeo(descripcion: str, aprobado: bool, error: str = "") -> None:
        res.chequeos.append((descripcion, aprobado))
        if not aprobado:
            res.ok = False
            if error:
                res.errores.append(error)

    # 1. Tamaño
    chequeo(
        f"El archivo tiene entre 1 y {MAX_FILAS:,} filas".replace(",", "."),
        0 < len(df) <= MAX_FILAS,
        f"El archivo tiene {len(df)} filas; debe tener entre 1 y {MAX_FILAS}.",
    )

    # 2. Columnas obligatorias
    faltantes = [c for c in COLUMNAS_OBLIGATORIAS if c not in df.columns]
    chequeo(
        "Están todas las columnas obligatorias",
        not faltantes,
        f"Faltan columnas obligatorias: {', '.join(faltantes)}.",
    )
    if faltantes:
        return df, res

    # 3. Tipos numéricos
    no_numericas = []
    for c in COLUMNAS_NUMERICAS:
        convertida = pd.to_numeric(df[c], errors="coerce")
        if convertida.isna().any():
            no_numericas.append(c)
        df[c] = convertida
    chequeo(
        "Los conteos de votos son numéricos y no están vacíos",
        not no_numericas,
        f"Hay valores vacíos o no numéricos en: {', '.join(no_numericas)}.",
    )
    if no_numericas:
        return df, res
    df[COLUMNAS_NUMERICAS] = df[COLUMNAS_NUMERICAS].round().astype(int)

    # 4. Valores no negativos y habilitados > 0
    negativos = [c for c in COLUMNAS_NUMERICAS if (df[c] < 0).any()]
    chequeo(
        "No hay conteos negativos",
        not negativos,
        f"Hay valores negativos en: {', '.join(negativos)}.",
    )
    chequeo(
        "Toda mesa tiene al menos un ciudadano habilitado",
        bool((df["votantes_habilitados"] > 0).all()),
        "Hay mesas con 0 ciudadanos habilitados (la participación no se puede calcular).",
    )

    # 5. Texto sin vacíos e identificadores únicos
    vacios = [c for c in COLUMNAS_TEXTO if df[c].isna().any()]
    chequeo(
        "Identificación de la mesa completa (id, departamento, municipio, zona)",
        not vacios,
        f"Hay celdas vacías en: {', '.join(vacios)}.",
    )
    for c in COLUMNAS_TEXTO:
        df[c] = df[c].astype(str).str.strip()
    duplicados = int(df["mesa_id"].duplicated().sum())
    chequeo(
        "Cada mesa_id es único",
        duplicados == 0,
        f"Hay {duplicados} mesa_id repetidos.",
    )

    # 6. Columnas opcionales
    if "hora_reporte" not in df.columns:
        df["hora_reporte"] = pd.NaT
        res.avisos.append("No hay columna 'hora_reporte'; el tiempo de reporte no se mostrará.")
    if "puesto" not in df.columns:
        df["puesto"] = ""

    # 7. Etiquetas (ground truth): solo para evaluar
    res.tiene_etiquetas = all(c in df.columns for c in ["es_anomalia", "tipo_anomalia"])
    if res.tiene_etiquetas:
        df["es_anomalia"] = pd.to_numeric(df["es_anomalia"], errors="coerce").fillna(0).astype(int)
        df["tipo_anomalia"] = df["tipo_anomalia"].fillna("ninguna").astype(str)
        if "nota_simulacion" not in df.columns:
            df["nota_simulacion"] = ""
        df["nota_simulacion"] = df["nota_simulacion"].fillna("").astype(str)
        res.avisos.append(
            "El archivo trae etiquetas (es_anomalia): se usarán SOLO para la pestaña Evaluación, "
            "nunca como entrada de los detectores."
        )
    else:
        df = df.drop(columns=[c for c in COLUMNAS_ETIQUETA if c in df.columns])

    return df, res
