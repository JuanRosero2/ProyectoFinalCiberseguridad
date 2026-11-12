"""Pruebas unitarias para el generador del dataset electoral simulado."""

import numpy as np
import pandas as pd
import pytest

from src.config import CANTIDADES_ANOMALIAS, NUM_EXTREMOS_LEGITIMOS, NUM_MESAS, SEED
from src.generate_dataset import COLUMNAS_ESQUEMA, generar_dataset


@pytest.fixture(scope="module")
def df_dataset() -> pd.DataFrame:
    return generar_dataset(seed=SEED)


def test_tamano_y_columnas(df_dataset: pd.DataFrame) -> None:
    """Verifica que el dataset tenga exactamente 5.000 filas y las columnas en orden."""
    assert len(df_dataset) == NUM_MESAS
    assert list(df_dataset.columns) == COLUMNAS_ESQUEMA


def test_sin_conteos_negativos(df_dataset: pd.DataFrame) -> None:
    """Verifica que ningún conteo de votos o habilitados sea negativo."""
    columnas_conteo = [
        "votantes_habilitados",
        "votos_cand_A",
        "votos_cand_B",
        "votos_cand_C",
        "votos_cand_D",
        "votos_blanco",
        "votos_nulos",
        "votos_no_marcados",
        "total_votos_reportado",
    ]
    for col in columnas_conteo:
        assert (df_dataset[col] >= 0).all(), f"Se encontraron valores negativos en {col}"


def test_distribucion_anomalias_y_extremos(df_dataset: pd.DataFrame) -> None:
    """Verifica los conteos exactos de cada tipo de anomalía y de extremos legítimos."""
    vc = df_dataset["tipo_anomalia"].value_counts().to_dict()

    for tipo, cant_esp in CANTIDADES_ANOMALIAS.items():
        assert vc.get(tipo, 0) == cant_esp, f"Esperado {cant_esp} para {tipo}, obtenido {vc.get(tipo, 0)}"

    assert vc.get("ninguna", 0) == NUM_MESAS - sum(CANTIDADES_ANOMALIAS.values())

    # Ground truth coherente: es_anomalia == 1 si y solo si tipo_anomalia != "ninguna"
    anomalas = df_dataset[df_dataset["es_anomalia"] == 1]
    assert len(anomalas) == 200
    assert (anomalas["tipo_anomalia"] != "ninguna").all()

    # Extremos legítimos: exactamente 40 con es_anomalia == 0
    extremos = df_dataset[df_dataset["nota_simulacion"] == "extremo_legitimo"]
    assert len(extremos) == NUM_EXTREMOS_LEGITIMOS
    assert (extremos["es_anomalia"] == 0).all()
    assert (extremos["tipo_anomalia"] == "ninguna").all()


def test_integridad_mesas_normales(df_dataset: pd.DataFrame) -> None:
    """En mesas con tipo_anomalia == 'ninguna', el total debe ser la suma exacta y <= habilitados."""
    normales = df_dataset[df_dataset["tipo_anomalia"] == "ninguna"]
    suma_componentes = (
        normales["votos_cand_A"]
        + normales["votos_cand_B"]
        + normales["votos_cand_C"]
        + normales["votos_cand_D"]
        + normales["votos_blanco"]
        + normales["votos_nulos"]
        + normales["votos_no_marcados"]
    )
    assert (normales["total_votos_reportado"] == suma_componentes).all()
    assert (normales["total_votos_reportado"] <= normales["votantes_habilitados"]).all()


def test_reproducibilidad() -> None:
    """Dos ejecuciones con la misma semilla deben producir DataFrames idénticos."""
    df1 = generar_dataset(seed=SEED)
    df2 = generar_dataset(seed=SEED)
    pd.testing.assert_frame_equal(df1, df2)

