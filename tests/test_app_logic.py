"""Pruebas de la lógica de la interfaz web (carga, validación y análisis) sin levantar Streamlit."""

from io import BytesIO
from pathlib import Path

import pandas as pd
import pytest

from app.analisis import analizar
from app.carga import COLUMNAS_ETIQUETA, leer_archivo, validar_y_preparar
from app.exportar import construir_excel
from src.config import IF_CONTAMINATION, OUTPUTS_TAB_DIR, SEED
from src.generate_dataset import generar_dataset


@pytest.fixture(scope="module")
def df_demo() -> pd.DataFrame:
    return generar_dataset(seed=SEED)


@pytest.fixture(scope="module")
def resultado_con_etiquetas(df_demo):
    df, val = validar_y_preparar(df_demo)
    assert val.ok
    return analizar(df, IF_CONTAMINATION, val.tiene_etiquetas)


def test_validacion_archivo_correcto(df_demo):
    _, val = validar_y_preparar(df_demo)
    assert val.ok and val.tiene_etiquetas and not val.errores


def test_validacion_columna_faltante(df_demo):
    _, val = validar_y_preparar(df_demo.drop(columns=["votos_nulos"]))
    assert not val.ok
    assert any("votos_nulos" in e for e in val.errores)


def test_validacion_conteo_negativo(df_demo):
    df = df_demo.copy()
    df.loc[0, "votos_cand_A"] = -5
    _, val = validar_y_preparar(df)
    assert not val.ok


def test_validacion_mesa_id_duplicado(df_demo):
    df = df_demo.copy()
    df.loc[1, "mesa_id"] = df.loc[0, "mesa_id"]
    _, val = validar_y_preparar(df)
    assert not val.ok


def test_lectura_csv_y_excel(df_demo, tmp_path: Path):
    muestra = df_demo.head(50)
    ruta_csv = tmp_path / "mesas.csv"
    ruta_xlsx = tmp_path / "mesas.xlsx"
    muestra.to_csv(ruta_csv, index=False)
    muestra.to_excel(ruta_xlsx, sheet_name="mesas", index=False)
    assert len(leer_archivo(ruta_csv)) == 50
    assert len(leer_archivo(ruta_xlsx)) == 50


def test_metricas_coinciden_con_pipeline(resultado_con_etiquetas):
    """La interfaz debe producir exactamente las mismas métricas que el pipeline de src/."""
    esperado = pd.read_csv(OUTPUTS_TAB_DIR / "metricas_detectores.csv")
    obtenido = resultado_con_etiquetas.evaluacion["metricas"]
    pd.testing.assert_frame_equal(
        obtenido[["detector", "VP", "FP", "FN", "VN"]].reset_index(drop=True),
        esperado[["detector", "VP", "FP", "FN", "VN"]],
    )


def test_sin_etiquetas_funciona_y_no_evalua(df_demo, resultado_con_etiquetas):
    df, val = validar_y_preparar(df_demo.drop(columns=COLUMNAS_ETIQUETA))
    assert val.ok and not val.tiene_etiquetas
    res = analizar(df, IF_CONTAMINATION, val.tiene_etiquetas)
    assert res.evaluacion is None
    # Las etiquetas no influyen en la detección: mismas alertas con y sin ellas
    con = resultado_con_etiquetas.df.set_index("mesa_id").sort_index()
    sin = res.df.set_index("mesa_id").sort_index()
    pd.testing.assert_series_equal(con["nivel_riesgo"], sin["nivel_riesgo"])


def test_exportar_excel(resultado_con_etiquetas):
    from app.analisis import riesgo_municipal

    contenido = construir_excel(resultado_con_etiquetas, riesgo_municipal(resultado_con_etiquetas, 0))
    hojas = pd.ExcelFile(BytesIO(contenido)).sheet_names
    assert {"resultados_mesas", "mesas_priorizadas", "riesgo_municipio", "metricas", "parametros"} <= set(hojas)
